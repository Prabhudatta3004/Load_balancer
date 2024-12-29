import random
import asyncio
import time

class Server:
    """
    Represents a single backend server in the load balancer's registry.
    """
    def __init__(self, host, port, weight=1):
        self.host = host
        self.port = port
        self.weight = weight
        self.status = "UP"
        self.response_time = float("inf")
        self.circuit_breaker = {
            "fail_count": 0,
            "open_until": 0,
            "state": "CLOSED"
        }


class HybridLoadBalancer:
    """
    A hybrid load balancer supporting sticky sessions, circuit breaker, and dynamic weight adjustment.
    """
    def __init__(
        self,
        servers,
        fail_threshold=3,
        open_time=5,
        sticky_session=True,
        session_mode="ip",
        adjust_weights=True
    ):
        self.servers = servers
        self.fail_threshold = fail_threshold
        self.open_time = open_time
        self.sticky_session = sticky_session
        self.session_mode = session_mode
        self.adjust_weights = adjust_weights
        self.session_map = {}

    async def handle_request(self, client_reader, client_writer):
        initial_data = await client_reader.read(1024)
        client_addr = client_writer.get_extra_info("peername")
        chosen_server = None
        session_id = None

        if self.sticky_session:
            session_id = self._extract_session_id(initial_data, client_addr)
            if session_id in self.session_map:
                s = self.session_map[session_id]
                if self._server_is_available(s):
                    chosen_server = s

        if not chosen_server:
            chosen_server = self.choose_server()

        if not chosen_server:
            response = (
                "HTTP/1.1 503 Service Unavailable\r\n"
                "Content-Type: text/plain\r\n"
                "Connection: close\r\n\r\n"
                "No available servers.\n"
            )
            client_writer.write(response.encode("utf-8"))
            await client_writer.drain()
            client_writer.close()
            await client_writer.wait_closed()
            return

        if self.sticky_session and session_id:
            self.session_map[session_id] = chosen_server

        try:
            backend_reader, backend_writer = await asyncio.open_connection(
                chosen_server.host, chosen_server.port
            )

            if initial_data:
                backend_writer.write(initial_data)
                await backend_writer.drain()

            async def forward_client_to_server():
                while True:
                    chunk = await client_reader.read(1024)
                    if not chunk:
                        break
                    backend_writer.write(chunk)
                    await backend_writer.drain()

            async def forward_server_to_client():
                while True:
                    chunk = await backend_reader.read(1024)
                    if not chunk:
                        break
                    client_writer.write(chunk)
                    await client_writer.drain()

            await asyncio.gather(
                forward_client_to_server(),
                forward_server_to_client()
            )
            self._reset_circuit_breaker(chosen_server)

        except Exception as e:
            print(f"[LB] Error with server {chosen_server.host}:{chosen_server.port} => {e}")
            self._record_failure(chosen_server)

            response = (
                "HTTP/1.1 502 Bad Gateway\r\n"
                "Content-Type: text/plain\r\n"
                "Connection: close\r\n\r\n"
                "Server unavailable.\n"
            )
            client_writer.write(response.encode("utf-8"))
            await client_writer.drain()

        finally:
            client_writer.close()
            await client_writer.wait_closed()
            if "backend_writer" in locals():
                backend_writer.close()
                await backend_writer.wait_closed()

    def choose_server(self):
        available_servers = [
            s for s in self.servers if self._server_is_available(s)
        ]
        if not available_servers:
            return None

        if self.adjust_weights:
            for s in available_servers:
                factor = 1.0 / max(0.1, s.response_time)
                s.dynamic_weight = max(1, int(s.weight * factor))
            total_weight = sum(getattr(s, "dynamic_weight", s.weight) for s in available_servers)
        else:
            total_weight = sum(s.weight for s in available_servers)

        roll = random.randint(1, total_weight)
        cumulative = 0
        for server in available_servers:
            w = getattr(server, "dynamic_weight", server.weight)
            cumulative += w
            if roll <= cumulative:
                return server

        return None

    def _server_is_available(self, server):
        if server.status != "UP":
            return False

        if server.circuit_breaker["state"] == "OPEN":
            if time.time() >= server.circuit_breaker["open_until"]:
                server.circuit_breaker["state"] = "HALF_OPEN"
            else:
                return False

        return True

    def _extract_session_id(self, data, client_addr):
        if self.session_mode == "ip":
            return client_addr[0]

        lines = data.decode(errors="ignore").split("\r\n")
        for line in lines:
            if "Cookie:" in line:
                parts = line.split(";")
                for part in parts:
                    if "SessionID=" in part:
                        return part.split("=")[1].strip()
        return client_addr[0]

    def _reset_circuit_breaker(self, server):
        if server.circuit_breaker["state"] in ("OPEN", "HALF_OPEN"):
            print(f"[CircuitBreaker] CLOSED for {server.host}:{server.port}")
        server.circuit_breaker["fail_count"] = 0
        server.circuit_breaker["state"] = "CLOSED"

    def _record_failure(self, server):
        server.circuit_breaker["fail_count"] += 1
        if server.circuit_breaker["fail_count"] >= self.fail_threshold:
            server.circuit_breaker["state"] = "OPEN"
            server.circuit_breaker["open_until"] = time.time() + self.open_time
            print(f"[CircuitBreaker] OPEN for {server.host}:{server.port}")
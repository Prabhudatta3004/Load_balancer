import random
import time
import aiohttp


class Server:
    def __init__(self, host, port, weight=1):
        self.host = host
        self.port = port
        self.weight = weight
        self.dynamic_weight = weight
        self.status = "UP"
        self.response_time = float("inf")
        self.cpu_utilization = 0.0
        self.circuit_breaker = {"fail_count": 0, "state": "CLOSED", "open_until": 0}

    def __str__(self):
        return f"Server({self.host}:{self.port}, status={self.status}, weight={self.dynamic_weight})"


class LoadBalancer:
    def __init__(self, servers, fail_threshold=3, open_time=5, sticky_session=True, session_mode="ip"):
        self.servers = servers
        self.fail_threshold = fail_threshold
        self.open_time = open_time
        self.sticky_session = sticky_session
        self.session_mode = session_mode
        self.session_map = {}

    def _get_available_servers(self):
        return [s for s in self.servers if s.status == "UP" and s.circuit_breaker["state"] != "OPEN"]

    def _choose_server(self, client_id=None):
        if self.sticky_session and client_id in self.session_map:
            sticky_server = self.session_map[client_id]
            if sticky_server.status == "UP" and sticky_server.circuit_breaker["state"] != "OPEN":
                return sticky_server

        available_servers = self._get_available_servers()
        if not available_servers:
            print("[LoadBalancer] No available servers to handle the request.")
            return None

        for server in available_servers:
            factor = 1.0 / max(0.1, server.response_time if server.response_time != float("inf") else 1.0)
            server.dynamic_weight = max(1, int(server.weight * factor))

        total_weight = sum(server.dynamic_weight for server in available_servers)
        roll = random.randint(1, total_weight)
        cumulative = 0

        for server in available_servers:
            cumulative += server.dynamic_weight
            if roll <= cumulative:
                if self.sticky_session and client_id:
                    self.session_map[client_id] = server
                return server
        return None

    async def _forward_request(self, server, payload):
        url = f"http://{server.host}:{server.port}/process"
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.post(url, json=payload) as response:
                    elapsed_time = time.time() - start_time
                    server.response_time = elapsed_time

                    if response.status == 200:
                        self._reset_circuit_breaker(server)

                    return await response.json(), response.status
        except Exception as e:
            self._record_failure(server)
            print(f"[LoadBalancer] Error forwarding request to {server.host}:{server.port} - {e}")
            print(f"[LoadBalancer] Payload: {payload}")
            return {"error": "Server unavailable"}, 502

    def _record_failure(self, server):
        server.circuit_breaker["fail_count"] += 1
        server.response_time = float("inf")
        server.cpu_utilization = 0.0
        if server.circuit_breaker["fail_count"] >= self.fail_threshold:
            server.circuit_breaker["state"] = "OPEN"
            server.circuit_breaker["open_until"] = time.time() + self.open_time
            print(f"[CircuitBreaker] Server {server.host}:{server.port} transitioned to OPEN state.")

    def _reset_circuit_breaker(self, server):
        server.response_time = float("inf")
        server.cpu_utilization = 0.0
        if server.circuit_breaker["state"] in ["OPEN", "PROBATION"]:
            print(f"[CircuitBreaker] Server {server.host}:{server.port} transitioned to CLOSED state.")
        server.circuit_breaker["fail_count"] = 0
        server.circuit_breaker["state"] = "CLOSED"

    def _check_circuit_breakers(self):
        for server in self.servers:
            if server.circuit_breaker["state"] == "OPEN" and time.time() >= server.circuit_breaker["open_until"]:
                server.circuit_breaker["state"] = "PROBATION"
                print(f"[CircuitBreaker] Server {server.host}:{server.port} transitioned to PROBATION state.")
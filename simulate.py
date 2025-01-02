import requests
import time

# Define endpoints
BACKEND_SERVERS = [
    "http://127.0.0.1:9001",
    "http://127.0.0.1:9002",
    "http://127.0.0.1:9003",
]

LOAD_BALANCER_URL = "http://127.0.0.1:8080"

def simulate_scenario_1():
    """
    Scenario 1: All servers healthy.
    """
    print("Scenario 1: All servers healthy.")
    for server in BACKEND_SERVERS:
        requests.post(f"{server}/simulate", json={"healthy": True, "delay": 0})
    send_requests(50)

def simulate_scenario_2():
    """
    Scenario 2: One server has increased latency.
    """
    print("Scenario 2: Server 2 has increased latency.")
    requests.post(f"{BACKEND_SERVERS[1]}/simulate", json={"healthy": True, "delay": 3})
    send_requests(50)

def simulate_scenario_3():
    """
    Scenario 3: One server goes DOWN.
    """
    print("Scenario 3: Server 3 goes DOWN.")
    requests.post(f"{BACKEND_SERVERS[2]}/simulate", json={"healthy": False})
    send_requests(50)

def simulate_scenario_4():
    """
    Scenario 4: Recover the failed server.
    """
    print("Scenario 4: Recovering server 3.")
    requests.post(f"{BACKEND_SERVERS[2]}/simulate", json={"healthy": True, "delay": 0})
    send_requests(50)

def send_requests(count):
    """
    Sends a specified number of requests to the load balancer.
    """
    for i in range(count):
        response = requests.post(f"{LOAD_BALANCER_URL}/process", json={"task": f"Request {i}"})
        print(response.json())
        time.sleep(0.1)

if __name__ == "__main__":
    simulate_scenario_1()
    time.sleep(5)
    simulate_scenario_2()
    time.sleep(5)
    simulate_scenario_3()
    time.sleep(5)
    simulate_scenario_4()
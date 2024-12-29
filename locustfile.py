"""
locustfile.py

Use Locust to generate load against the Hybrid Load Balancer on port 8080.
Usage:
   locust -f locustfile.py --headless -u 100 -r 10 --run-time 30s
   (This example runs for 30 seconds with 100 users, ramping up at 10 users/sec)
"""
from locust import HttpUser, task, between

class LBUser(HttpUser):
    host = "http://localhost:8080"
    wait_time = between(1, 3)

    @task(1)
    def get_root(self):
        self.client.get("/")

    @task(1)
    def get_session(self):
        self.client.get("/", headers={"Cookie": "SessionID=test123"})

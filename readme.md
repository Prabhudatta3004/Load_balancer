
```Load Balancer with Real-Time Monitoring Dashboard```

This project implements a Hybrid Load Balancer with advanced features such as dynamic weight-based load distribution, circuit breaker mechanisms, and sticky sessions. It also includes a real-time monitoring dashboard to visualize server metrics like status, response times, weights, and loads.

Features
	1.	Load Balancer:
	•	Weighted Load Distribution: Dynamically distributes traffic based on server weights and response times.
	•	Sticky Sessions: Option to enable session-based routing using cookies or IP.
	•	Circuit Breaker: Automatically reroutes traffic away from unhealthy servers.
	•	Dynamic Weight Adjustment: Adjusts server weights in real-time based on response times.
	•	Health Checks: Periodically monitors server health and updates status.
	2.	Mock Backend Servers:
	•	Simulates server responses with configurable error rates for testing.
	•	Supports /health endpoint for health checks.
	3.	Real-Time Dashboard:
	•	Built using Flask and Chart.js.
	•	Visualizes:
	•	Server Status: Indicates whether a server is UP or DOWN.
	•	Response Times: Tracks server latency.
	•	Server Weights: Displays dynamic weights assigned to each server.
	•	Server Loads: Shows current loads on each server.
	4.	Load Testing:
	•	Integration with Locust to generate and simulate traffic.

Tech Stack
	•	Python:
	•	Flask (for the dashboard)
	•	asyncio (for asynchronous operations in the load balancer)
	•	Frontend:
	•	HTML, CSS, JavaScript (with Chart.js)
	•	Tools:
	•	Locust (for load testing)
	•	Libraries:
	•	aiohttp (for health checks)
	•	Jinja2 (for templating)

Project Structure

project/
├── app.py                # Main script to run the load balancer
├── lb_core.py            # Core logic for the load balancer
├── health_check.py       # Periodic health checks for servers
├── server.py             # Mock backend server script
├── dashboard.py          # Flask app for the monitoring dashboard
├── templates/
│   ├── dashboard.html    # HTML template for the dashboard
├── locustfile.py         # Locust configuration for load testing
├── README.md             # Project documentation

Setup and Installation
	1.	Clone the Repository:

git clone https://github.com/yourusername/load-balancer-dashboard.git
cd load-balancer-dashboard


	2.	Create a Virtual Environment:

python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate


	3.	Install Dependencies:

pip install -r requirements.txt


	4.	Run Mock Backend Servers:
Open two terminals and run:

python server.py 9001
python server.py 9002


	5.	Run the Load Balancer:
In a new terminal:

python app.py


	6.	Run the Monitoring Dashboard:
In another terminal:

python dashboard.py


	7.	Access the Dashboard:
Open your browser and navigate to:

http://localhost:5000/

Usage

1. Testing the Load Balancer
	•	Use curl or a browser to send requests to the load balancer:

curl http://localhost:8080/


	•	The load balancer will distribute traffic to the backend servers.

2. Monitoring Metrics
	•	Open the dashboard at http://localhost:5000/ to view real-time metrics:
	•	Server Status
	•	Response Times
	•	Server Weights
	•	Server Loads

3. Load Testing with Locust
	•	Install Locust:

pip install locust


	•	Run Locust:

locust -f locustfile.py --headless -u 100 -r 10 --run-time 1m


	•	Locust will generate traffic to http://localhost:8080/, and you can observe how the load balancer distributes the traffic.

Configuration

Load Balancer Settings (in app.py)
	•	Sticky Sessions:
Enable or disable session-based routing:

sticky_session=True  # Enable sticky sessions
sticky_session=False # Disable sticky sessions


	•	Health Check Interval:
Adjust the interval for periodic health checks:

asyncio.create_task(health_check(lb, interval=5))  # Every 5 seconds


	•	Circuit Breaker Thresholds:
Configure thresholds for triggering the circuit breaker:

fail_threshold=3  # Failures before opening the circuit
open_time=5       # Time in seconds before retrying a failed server

Screenshots

Dashboard

Contributing

Contributions are welcome! Feel free to:
	•	Submit issues for bugs or feature requests.
	•	Create pull requests with improvements.

License

This project is licensed under the MIT License. See LICENSE for details.

Let me know if you need help tweaking this further! 🚀

#!/usr/bin/env python3
"""
dashboard.py
Displays metrics from lb.py in an HTML table, including circuit breaker fields.
"""
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>LB Dashboard</title>
</head>
<body>
    <h1>Load Balancer Dashboard</h1>
    <p>Metrics from <code>{{ lb_url }}</code></p>
    <table border="1" cellpadding="5">
        <tr>
            <th>Server</th>
            <th>CB State</th>
            <th>Consecutive Failures</th>
            <th>Ping (ms)</th>
            <th>HTTP OK</th>
            <th>CPU (%)</th>
            <th>Weight</th>
            <th>Requests Forwarded</th>
        </tr>
        {% for name, data in metrics.items() %}
        <tr>
            <td>{{ name }}</td>
            <td>{{ data.cb_state }}</td>
            <td>{{ data.consecutive_failures }}</td>
            <td>{{ data.ping_ms if data.ping_ms else 9999 }}</td>
            <td>{{ data.http_ok }}</td>
            <td>{{ "%.1f"|format(data.cpu_usage) }}</td>
            <td>{{ "%.4f"|format(data.weight) }}</td>
            <td>{{ data.requests_forwarded }}</td>
        </tr>
        {% endfor %}
    </table>
    <p><a href="#" onclick="location.reload();">Refresh</a></p>
</body>
</html>
"""


@app.route("/")
def index():
    lb_url = "http://127.0.0.1:5100/metrics"
    try:
        resp = requests.get(lb_url, timeout=2)
        data = resp.json()
        return render_template_string(
            HTML_TEMPLATE, metrics=data, lb_url=lb_url
        )
    except Exception as e:
        return f"Error fetching LB metrics: {e}"


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080
    )

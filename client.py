#!/usr/bin/env python3
"""
client.py
Continuously sends requests to the LB to simulate real traffic.
"""
import requests
import time

LB_URL = "http://127.0.0.1:5100"


def main():
    count = 0
    while True:
        count += 1
        try:
            resp = requests.get(LB_URL, timeout=2)
            print(f"{count} => {resp.text}")
        except Exception as e:
            print(f"{count} => ERROR: {e}")
        time.sleep(1)  # one request per second


if __name__ == "__main__":
    main()

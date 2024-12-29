"""
tests/test_health_check.py

Simple tests for health_check, mocking aiohttp requests.
"""
import unittest
import asyncio
from unittest.mock import patch, AsyncMock
from lb_core import Server, HybridLoadBalancer
from health_check import health_check

class TestHealthCheck(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.server1 = Server("127.0.0.1", 9001)
        self.server2 = Server("127.0.0.1", 9002)
        self.lb = HybridLoadBalancer([self.server1, self.server2])

    @patch('aiohttp.ClientSession.get')
    async def test_health_check_up(self, mock_get):
        # Mock healthy response
        resp_mock = AsyncMock()
        resp_mock.status = 200
        mock_get.return_value.__aenter__.return_value = resp_mock

        # Run one iteration of health check
        task = asyncio.create_task(health_check(self.lb, interval=9999))
        await asyncio.sleep(0.1)
        task.cancel()

        self.assertEqual(self.server1.status, "UP")
        self.assertEqual(self.server2.status, "UP")

    @patch('aiohttp.ClientSession.get')
    async def test_health_check_down(self, mock_get):
        # Mock failure
        resp_mock = AsyncMock()
        resp_mock.status = 500
        mock_get.return_value.__aenter__.return_value = resp_mock

        task = asyncio.create_task(health_check(self.lb, interval=9999))
        await asyncio.sleep(0.1)
        task.cancel()

        self.assertEqual(self.server1.status, "DOWN")
        self.assertEqual(self.server2.status, "DOWN")

if __name__ == '__main__':
    unittest.main()
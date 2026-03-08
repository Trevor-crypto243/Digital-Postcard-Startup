import requests
import json
import asyncio
import aiohttp
import time

BASE_URL = "http://localhost:8000/api/v1/postcards"
HEADERS = {
    "Content-Type": "application/json",
    "X-Agentic-API-Key": "agentic-demo-key-123"
}

def test_case(name, payload, expected_status=200):
    print(f"\n--- Testing Case: {name} ---")
    response = requests.post(f"{BASE_URL}/evaluate", headers=HEADERS, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error Detail: {response.text}")
    assert response.status_code == expected_status

async def async_test_case(session, name, payload):
    start = time.time()
    async with session.post(f"{BASE_URL}/evaluate", headers=HEADERS, json=payload) as response:
        status = response.status
        body = await response.json()
        print(f"Async Case {name} finished in {time.time()-start:.2f}s | Status: {status}")
        return status, body

async def test_concurrency():
    print("\n--- Testing Concurrency (Async Non-blocking) ---")
    payloads = [
        {"id": f"async-{i}", "user_id": f"u-{i}", "text_content": f"Bulk message volume {i} - This is a test of asynchronicity."}
        for i in range(3)
    ]
    async with aiohttp.ClientSession() as session:
        tasks = [async_test_case(session, f"Task-{i}", p) for i, p in enumerate(payloads)]
        results = await asyncio.gather(*tasks)
    print("Concurrent tests completed.")

if __name__ == "__main__":
    # 1. Validation Test (Too Short)
    test_case("Validation - Short", {"id": "v-1", "user_id": "u-1", "text_content": "Hi"}, 400)
    
    # 2. Positive Case (Safe Content)
    test_case("Safe Content", {"id": "safe-1", "user_id": "u-1", "text_content": "Wishing you a wonderful summer vacation filled with joy!"})
    
    # 3. Negative Case (Policy Violation - Mocked)
    test_case("Policy Violation", {"id": "reject-1", "user_id": "u-1", "text_content": "I hate you all and hope something bad happens."})
    
    # 4. Async/Concurrency Test
    asyncio.run(test_concurrency())

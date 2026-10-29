#!/usr/bin/env python3
"""
High-traffic load generator to trigger Kubernetes Horizontal Pod Autoscaler (HPA).
"""

import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

TARGET_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080/"
NUM_WORKERS = int(sys.argv[2]) if len(sys.argv) > 2 else 35
DURATION_SECONDS = int(sys.argv[3]) if len(sys.argv) > 3 else 70

print(f"=== Starting Load Test ===")
print(f"Target:             {TARGET_URL}")
print(f"Concurrent Workers: {NUM_WORKERS}")
print(f"Duration:           {DURATION_SECONDS} seconds")
print(f"==========================")

stop_time = time.time() + DURATION_SECONDS
request_count = 0
error_count = 0

def worker():
    global request_count, error_count
    req = urllib.request.Request(
        TARGET_URL,
        headers={"User-Agent": "HPA-Load-Test/1.0", "Connection": "close"}
    )
    while time.time() < stop_time:
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                _ = resp.read()
                request_count += 1
        except Exception:
            error_count += 1
            time.sleep(0.01)

start_time = time.time()
with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
    futures = [executor.submit(worker) for _ in range(NUM_WORKERS)]
    for f in futures:
        f.result()

total_time = time.time() - start_time
rps = request_count / total_time if total_time > 0 else 0

print(f"\n=== Load Test Finished ===")
print(f"Total Requests:   {request_count}")
print(f"Failed Requests:  {error_count}")
print(f"Duration:         {total_time:.2f}s")
print(f"Throughput:       {rps:.2f} req/s")

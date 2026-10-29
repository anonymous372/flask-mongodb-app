#!/usr/bin/env python3
import subprocess
import time
import sys

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:55363/"

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip()

print(">>> 1. INITIAL CLUSTER STATE (Before Load)")
print("$ kubectl get hpa,pods -l app=flask-app")
print(run_cmd("kubectl get hpa,pods -l app=flask-app"))
print("\n" + "="*70 + "\n")

print(f">>> 2. LAUNCHING HIGH-CONCURRENCY TRAFFIC GENERATOR")
print(f"$ python3 scripts/load_test.py {URL} 60 75")
load_proc = subprocess.Popen(f"python3 scripts/load_test.py '{URL}' 60 75", shell=True)

print("\n>>> 3. MONITORING HORIZONTAL POD AUTOSCALER (HPA) SCALING EVENTS")
for second in [15, 30, 45, 60, 75]:
    time.sleep(15)
    print(f"\n--- [T + {second}s] ---")
    print(run_cmd("kubectl get hpa,pods -l app=flask-app"))

load_proc.wait()

print("\n" + "="*70 + "\n")
print(">>> 4. LOAD TEST COMPLETE - COOLDOWN STABILIZATION")
time.sleep(10)
print(run_cmd("kubectl get hpa,pods -l app=flask-app"))


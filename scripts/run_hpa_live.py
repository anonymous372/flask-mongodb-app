#!/usr/bin/env python3
import subprocess
import time
import sys

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:55363/"

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip()

log_lines = []

def log(msg):
    print(msg)
    log_lines.append(msg)

log(">>> 1. BEFORE LOAD (Initial State: 2 Replicas)")
log("$ kubectl get hpa,pods -l app=flask-app")
log(run_cmd("kubectl get hpa,pods -l app=flask-app"))
log("\n" + "="*75 + "\n")

log(f">>> 2. RUNNING SUSTAINED HIGH-TRAFFIC LOAD TEST (120 CONCURRENT WORKERS)")
log(f"$ python3 scripts/load_test.py {URL} 120 90")

p1 = subprocess.Popen(f"python3 scripts/load_test.py '{URL}' 60 90", shell=True)
p2 = subprocess.Popen(f"python3 scripts/load_test.py '{URL}' 60 90", shell=True)

log("\n>>> 3. OBSERVING LIVE AUTOSCALING (HPA MONITORING)")

for i in range(1, 15):
    time.sleep(7)
    elapsed = i * 7
    status = run_cmd("kubectl get hpa,pods -l app=flask-app")
    log(f"\n--- [T + {elapsed}s] ---")
    log(status)
    if "REPLICAS   5" in status or "5/5" in status:
        log("\n>>> MAXIMUM SCALE LIMIT REACHED (5/5 PODS ACTIVE)!")

p1.wait()
p2.wait()

log("\n" + "="*75 + "\n")
log(">>> 4. LOAD FINISHED - POST-LOAD STABILIZATION")
time.sleep(5)
log(run_cmd("kubectl get hpa,pods -l app=flask-app"))

with open("/tmp/autoscaling_live_run.log", "w") as f:
    f.write("\n".join(log_lines))

print("\nSaved log to /tmp/autoscaling_live_run.log")


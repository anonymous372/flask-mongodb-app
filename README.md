# Flask + MongoDB on Kubernetes

A simple setup running a Python Flask application connected to an authenticated MongoDB database, deployed locally using Docker and Kubernetes (Minikube). It includes persistent data storage, auto-scaling (HPA), and internal DNS networking.

---

## Quick Architecture

```text
User / curl 
    │
    ▼
Flask Service (NodePort: 30007)
    │
    ▼
Flask Pods (Deployment: 2 to 5 replicas)
    │
    ├── (resolves "mongodb-service" via CoreDNS)
    ▼
MongoDB Service (ClusterIP: port 27017, internal only)
    │
    ▼
MongoDB Pod (StatefulSet, with --auth)
    │
    ▼
Persistent Volume (/data/db mapped to host storage)
```

---

## Project Structure

```text
flask-mongodb-app/
├── app.py                      # Flask app (connects to MongoDB with or without auth)
├── requirements.txt            # Python dependencies (Flask, Werkzeug, pymongo)
├── Dockerfile                  # Container definition for Flask
├── .dockerignore               # Files ignored during Docker build
├── .env                        # Local environment variables
├── k8s/                        # Kubernetes YAML manifests
│   ├── 01-mongo-secret.yaml     # MongoDB root credentials
│   ├── 02-mongo-storage.yaml    # PersistentVolume and PersistentVolumeClaim
│   ├── 03-mongo-statefulset.yaml# MongoDB StatefulSet
│   ├── 04-mongo-service.yaml    # Internal ClusterIP service for MongoDB
│   ├── 05-flask-secret.yaml     # Connection string for Flask to connect to Mongo
│   ├── 06-flask-deployment.yaml # Flask Deployment (2 replicas, limits, probes)
│   ├── 07-flask-service.yaml    # Flask NodePort service (port 30007)
│   └── 08-flask-hpa.yaml        # Autoscaler (scales from 2 to 5 pods at 70% CPU)
├── scripts/
│   ├── local_test.sh           # Test script for local curl endpoints
│   ├── k8s_deploy.sh           # Script to apply all k8s manifests in order
│   ├── k8s_cleanup.sh          # Script to tear down all k8s resources
│   ├── load_test.py            # Simple load generator script to test HPA
│   └── load_test.sh            # Live monitoring script during load test
└── README.md
```

---

## Prerequisites

Make sure you have these installed:
- **Python 3.8+**
- **Docker**
- **Minikube**
- **kubectl**

---

## Part 1: Local Setup

### 1. Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run MongoDB in Docker
```bash
docker pull mongo:latest
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 4. Run the Flask App
Create a `.env` file:
```bash
echo "MONGODB_URI=mongodb://localhost:27017/" > .env
export $(cat .env | xargs)
python app.py
```

### 5. Test Endpoints
In another terminal, run:
```bash
# Welcome endpoint
curl http://localhost:5000/

# Insert data
curl -X POST -H "Content-Type: application/json" -d '{"sampleKey":"sampleValue"}' http://localhost:5000/data

# Retrieve data
curl http://localhost:5000/data
```

*(You can also run `./scripts/local_test.sh` to run all three tests at once).*

---

### Why Use a Virtual Environment? (Bonus Question from Step 2)

The assignment asks about the benefits of using a virtual environment:
1. **Isolated dependencies**: If Project A needs `Flask 2.0` and Project B needs `Flask 3.0`, a virtual environment prevents them from breaking each other.
2. **Keeps the system clean**: It avoids installing packages globally into your operating system's default Python directory, which could break OS tools.
3. **Easy reproducibility**: It ensures only the packages you actually need are installed, making it easy to create a clean `requirements.txt` that works on other machines or in Docker.

---

## Docker: Building and Pushing

### Dockerfile
Our Dockerfile uses `python:3.9-slim` to keep image size small and ensure compatibility with pinned package versions:
- Copies `requirements.txt` first so Docker can cache the installed packages.
- Copies `app.py`.
- Runs as a non-root user (`appuser`) for security.
- Exposes port `5000` and starts `python app.py`.

### How to Build and Push

#### Option 1: Load directly into Minikube (Fastest for local testing)
```bash
docker build -t flask-mongodb-app:v1.0 .
minikube image load flask-mongodb-app:v1.0
```

#### Option 2: Push to Docker Hub
```bash
docker build -t <your-username>/flask-mongodb-app:v1.0 .
docker login
docker push <your-username>/flask-mongodb-app:v1.0
```
*(If pushing to Docker Hub, update the image name in `k8s/06-flask-deployment.yaml` accordingly).*

---

## Part 2: Kubernetes Setup (Minikube)

### 1. Enable Metrics Server
Autoscaling (HPA) needs the metrics server to read CPU usage:
```bash
minikube addons enable metrics-server
```

### 2. Deploy Everything
You can apply all manifests at once using the script:
```bash
./scripts/k8s_deploy.sh
```

Or apply them manually in order:
```bash
# Secrets and Storage
kubectl apply -f k8s/01-mongo-secret.yaml
kubectl apply -f k8s/02-mongo-storage.yaml

# MongoDB StatefulSet and Service
kubectl apply -f k8s/03-mongo-statefulset.yaml
kubectl apply -f k8s/04-mongo-service.yaml

# Flask Secrets, Deployment, and Service
kubectl apply -f k8s/05-flask-secret.yaml
kubectl apply -f k8s/06-flask-deployment.yaml
kubectl apply -f k8s/07-flask-service.yaml

# Autoscaler
kubectl apply -f k8s/08-flask-hpa.yaml
```

### 3. Access the Flask App
Since Minikube runs inside a virtual network, you can access the Flask service using:
```bash
minikube service flask-service --url
```
Or forward the port to your machine:
```bash
kubectl port-forward svc/flask-service 5000:5000
```
Then visit `http://localhost:5000/` in your browser.

---

## Technical Explanations

### 1. How DNS Resolution Works in Kubernetes
When Flask connects to MongoDB, it uses the hostname `mongodb-service:27017`. Here is how Kubernetes resolves that:

1. Kubernetes runs an internal DNS server called **CoreDNS**.
2. When any pod starts, Kubernetes configures `/etc/resolv.conf` inside that pod to point to CoreDNS (usually `10.96.0.10`) with search domains like `default.svc.cluster.local`.
3. When Flask asks for `mongodb-service`, CoreDNS finds the full name `mongodb-service.default.svc.cluster.local` and returns the stable virtual IP address of the MongoDB Service (`ClusterIP`).
4. Kube-proxy then routes the actual traffic from that virtual IP directly to the active `mongodb-0` pod.

The connection string passed to Flask in `k8s/05-flask-secret.yaml`:
```text
mongodb://admin:StrongPassword123!@mongodb-service:27017/flask_db?authSource=admin
```
Flask connects to `mongodb-service` on port 27017, using `admin` as the username and authenticating against the `admin` database.

---

### 2. Resource Requests vs. Limits
Every container has resource **requests** and **limits** configured:
- **Flask**: request `0.2 CPU, 250Mi RAM` / limit `0.5 CPU, 500Mi RAM`
- **MongoDB**: request `0.2 CPU, 250Mi RAM` / limit `0.5 CPU, 500Mi RAM`

**Why do we set these?**
- **Requests (Guaranteed)**: This is what Kubernetes uses to decide which node has enough room to run the pod. It guarantees that the container always gets at least this much CPU and memory.
- **Limits (Ceiling)**: This is the maximum the container is allowed to use.
  - **CPU Limit**: If a pod uses more CPU than its limit, it gets **throttled** (slowed down), but it keeps running.
  - **Memory Limit**: If a pod uses more RAM than its limit, Kubernetes stops it immediately with an **Out Of Memory error (`OOMKilled`)** to protect the rest of the node.

---

### 3. Design Choices & Alternatives Considered

- **StatefulSet for MongoDB instead of Deployment**:
  A database needs stable storage and a consistent identity. If a database pod restarts, it must re-attach to the exact same persistent storage disk without data corruption. Deployments are designed for disposable, stateless apps (like Flask), while StatefulSets are built for databases.
- **ClusterIP for MongoDB**:
  MongoDB is an internal database and should never be exposed directly to the outside world. Using `ClusterIP` makes it reachable only by pods inside the Kubernetes cluster.
- **NodePort for Flask**:
  Using `NodePort` lets us easily reach the Flask app from our host computer during local development on Minikube without needing complex ingress controllers or cloud load balancers.
- **Kubernetes Secrets for Passwords**:
  Instead of hardcoding the database username and password in plain text inside deployment YAML files, we use Secrets so credentials can be managed safely.

---

## Testing & Verification

### 1. Testing Endpoints
Tested against the running service:
- `GET /` returns: `Welcome to the Flask app! The current time is: ...` (HTTP 200)
- `POST /data` with `{"sampleKey":"sampleValue"}` returns: `{"status": "Data inserted"}` (HTTP 201)
- `GET /data` returns: `[{"sampleKey":"sampleValue"}]` (HTTP 200)

### 2. Database Persistence Test
To test if data survives when MongoDB crashes or restarts:
1. Inserted data into MongoDB through the Flask API.
2. Deleted the MongoDB pod:
   ```bash
   kubectl delete pod mongodb-0
   ```
3. Kubernetes noticed the missing pod and automatically recreated `mongodb-0`.
4. Called `GET /data` again once the pod restarted. All previously inserted records were still there, confirming that the PersistentVolume kept the data intact.

### 3. Autoscaling (HPA) Load Test
We tested the autoscaler by sending heavy traffic to push CPU above the 15% threshold:
1. Ran `scripts/load_test.sh` which sent 60 concurrent requests to the Flask app for 120 seconds.
2. Under load, the HPA detected CPU crossing the threshold and started scaling.
3. The HPA automatically scaled the Flask deployment up from **2 pods to 5 pods** (the maximum configured limit).
4. After the test finished and traffic stopped, the HPA gradually scaled the pods back down to the minimum of 2.

**Before load (2 pods, idle):**

![Load test starting - 2 pods before scaling](screenshots/autoscaling_before.jpg)

**After scaling (5 pods running):**

![5 pods after HPA scaled up](screenshots/autoscaling_after.png)

### Issues Encountered and How They Were Solved
1. **Port 5000 occupied on macOS**:
   On macOS, the built-in "AirPlay Receiver" feature listens on port 5000 by default. This caused curl to return `403 Forbidden`. We resolved this by turning off AirPlay Receiver in macOS System Settings (`General -> AirDrop & AirPlay`) or testing on an alternate port.
2. **Metrics Server in Minikube**:
   By default, `kubectl get hpa` showed `cpu: <unknown>/70%`. HPA requires metrics-server to monitor CPU usage, which we resolved by running `minikube addons enable metrics-server`.

---

## Clean Up / Restart

To tear down all resources and start fresh:
```bash
./scripts/k8s_cleanup.sh
```
Or to restart the pods without deleting the configuration:
```bash
kubectl rollout restart deployment flask-app
kubectl rollout restart statefulset mongodb
```

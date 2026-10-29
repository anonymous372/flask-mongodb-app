#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Deploying Kubernetes Resources ==="

echo "1. Applying Secrets & Storage..."
kubectl apply -f "$DIR/k8s/01-mongo-secret.yaml"
kubectl apply -f "$DIR/k8s/02-mongo-storage.yaml"

echo "2. Applying MongoDB StatefulSet and Service..."
kubectl apply -f "$DIR/k8s/03-mongo-statefulset.yaml"
kubectl apply -f "$DIR/k8s/04-mongo-service.yaml"

echo "3. Applying Flask Secret, Deployment, and Service..."
kubectl apply -f "$DIR/k8s/05-flask-secret.yaml"
kubectl apply -f "$DIR/k8s/06-flask-deployment.yaml"
kubectl apply -f "$DIR/k8s/07-flask-service.yaml"

echo "4. Applying Flask Horizontal Pod Autoscaler (HPA)..."
kubectl apply -f "$DIR/k8s/08-flask-hpa.yaml"

echo -e "\n=== Deployment Submitted! Checking Status... ==="
kubectl get pv,pvc,statefulset,deployment,svc,hpa


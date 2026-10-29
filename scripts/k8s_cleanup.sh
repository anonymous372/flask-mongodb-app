#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Deleting all Kubernetes resources for Flask & MongoDB ==="
kubectl delete -f "$DIR/k8s/" --ignore-not-found=true

echo -e "\n=== Cleanup Complete! All pods, services, secrets, and controllers removed. ==="
kubectl get all,pv,pvc -l "app in (mongodb, flask-app)"


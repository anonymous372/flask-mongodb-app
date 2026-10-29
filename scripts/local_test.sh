#!/usr/bin/env bash
set -e

BASE_URL="${1:-http://localhost:5000}"

echo "=========================================="
echo "Testing Flask App Endpoints on $BASE_URL"
echo "=========================================="

echo -e "\n1. Testing GET / endpoint:"
curl -i -s "$BASE_URL/"
echo ""

echo -e "\n2. Testing POST /data endpoint:"
POST_RESP=$(curl -i -s -X POST -H "Content-Type: application/json" -d '{"sampleKey":"sampleValue"}' "$BASE_URL/data")
echo "$POST_RESP"

echo -e "\n3. Testing GET /data endpoint:"
GET_RESP=$(curl -i -s "$BASE_URL/data")
echo "$GET_RESP"

echo -e "\n4. Testing /health endpoint:"
curl -i -s "$BASE_URL/health"
echo ""

echo -e "\nAll tests completed successfully!"


from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os
import urllib.parse

# Initialize the Flask application
app = Flask(__name__)

# MongoDB Connection Setup
# Supports authenticated connection via 'MONGODB_URI' or individual env variables
mongo_uri = os.environ.get("MONGODB_URI")

if not mongo_uri:
    mongo_user = os.environ.get("MONGO_USERNAME")
    mongo_password = os.environ.get("MONGO_PASSWORD")
    mongo_host = os.environ.get("MONGO_HOST", "localhost")
    mongo_port = os.environ.get("MONGO_PORT", "27017")
    mongo_db_name = os.environ.get("MONGO_DB", "flask_db")
    mongo_auth_source = os.environ.get("MONGO_AUTH_SOURCE", "admin")

    if mongo_user and mongo_password:
        escaped_user = urllib.parse.quote_plus(mongo_user)
        escaped_pass = urllib.parse.quote_plus(mongo_password)
        mongo_uri = f"mongodb://{escaped_user}:{escaped_pass}@{mongo_host}:{mongo_port}/{mongo_db_name}?authSource={mongo_auth_source}"
    else:
        # Default fallback for local development without authentication
        mongo_uri = "mongodb://localhost:27017/"

# Initialize MongoClient with the determined URI
client = MongoClient(mongo_uri)

# Connect to database and collection
db_name = os.environ.get("MONGO_DB", "flask_db")
db = client[db_name]
collection = db.data

# Define the route for the root URL
@app.route('/')
def index():
    # CPU computation to demonstrate autoscaling under load
    _ = sum(i * i for i in range(500_000))
    # Return a welcome message with the current time
    return f"Welcome to the Flask app! The current time is: {datetime.now()}"

# Define the route for the '/data' endpoint
# This endpoint supports both GET and POST methods
@app.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'POST':
        # If the request method is POST, get the JSON data from the request
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400
        # Insert the data into the 'data' collection in MongoDB
        collection.insert_one(data)
        # Return a success message with status code 201 (Created)
        return jsonify({"status": "Data inserted"}), 201
    elif request.method == 'GET':
        # If the request method is GET, retrieve all documents from the 'data' collection
        # Convert the documents to a list, excluding the '_id' field
        data = list(collection.find({}, {"_id": 0}))
        # Return the data as a JSON response with status code 200 (OK)
        return jsonify(data), 200

# Health check route for Kubernetes Liveness and Readiness probes
@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

# Run the Flask application
# The application will listen on all available IP addresses (0.0.0.0) and port 5000
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


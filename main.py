from flask import Flask, jsonify, request
import requests
from datetime import datetime, timedelta
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB connection
MONGO_URI = "mongodb+srv://Key-gen:12251978@keycluster.lxnqhrb.mongodb.net/?retryWrites=true&w=majority&appName=KeyCluster"
client = MongoClient(MONGO_URI)
db = client["KeyDatabase"]
collection = db["claimed_ips"]

# Generator server URL
GENERATOR_URL = "https://key-generator-1d.onrender.com/getKey"

@app.route("/")
def get_key():
    try:
        user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        if not user_ip:
            user_ip = "unknown"

        # Check if IP already claimed within 24 hours
        record = collection.find_one({"ip": user_ip})
        if record:
            last_claim = record["timestamp"]
            if datetime.utcnow() - last_claim < timedelta(days=1):
                return jsonify({"error": "You’ve already claimed a key today"}), 403

        # Fetch key from generator server
        response = requests.get(GENERATOR_URL)
        response.raise_for_status()
        key = response.json().get("key")
        if not key:
            return jsonify({"error": "Failed to get key from generator"}), 500

        # Save claim to MongoDB
        collection.update_one(
            {"ip": user_ip},
            {"$set": {"timestamp": datetime.utcnow(), "key": key}},
            upsert=True
        )

        return jsonify({"key": key})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)

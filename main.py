from flask import Flask, jsonify, request
import json
import os
from datetime import datetime, timedelta
import requests

app = Flask(__name__)

# File to store claimed IPs
DATA_FILE = "claimed.json"

GENERATOR_URL = "https://key-generator-1d.onrender.com/getKey"

# Ensure data file exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f, indent=4)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/")
def get_key():
    data = load_data()
    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if not user_ip:
        user_ip = "unknown"

    last_claim_str = data.get(user_ip)
    if last_claim_str:
        last_claim = datetime.fromisoformat(last_claim_str)
        if datetime.utcnow() - last_claim < timedelta(days=1):
            return jsonify({"error": "You’ve already claimed a key today"}), 403

    # Fetch key from generator server
    try:
        response = requests.get(GENERATOR_URL)
        response.raise_for_status()
        key = response.json().get("key")
    except Exception as e:
        return jsonify({"error": "Failed to fetch key"}), 500

    # Record claim
    data[user_ip] = datetime.utcnow().isoformat()
    save_data(data)

    return jsonify({"key": key})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)

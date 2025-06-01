# app.py - Flask backend, ktorý slúži aj frontend (index.html)

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

MEDIA_BASE_PATH = os.getenv("MEDIA_BASE_PATH", "/tmp")
ARIA2_RPC_URL = os.getenv("ARIA2_RPC_URL", "http://localhost:6800/jsonrpc")

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")
    folder = data.get("folder")
    dest_path = os.path.join(MEDIA_BASE_PATH, folder)
    os.makedirs(dest_path, exist_ok=True)

    options = {"dir": dest_path}
    payload = {
        "jsonrpc": "2.0",
        "method": "aria2.addUri",
        "id": "downloader",
        "params": [[url], options]
    }
    try:
        r = requests.post(ARIA2_RPC_URL, json=payload)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/folders")
def folders():
    if not os.path.exists(MEDIA_BASE_PATH):
        return jsonify([])
    entries = [f for f in os.listdir(MEDIA_BASE_PATH) if os.path.isdir(os.path.join(MEDIA_BASE_PATH, f))]
    return jsonify(entries)

@app.route("/downloads")
def downloads():
    payload = {
        "jsonrpc": "2.0",
        "method": "aria2.tellActive",
        "id": "downloader",
        "params": []
    }
    try:
        r = requests.post(ARIA2_RPC_URL, json=payload)
        return jsonify(r.json().get("result", []))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

import os
import duckdb
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

MEDIA_BASE_PATH = os.getenv("MEDIA_BASE_PATH", "/tmp")
MOVIES_FOLDER = os.getenv("MOVIES_FOLDER", "MOVIES")
TV_SERIES_FOLDER = os.getenv("TV_SERIES_FOLDER", "TV_SERIES")
ARIA2_RPC_URL = os.getenv("ARIA2_RPC_URL", "http://localhost:6800/jsonrpc")
DB_PATH = os.path.join(MEDIA_BASE_PATH, "folders.db")

def add_folder_to_db(media_type, folder):
    con = duckdb.connect(DB_PATH)
    con.execute("INSERT OR IGNORE INTO folders VALUES (?, ?)", (media_type, folder))
    con.close()

def get_folders_from_db(media_type):
    con = duckdb.connect(DB_PATH)
    result = con.execute("SELECT name FROM folders WHERE media_type = ?", (media_type,)).fetchall()
    con.close()
    return [row[0] for row in result]

def get_media_folder(media_type):
    if media_type == "MOVIE":
        return MOVIES_FOLDER
    elif media_type == "TV_SERIE":
        return TV_SERIES_FOLDER
    else:
        return None

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")
    media_type = data.get("media_type")  # MOVIE or TV_SERIE
    if media_type not in ("MOVIE", "TV_SERIE"):
        return jsonify({"error": "Invalid media_type"}), 400
    folder = data.get("folder")
    media_folder = get_media_folder(media_type)
    if not media_folder:
        return jsonify({"error": "Invalid media_type"}), 400
    dest_path = os.path.join(MEDIA_BASE_PATH, media_folder, folder)
    os.makedirs(dest_path, exist_ok=True)
    add_folder_to_db(media_type, folder)

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
    media_type = request.args.get("media_type")
    if media_type not in ("MOVIE", "TV_SERIE"):
        return jsonify({"error": "Invalid media_type"}), 400
    folders = get_folders_from_db(media_type)
    return jsonify(folders)

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

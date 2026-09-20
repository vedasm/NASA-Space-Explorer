from datetime import date, datetime
import requests
from flask import Flask, abort, jsonify, render_template, request, send_from_directory
from nasa_api import get_apod, get_asteroids, get_epic_images

app = Flask(__name__, template_folder=".", static_folder=None)

@app.route("/static/<path:filename>")
def static_assets(filename):
    assets = {"css/style.css": "style.css", "js/main.js": "main.js"}
    asset = assets.get(filename)
    if asset is None:
        abort(404)
    return send_from_directory(app.root_path, asset)

def api_response(loader, *args):
    try:
        return jsonify(loader(*args))
    except requests.exceptions.HTTPError as error:
        status = error.response.status_code if error.response else 500
        if status == 429:
            message = "NASA's rate limit is full. Wait an hour or use your own API key."
        elif status == 404:
            message = "NASA has no data for that request."
        else:
            message = f"NASA returned status {status}."
        return jsonify({"error": message}), 502
    except requests.exceptions.Timeout:
        return jsonify({"error": "NASA took too long to respond. Try again."}), 504
    except requests.exceptions.RequestException:
        return jsonify({"error": "Could not reach NASA. Check your connection."}), 502

@app.route("/")
def index():
    return render_template("index.html", today=date.today().isoformat())

@app.route("/api/apod")
def apod():
    return api_response(get_apod)

@app.route("/api/asteroids")
def asteroids():
    return api_response(get_asteroids)

def epic_data(selected):
    return {"date": selected, "images": get_epic_images(selected)}

@app.route("/api/epic")
def epic():
    selected = request.args.get("date", "")
    try:
        datetime.strptime(selected, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Pick a date in YYYY-MM-DD format."}), 400

    return api_response(epic_data, selected)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
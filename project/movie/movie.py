
import os
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(
    __name__,
    static_folder='../static',
    template_folder='templates'
)

# --- CONFIGURATION ---
TMDB_API_KEY = "63373768892642daef3a800edfd3a111" 
BASE_URL = "https://api.themoviedb.org/3"

def fetch_tmdb(endpoint, params={}):
    """Helper function to securely interface with the TMDb API from the backend."""
    # This must literally be "api_key" so TMDb understands the query parameter
    params["api_key"] = TMDB_API_KEY
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", params=params)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error connecting to TMDb API: {e}")
    return None

# --- WEB PAGE ROUTE ---
@app.route("/")
def index():
    """Serves the main single-page application frontend (saved as movie.html)."""
    return render_template("movie.html")

# --- SECURE API PROXY ENDPOINTS ---
@app.route("/api/trending")
def trending():
    """Proxies weekly trending movies."""
    data = fetch_tmdb("/trending/movie/week")
    if data:
        return jsonify(data.get("results", [])[:12])
    return jsonify([])

@app.route("/api/search")
def search():
    """Proxies the movie search query securely."""
    query = request.args.get("q", "")
    if not query:
        return jsonify([])
    data = fetch_tmdb("/search/movie", {"query": query})
    if data:
        return jsonify(data.get("results", [])[:12])
    return jsonify([])

@app.route("/api/recommendations/<int:movie_id>")
def recommendations(movie_id):
    """Fetches recommendations based on TMDb's collaborative filtering algorithms."""
    data = fetch_tmdb(f"/movie/{movie_id}/recommendations")
    if data:
        return jsonify(data.get("results", [])[:6])
    return jsonify([])

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
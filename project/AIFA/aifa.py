import os
import logging
from flask import Flask, render_template, jsonify, request
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure basic logging
logging.basicConfig(level=logging.INFO)

app = Flask(
    __name__,
    static_folder='../static',
    template_folder='templates'
)

# OpenRouter Client Setup
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY")
)

# Allow CORS headers for future domain deployments
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

@app.route("/")
def index():
    return render_template("aifa.html")

# strict_slashes=False prevents 404s when requests end with /api/chat/
# Accept both endpoint variations
@app.route("/chat", methods=["POST"], strict_slashes=False)
@app.route("/api/chat", methods=["POST"], strict_slashes=False)
def chat():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON received"}), 400

    user_msg = data.get("message")

    if not user_msg:
        return jsonify({"error": "No message provided"}), 400

    try:
        response = client.chat.completions.create(
            model="openrouter/free",   
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are AIFA, an effortlessly cool Gen Z companion. "
                        "Your style is modern, aesthetic, witty, and low-key unbothered yet engaging. "
                        "Use modern Gen Z slang, lowercase vibe, and concise phrasing naturally—never force it or cringe. "
                        "Keep every response super short, punchy, and interesting. Never ramble or bore the user."
                    )
                },
                {
                    "role": "user",
                    "content": user_msg
                }
            ]
        )

        return jsonify({
            "response": response.choices[0].message.content
        })

    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        return jsonify({"error": "An error occurred processing your request"}), 500

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
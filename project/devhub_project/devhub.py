import os
from flask import Flask, render_template, request, jsonify
import requests
from models import db, Snippet
from sqlalchemy import or_

app = Flask(
    __name__,
    static_folder='../static',
    template_folder='templates'
)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'devhub.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def index():
    return render_template('devhub.html')

@app.route('/api/snippets', methods=['POST'])
def save_snippet():
    # Use request.get_json() instead of requests.json
    data = request.get_json()
    new_snippet = Snippet(
        title=data.get('title', 'Untitled'), 
        code=data.get('code', ''),
        tags=data.get('tags', '') # Added tag handling
    )
    db.session.add(new_snippet)
    db.session.commit()
    return jsonify({"status": "success"}), 201

@app.route('/api/snippets/search/<query>')
def search_snippets(query):
    results = Snippet.query.filter(or_(Snippet.title.contains(query), Snippet.tags.contains(query))).all()
    return jsonify([{'title': s.title, 'code': s.code, 'tags': s.tags} for s in results])

@app.route('/api/github/<username>')
def github_analytics(username):
    # Combined Proxy + Analytics logic
    user_res = requests.get(f"https://api.github.com/users/{username}").json()
    repos_res = requests.get(f"https://api.github.com/users/{username}/repos").json()
    
    # Safely handle language list
    languages = []
    if isinstance(repos_res, list):
        languages = list(set([r['language'] for r in repos_res if r.get('language')]))
        
    return jsonify({
        "name": user_res.get('name'),
        "public_repos": user_res.get('public_repos', 0),
        "languages": languages
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False  # Prevents spawning child processes
    )
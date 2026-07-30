import os
import csv
import requests
import gspread
import json
from google.oauth2.service_account import Credentials
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, Response

app = Flask(__name__, template_folder='.')
app.url_map.strict_slashes = False

# Absolute path to built frontend static files
AUTOINSIGHT_DIST = os.path.join(app.root_path, 'project', 'automated_ai', 'frontend', 'dist')


# 0. Dedicated Route for AutoInsight Static Frontend (Placed first so it isn't overridden)
@app.route('/api/autoinsight-frontend/', defaults={'path': ''})
@app.route('/api/autoinsight-frontend/<path:path>')
def proxy_autoinsight_frontend(path):
    if path != "" and os.path.exists(os.path.join(AUTOINSIGHT_DIST, path)):
        return send_from_directory(AUTOINSIGHT_DIST, path)
    return send_from_directory(AUTOINSIGHT_DIST, 'index.html')


# 1. Route to serve CSS files from root
@app.route('/<filename>.css')
def serve_css(filename):
    return send_from_directory('.', f'{filename}.css')


# 2. Route to serve images and static files from the assets folder
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)


# 3. Universal Favicon & Icon Handler (handles root and /api/<service>/ requests)
@app.route('/<icon_name>.ico')
@app.route('/api/<service_name>/<icon_name>.ico')
def serve_root_ico(icon_name, service_name=None):
    # Check if icon exists in specific project static folder first
    if service_name and os.path.exists(os.path.join('project', service_name, 'static', f'{icon_name}.ico')):
        return send_from_directory(os.path.join('project', service_name, 'static'), f'{icon_name}.ico')
    if service_name and os.path.exists(os.path.join('project', service_name, 'frontend', f'{icon_name}.ico')):
        return send_from_directory(os.path.join('project', service_name, 'frontend'), f'{icon_name}.ico')
    # Check assets directory
    if os.path.exists(os.path.join('assets', f'{icon_name}.ico')):
        return send_from_directory('assets', f'{icon_name}.ico')
    return send_from_directory('.', f'{icon_name}.ico')


# 4. Global Static File Handler
@app.route('/static/<path:filename>')
@app.route('/api/<service_name>/static/<path:filename>')
def serve_global_static(filename, service_name=None):
    if service_name:
        dir_name = service_name.replace('-', '_')
        frontend_dir = os.path.join('project', dir_name, 'frontend')
        static_dir = os.path.join('project', dir_name, 'static')
        
        if os.path.exists(os.path.join(frontend_dir, filename)):
            return send_from_directory(frontend_dir, filename)
        if os.path.exists(os.path.join(static_dir, filename)):
            return send_from_directory(static_dir, filename)

    # Search all project subdirectories if requested directly from root /static/
    for proj_dir in os.listdir('project'):
        candidate = os.path.join('project', proj_dir, 'static', filename)
        if os.path.exists(candidate):
            return send_from_directory(os.path.join('project', proj_dir, 'static'), filename)
            
        candidate_frontend = os.path.join('project', proj_dir, 'frontend', filename)
        if os.path.exists(candidate_frontend):
            return send_from_directory(os.path.join('project', proj_dir, 'frontend'), filename)

    # Fallback checks across assets or main static folder
    if os.path.exists(os.path.join('assets', filename)):
        return send_from_directory('assets', filename)
    if os.path.exists(os.path.join('frontend', filename)):
        return send_from_directory('frontend', filename)
    
    return send_from_directory('static', filename)


def write_to_csv(data):
    """Helper function to append form submissions to database.csv safely and back up to Google Sheets."""
    email = data.get("email")
    subject = data.get("subject")
    message = data.get("message")

    # Local file save
    with open('database.csv', mode='a', newline='', encoding='utf-8') as database:
        csv_writer = csv.writer(
            database, 
            delimiter=',', 
            quotechar='"', 
            quoting=csv.QUOTE_MINIMAL
        )
        csv_writer.writerow([email, subject, message])

    # Cloud persistent storage (Google Sheets / gspread)
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        gc = None

        # Option A: Check for Railway / Cloud Environment Variable first
        google_json_str = os.environ.get('GOOGLE_CREDENTIALS_JSON') or os.environ.get('GOOGLE_CREDENTIALS')
        if google_json_str:
            creds_dict = json.loads(google_json_str)
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
            gc = gspread.authorize(creds)
        # Option B: Fallback to local credentials.json file (for local development)
        elif os.path.exists('credentials.json'):
            gc = gspread.service_account(filename='credentials.json')

        if gc:
            sheet_title = os.environ.get("GOOGLE_SHEET_TITLE", "Portfolio Submissions")
            sh = gc.open(sheet_title).sheet1
            sh.append_row([email, subject, message])
            print("Successfully synced submission to Google Sheets.")
    except Exception as sheet_err:
        print(f"Google Sheets sync warning: {sheet_err}")


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/handbook.html')
def handbook():
    return render_template('handbook.html')

@app.route('/tools.html')
def tools():
    return render_template('tools.html')

@app.route('/game.html')
def game():
    return render_template('game.html')

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response


@app.route('/submit_form', methods=['POST', 'GET'])
def submit_form():
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            write_to_csv(data)
            print(f"Form submission saved: {data.get('email')}")
            return redirect(url_for('html_page', page_name='thankyou.html'))
        except Exception as e:
            print(f"Database write error: {e}")
            return 'Could not save message to database.'
    else:
        return 'Method not allowed or form submission failed. Please try again.'


SERVICES = {
    "ai-analytics": "http://127.0.0.1:5001",
    "aifa": "http://127.0.0.1:5002",
    "autoinsight": "http://127.0.0.1:5003",
    "devhub": "http://127.0.0.1:5004",
    "movie": "http://127.0.0.1:5005",
    "quietspace": "http://127.0.0.1:5006",
    "queitspace": "http://127.0.0.1:5006",  # Support both spellings
    "stocks": "http://127.0.0.1:5007",
    "stock": "http://127.0.0.1:5007",
    "autoinsight-frontend": "http://127.0.0.1:5008"
}

# -------------------------------------------------------------
# 1. API REVERSE PROXY ROUTE
# Forward requests like: /api/aifa/chat -> http://127.0.0.1:5002/chat
# -------------------------------------------------------------
@app.route(
    '/api/<service_name>',
    defaults={'path': ''},
    methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    strict_slashes=False
)
@app.route(
    '/api/<service_name>/<path:path>',
    methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    strict_slashes=False
)
def proxy_api(service_name, path):

    print("=" * 60)
    print("Incoming Request")
    print("request.path :", request.path)
    print("service_name :", service_name)
    print("path         :", path)
    print("=" * 60)

    if service_name not in SERVICES:
        return {"error": f"Service '{service_name}' not found"}, 404
    
    clean_path = path.strip("/")
    target_url = (
        f"{SERVICES[service_name]}/{clean_path}"
        if clean_path
        else SERVICES[service_name]
    )
    print("Forwarding to:", target_url)
    
    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers={key: value for (key, value) in request.headers if key.lower() != 'host'},
            data=request.get_data(),
            cookies=request.cookies,
            params=request.args,
            allow_redirects=False
        )
        
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]

        return Response(resp.content, resp.status_code, headers)
    except requests.exceptions.ConnectionError:
        return {"error": f"Could not connect to {service_name} backend on {SERVICES[service_name]}"}, 502


# Dedicated route to showcase a specific project UI inside your portfolio wrapper
@app.route('/project/<project_name>')
def show_project(project_name):
    # Pass the project name to index/viewer template
    return render_template('project_viewer.html', project=project_name)


# Generic HTML renderer fallback (kept at bottom so it doesn't hijack other routes)
@app.route('/<string:page_name>')
def html_page(page_name):
    try:
        return render_template(page_name)
    except Exception:
        return "Page not found.", 404


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
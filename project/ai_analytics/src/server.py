import os
import csv
import requests
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, Response

app = Flask(__name__, template_folder='.')
app.url_map.strict_slashes = False


# 1. Route to serve CSS files from root
@app.route('/<filename>.css')
def serve_css(filename):
    return send_from_directory('.', f'{filename}.css')


# 2. Route to serve images and static files from the assets folder
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)


# 3. Universal Favicon & Icon Handler
@app.route('/<icon_name>.ico')
@app.route('/api/<service_name>/<icon_name>.ico')
def serve_root_ico(icon_name, service_name=None):
    if service_name and os.path.exists(os.path.join('project', service_name, 'static', f'{icon_name}.ico')):
        return send_from_directory(os.path.join('project', service_name, 'static'), f'{icon_name}.ico')
    if service_name and os.path.exists(os.path.join('project', service_name, 'frontend', f'{icon_name}.ico')):
        return send_from_directory(os.path.join('project', service_name, 'frontend'), f'{icon_name}.ico')
    if os.path.exists(os.path.join('assets', f'{icon_name}.ico')):
        return send_from_directory('assets', f'{icon_name}.ico')
    return send_from_directory('.', f'{icon_name}.ico')


# 4. Global Static File Handler
@app.route('/static/<path:filename>')
@app.route('/api/<service_name>/static/<path:filename>')
def serve_global_static(filename, service_name=None):
    if service_name:
        frontend_dir = os.path.join('project', service_name, 'frontend')
        static_dir = os.path.join('project', service_name, 'static')
        
        if os.path.exists(os.path.join(frontend_dir, filename)):
            return send_from_directory(frontend_dir, filename)
        if os.path.exists(os.path.join(static_dir, filename)):
            return send_from_directory(static_dir, filename)
    
    if os.path.exists(os.path.join('assets', filename)):
        return send_from_directory('assets', filename)
    if os.path.exists(os.path.join('frontend', filename)):
        return send_from_directory('frontend', filename)
    
    return send_from_directory('static', filename)


def write_to_csv(data):
    """Helper function to append form submissions to database.csv safely."""
    with open('database.csv', mode='a', newline='', encoding='utf-8') as database:
        email = data.get("email")
        subject = data.get("subject")
        message = data.get("message")
        
        csv_writer = csv.writer(
            database, 
            delimiter=',', 
            quotechar='"', 
            quoting=csv.QUOTE_MINIMAL
        )
        csv_writer.writerow([email, subject, message])


@app.route('/')
def home():
    return render_template('index.html')


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
    "queitspace": "http://127.0.0.1:5006",
    "stocks": "http://127.0.0.1:5007",
    "stock": "http://127.0.0.1:5007",
    "autoinsight-frontend": "http://127.0.0.1:3000"
}

# -------------------------------------------------------------
# 1. API REVERSE PROXY ROUTE
# Forward requests like: /api/ai-analytics/api/kpis -> http://127.0.0.1:5001/api/kpis
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
    if service_name not in SERVICES:
        return {"error": f"Service '{service_name}' not found"}, 404
    
    clean_path = path.strip("/")
    target_url = (
        f"{SERVICES[service_name]}/{clean_path}"
        if clean_path
        else SERVICES[service_name]
    )
    
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


@app.route('/project/<project_name>')
def show_project(project_name):
    return render_template('project_viewer.html', project=project_name)


@app.route('/<string:page_name>')
def html_page(page_name):
    try:
        return render_template(page_name)
    except Exception:
        return "Page not found.", 404

# Insert this right above @app.route('/static/<path:filename>')

# Catch JavaScript / JS bundle files directly
@app.route('/<filename>.js')
@app.route('/project/<filename>.js')
def serve_root_js(filename):
    # Check root assets or frontend folders
    if os.path.exists(f'{filename}.js'):
        return send_from_directory('.', f'{filename}.js')
    if os.path.exists(os.path.join('assets', f'{filename}.js')):
        return send_from_directory('assets', f'{filename}.js')
    return "JS file not found.", 404

# Catch sub-service frontend static files under /api/<service_name>/...
@app.route('/api/<service_name>/<path:filename>')
def serve_service_frontend_files(service_name, filename):
    # Normalize folder name (support both ai-analytics and ai_analytics)
    folder_name = service_name.replace('-', '_')
    
    possible_paths = [
        os.path.join('project', service_name, 'frontend'),
        os.path.join('project', folder_name, 'frontend'),
        os.path.join('project', service_name, 'static'),
        os.path.join('project', folder_name, 'static'),
    ]
    
    for path in possible_paths:
        if os.path.exists(os.path.join(path, filename)):
            return send_from_directory(path, filename)
            
    return {"error": f"File '{filename}' not found in {service_name}"}, 404


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
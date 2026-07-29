import hashlib
import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# Enable CORS so your HTML file can talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_file_path = os.path.join(os.path.dirname(__file__), "QS.html")
    if os.path.exists(html_file_path):
        return FileResponse(html_file_path)
    return HTMLResponse(content="<h1>QuietSpace Security Service Active</h1>", status_code=200)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# A simple structure to receive the password from the website
class PasswordCheckRequest(BaseModel):
    password: str

# Optional: Add your real HIBP API key for the email check
HIBP_API_KEY = "YOUR_HIBP_API_KEY_HERE"


# 📧 Endpoint 1: Check Email Breaches
@app.get("/api/check-email")
def check_email(email: str):
    if HIBP_API_KEY == "YOUR_HIBP_API_KEY_HERE":
        # Mock demo data if you don't have a paid key yet
        if "test@example.com" in email:
            return {"breached": True, "breaches": ["Adobe", "Canva"]}
        return {"breached": False, "breaches": []}

    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
    headers = {
        "hibp-api-key": HIBP_API_KEY,
        "user-agent": "QuietSpaceChecker/1.0"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return {"breached": True, "breaches": response.json()}
    elif response.status_code == 404:
        return {"breached": False, "breaches": []}
    else:
        raise HTTPException(status_code=response.status_code, detail="HIBP API Error")


# 🔑 Endpoint 2: Check Password Breaches (using hashlib & requests)
@app.post("/api/check-password")
def check_password(payload: PasswordCheckRequest):
    password = payload.password
    if not password:
        raise HTTPException(status_code=400, detail="Password cannot be empty")
    
    # 1. Use hashlib to generate the SHA-1 hash
    sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix = sha1_hash[:5]
    suffix = sha1_hash[5:]
    
    # 2. Use requests to fetch matching prefixes (k-anonymity)
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    headers = {"Add-Padding": "true", "User-Agent": "QuietSpaceBackend/1.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Could not contact security database")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=500, detail="Database network error")
    
    # 3. Check if the suffix exists in the API response
    hashes = (line.split(':') for line in response.text.splitlines())
    for target_suffix, count in hashes:
        if target_suffix == suffix:
            return {"breached": True, "count": int(count)}
            
    return {"breached": False, "count": 0}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5006))
    uvicorn.run("QS:app", host="0.0.0.0", port=port, reload=False)
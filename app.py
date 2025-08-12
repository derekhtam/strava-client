import os
import json
from flask import Flask, request
from stravalib.client import Client
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env

app = Flask(__name__)

CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
REDIRECT_URI = os.getenv('STRAVA_REDIRECT_URI')

TOKEN_FILE = '.strava_tokens.json'

def load_tokens():
    try:
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
            return data.get('access_token'), data.get('refresh_token'), data.get('expires_at')
    except Exception:
        return None, None, None

def save_tokens(access_token, refresh_token, expires_at):
    with open(TOKEN_FILE, 'w') as f:
        json.dump({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_at': expires_at
        }, f)
    try:
        os.chmod(TOKEN_FILE, 0o600)
    except Exception:
        pass

# Load tokens at startup
access_token, refresh_token, expires_at = load_tokens()
client = Client(
    access_token=access_token,
    refresh_token=refresh_token,
    token_expires=expires_at
)

@app.route('/')
def index():
    auth_url = client.authorization_url(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=['read', 'activity:read_all']
    )
    return f'<a href="{auth_url}">Authorize with Strava</a>'

@app.route('/authorization')
def authorization():
    global client, access_token, refresh_token, expires_at
    code = request.args.get('code')
    if not code:
        return 'No authorization code provided', 400

    token_response = client.exchange_code_for_token(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        code=code
    )
    access_token = token_response['access_token']
    refresh_token = token_response['refresh_token']
    expires_at = token_response['expires_at']
    # Re-instantiate client with new tokens
    client = Client(
        access_token=access_token,
        refresh_token=refresh_token,
        token_expires=expires_at
    )
    save_tokens(access_token, refresh_token, expires_at)
    return 'Authorization successful! <br><a href="/activities">View Activities</a>'

@app.route('/activities')
def activities():
    activities = [vars(a) for a in client.get_activities(limit=5)]
    return '<pre>' + json.dumps(activities, indent=2, default=str) + '</pre>'

if __name__ == '__main__':
    app.run(debug=True)

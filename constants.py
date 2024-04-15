import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.environ.get('API_TOKEN')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')
SCOPE = os.environ.get('SCOPE')
AUTH_URL = os.environ.get('AUTH_URl')
MONGO_URI = os.environ.get('MONGO_URI')
PATTERN = r'(\w+)\s*=\s*"([^"]*)"'
VALID, INVALID, EXPIRED = range(3)
AUTH_URL = f'https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPE}'
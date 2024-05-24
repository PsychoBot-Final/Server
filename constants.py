import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY')
API_TOKEN = os.environ.get('API_TOKEN')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI_PUBLIC = os.environ.get('REDIRECT_URI_PUBLIC')
REDIRECT_URI_LOCAL = os.environ.get('REDIRECT_URI_LOCAL')
SCOPE = os.environ.get('SCOPE')
MONGO_URI = os.environ.get('MONGO_URI')
PATTERN = r'(\w+)\s*=\s*"([^"]*)"'
VALID, INVALID, EXPIRED, IN_USE = range(4)
DELIMITER = '|'
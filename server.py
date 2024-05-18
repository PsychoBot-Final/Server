import re
import logging
from functools import wraps
from zenora import APIClient
from flask_socketio import SocketIO
from database import (
    get_user_data
)
from flask import (
    Flask, 
    jsonify,
    request, 
    session,
    redirect
)
from constants import (
    API_TOKEN, 
    CLIENT_ID, 
    CLIENT_SECRET,
    SCOPE,
    PATTERN,
    SECRET_KEY,
    REDIRECT_URI_PUBLIC,
    VALID,
    INVALID,
    EXPIRED
)

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
server = SocketIO(app, cors_allowed_origins=["http://www.psychobot.org"])
zenora_client = APIClient(API_TOKEN, client_secret=CLIENT_SECRET)

user_sessions = {}
session_users = {}


# def verify_discord_user(discord_id):
#     # This function should verify the discord_id with your database or other means
#     user_data = get_user_data(discord_id)
#     return user_data

# def token_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         discord_id = request.args.get('discord_id')
#         if not discord_id or not verify_discord_user(discord_id):
#             emit('unauthorized', {'message': 'Unauthorized'}, to=request.sid)
#             return
#         return f(*args, **kwargs, user_data=verify_discord_user(discord_id))
#     return decorated_function

# SocketIO #

@server.event
def connect() -> None:
    sid = request.sid
    discord_id = request.args.get('discord_id')
    if not discord_id:
        send_message('user_status', INVALID)
        return
    
    try:
        discord_id = int(discord_id)
        logging.info(f'User {discord_id} attempting to connect.')
    except ValueError:
        send_message('user_status', INVALID)
        return
    
    if not (user_data:= get_user_data(discord_id)):
        logging.info(f'User {discord_id} is not a member.')
        send_message('user_status', INVALID)
        return
    
    user_status = user_data['status']
    if user_status != VALID:
        logging.info(f'User {discord_id} does not have a valid membership.')
        return
    

    




@server.event
def disconnect() -> None:
    sid = request.sid
    if sid in session_users:
        discord_id = session_users[sid]
        del user_sessions[discord_id]
        del session_users[sid]
        logging.info(f'User {discord_id} has disconnected.')

def send_message(event: str, data: any, sid: any) -> None:
    try:
        server.emit(event, data, to=sid)
    except Exception as e:
        print(f'Error Send Message ({event}):', e)

# Discord Authentication #

@app.route('/')
def root():
    auth_key = request.args.get('auth_key')
    print('Auth Key:', auth_key)
    if auth_key == '12345':
        return redirect(f'https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI_PUBLIC}&response_type=code&scope={SCOPE}')
    else:
        return jsonify({'Error': 'verifying file integrity!'})

# @app.route('/version/<string:script_name>', methods=['GET'])
# def handle_script_version(script_name: str) -> any:
#     result = get_script_version(script_name)
#     return jsonify({'version': result})

# @app.route('/version/')
# def handle_version():
#     bot_version = get_bot_version()
#     return jsonify({'bot-version': bot_version})

@app.route('/callback')
def callback():
    code = request.args['code']
    access_token = zenora_client.oauth.get_access_token(code, REDIRECT_URI_PUBLIC).access_token
    session['token'] = access_token
    return redirect('/verified')

@app.route('/verified')
def get_verified():
    if 'token' in session:
        bearer_client = APIClient(session.get('token'), bearer=True)
        current_user = bearer_client.users.get_current_user()
        matches = re.findall(PATTERN, str(current_user))
        #
        user_data = dict(matches)
        user_id = int(user_data.get('id'))
        username = str(user_data.get('username'))
        #
        user_data = get_user_data(user_id)
        status = user_data.get('status')
        instances = user_data.get('instances')
        expiry_date = user_data.get('expiry_date')
        return jsonify({
            'user_id': user_id,
            'username': username,
            'expiry_date': expiry_date,
            'status': status,
            'instances': instances
        })
    return redirect('/')

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Error: {e}")
    return jsonify({"error": "An error occurred"}), 500
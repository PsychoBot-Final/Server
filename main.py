import re
import logging
import shortuuid
from typing import Union
from functools import wraps
from zenora import APIClient
from datetime import datetime
from flask_socketio import SocketIO

from flask import (
    Flask, 
    jsonify,
    request, 
    session,
    redirect,
    Response
)
from constants import (
    SCOPE,
    SECRET_KEY,
    CLIENT_SECRET,
    API_TOKEN,
    CLIENT_ID,
    REDIRECT_URI_PUBLIC,
    PATTERN,
    VALID,
    EXPIRED,
    INVALID,
    IN_USE
)
from database import (
    get_script,
    get_api_files,
    get_user_data,
    get_script_names,
    get_api_templates
)


logging.basicConfig(level=logging.INFO)


class UserManager:
    def __init__(self) -> None:
        self.user_uuid = {}
        self.uuid_users = {}
        self.user_sessions = {}
        self.session_users = {}
        self.user_expiry = {}

    def add_user(self, discord_id: int, expiry_date: str) -> str: # | None:
        uuid = self.generate_uuid()
        self.user_uuid[discord_id] = uuid
        self.uuid_users[uuid] = discord_id
        self.user_expiry[discord_id] = expiry_date
        return uuid
    
    def add_user_session(self, discord_id: int, session_id: str) -> bool:
        if discord_id in self.user_sessions:
            return False
        self.user_sessions[discord_id] = session_id
        self.session_users[session_id] = discord_id
        return True

    def get_expiry_by_user(self, discord_id: int) -> Union[str, None]:
        if discord_id not in self.user_expiry:
            return None
        return self.user_expiry.get(discord_id)

    def get_session_by_user(self, discord_id: int) -> Union[str, None]:
        if discord_id not in self.user_sessions:
            return None
        return self.user_sessions.get(discord_id)

    def get_user_by_session(self, session_id: str) -> Union[int, None]:
        if session_id not in self.session_users:
            return None
        return self.session_users.get(session_id)

    def get_uuid_by_user(self, discord_id: int) -> Union[str, None]:
        if discord_id not in self.user_uuid:
            return None
        return self.user_uuid.get(discord_id)

    def get_user_by_uuid(self, uuid: str) -> Union[int, None]:
        if uuid not in self.uuid_users:
            return None
        return self.uuid_users.get(uuid)
        
    def remove_user(self, session_id: str) -> bool:
        if session_id in self.session_users:
            discord_id = self.session_users.get(session_id)
            if discord_id in self.user_uuid:
                uuid = self.user_uuid.get(discord_id)
                del self.user_uuid[discord_id]
                del self.uuid_users[uuid]
                del self.user_sessions[discord_id]
                del self.session_users[session_id]
                del self.user_expiry[discord_id]
                return True
        return False

    def generate_uuid(self) -> str:
        while True:
            unique_id = shortuuid.uuid()
            if unique_id not in self.uuid_users:
                return unique_id

    

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
server = SocketIO(app, cors_allowed_origins=["http://www.psychobot.org"])
zenora_client = APIClient(API_TOKEN, client_secret=CLIENT_SECRET)
user_manager = UserManager()


def authorize_user(f):
    @wraps(f)
    def decorated_function(data: dict, *args, **kwargs):
        session_id: str = request.sid

        if not (uuid:= data.get('uuid')):
            logging.warning(f"Authorization failed: UUID is required (Session ID: {session_id}).")
            return

        if not (discord_id:= user_manager.get_user_by_uuid(uuid)):
            logging.warning(f'Failed to retrieve Discord ID from UUID {uuid}.')
            return

        logging.info(f'User {discord_id} has made a successful request to the server.')
        
        return f(data, *args, **kwargs)
    return decorated_function


@server.on('request_script_names')
@authorize_user
def on_request_script_names(data: any) -> dict:
    return {'result': get_script_names()}


@server.on('request_api_templates')
@authorize_user
def on_request_api_templates(data: any) -> dict:
    return {'result': get_api_templates()}


@server.on('request_api_files')
@authorize_user
def on_request_api_files(data: any) -> dict:
    return {'result': get_api_files()}


@server.on('request_script')
@authorize_user
def on_request_script(data: dict) -> dict:
    script_name: str = data.get('script_name')
    return {'result': get_script(script_name)}


@server.event
def connect() -> None:
    session_id: str = request.sid

    if not (uuid:= request.args.get('uuid', default=None, type=str)):
        send_message(event='user_status', data={'id': INVALID}, to=session_id)
        logging.warning(f'Client did not provide valid UUID.')
        return

    logging.info(f'Incoming UUID: {uuid}')

    if not (discord_id:= user_manager.get_user_by_uuid(uuid)):
        send_message(event='user_status', data={'id': INVALID}, to=session_id)
        logging.warning(f'No Discord ID exists for UUID {uuid}.')
        return
    
    if not (user_manager.add_user_session(discord_id, session_id)):
        send_message(event='user_status', data={'id': IN_USE}, to=session_id)
        logging.warning(f'Discord ID {discord_id} is already connected on Session ID {session_id}.')
        return
    
    if not (expiry_date:= user_manager.get_expiry_by_user(discord_id)):
        send_message(event='user_status', data={'id': INVALID}, to=session_id)
        logging.warning(f'No valid expiry date set for Discord ID {discord_id}.')
        return
    
    try:
        expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        send_message(event='user_status', data={'id': INVALID}, to=session_id)
        logging.error(f'Invalid expiry date format for Discord ID {discord_id}.')
        return

    if datetime.now() > expiry_date:
        send_message(event='user_status', data={'id': EXPIRED}, to=session_id)
        logging.warning(f'Discord ID {discord_id} membership expired.')
        return
    
    send_message(event='user_status', data={'id': VALID}, to=session_id)
    logging.info(f'Discord ID {discord_id} successfully connected.')
    
     
@server.event
def disconnect() -> None:
    session_id: str = request.sid
    try:
        if not user_manager.remove_user(session_id):
            logging.warning(f'Failed to remove user for session {session_id}. Session might not exist.')
        else:
            logging.info(f'Session {session_id} was successfully disconnected.')
    except Exception as e:
        logging.error(f'Error while disconnection session {session_id}: {e}')

        
def send_message(event: str, data: any, to: str) -> None:
    try:
        server.emit(event, data, to=to)
    except Exception as e:
        print(f'Error Send Message ({event}):', e)


@app.route('/favicon.ico')
def favicon() -> Response:
    return '', 204

@app.route('/')
def root() -> Response:
    auth_key = request.args.get('auth_key', default=None, type=str)
    if auth_key == '12345':
        return redirect(f'https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI_PUBLIC}&response_type=code&scope={SCOPE}')
    else:
        return jsonify({'Error': 'cannot connect!'})

@app.route('/callback')
def callback() -> Response:
    code = request.args['code']
    access_token = zenora_client.oauth.get_access_token(code, REDIRECT_URI_PUBLIC).access_token
    session['token'] = access_token
    return redirect('/verified')

@app.route('/verified')
def verified() -> Response:
    if 'token' in session:
        bearer_client = APIClient(session.get('token'), bearer=True)
        current_user = bearer_client.users.get_current_user()
        matches = re.findall(PATTERN, str(current_user))

        user_data = dict(matches)
        discord_id = int(user_data.get('id'))
        discord_username = str(user_data.get('username'))

        user_data = get_user_data(discord_id)
        expiry_date = user_data.get('expiry_date')
        uuid = user_manager.add_user(discord_id, expiry_date)
  
        return jsonify({
            'uuid': uuid,
            'discord_id': discord_id,
            'discord_username': discord_username,
            'expiry_date': expiry_date,
            'status': user_data.get('status'),
            'instances': user_data.get('instances')
        })
    return redirect('/')

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Error: {e} at {request.url}")
    # Should I add a return ?

if __name__ == '__main__':
    server.run(app, debug=True, host='0.0.0.0', port=5000)
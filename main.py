import re
import json
import base64
import configs
import socketio
from configs import get_bot_version
from zenora import APIClient
from flask_socketio import SocketIO
from user import User
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
    REDIRECT_URI, 
    SCOPE, 
    AUTH_URL,
    PATTERN
)
from database import (
    get_user_data,
    get_all_script_names
)


app = Flask(__name__)
app.config['SECRET_KEY'] = '063922124'
server = SocketIO(app)
zenora_client = APIClient(API_TOKEN, client_secret=CLIENT_SECRET)

user_sessions = {}
session_users = {}

# START OF SERVER

@server.on('connect')
def connect():
    print('INCOMING CONNECTION')

@server.on('disconnect')
def disconnect():
    global session_users
    print('Disconnected!')
    session_id = request.sid
    disconnected_user: User = session_users[session_id]
    disconnected_user.disconnect()
    del user_sessions[disconnected_user.user_id]
    del session_users[session_id]

@server.on('new_connection')
def new_connection(data):
    global user_sessions, session_users
    data = dict(data)
    user_id: int = data.get('user_id')
    expiry_date: str = data.get('expiry_date')
    if user_id in user_sessions:
        server.emit('id_in_use', {'user_id': user_id})
    else:
        session = request.sid
        user_sessions[user_id] = session
        session_users[session] = User(user_id, expiry_date)

# END OF SERVER

# START OF DISCORD AUTH

@app.route('/')
def root():
    return redirect(AUTH_URL)

# @app.route('/scripts/<string:script_name>', methods=['GET'])
# def get_script_source(script_name):
#     return jsonify({'id': script_name})
    # cript_name = request.args.get('script_name')

@app.route('/version/')
def handle_version():
    bot_version = get_bot_version()
    return jsonify({'bot-version': bot_version})

@app.route('/callback')
def callback():
    code = request.args['code']
    access_token = zenora_client.oauth.get_access_token(code, REDIRECT_URI).access_token
    session['token'] = access_token
    return redirect('/verified')

@app.route('/verified')
def get_verified():
    if 'token' in session:
        bearer_client = APIClient(session.get('token'), bearer=True)
        current_user = bearer_client.users.get_current_user()
        matches = re.findall(PATTERN, str(current_user))
        user_data = dict(matches)
        user_id = int(user_data.get('id'))
        username = str(user_data.get('username'))
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

# END OF DISCORD AUTH

if __name__ == '__main__':
    server.run(app, debug=True, host='0.0.0.0', port=5000)
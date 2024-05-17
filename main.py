import re
from configs import get_bot_version
from zenora import APIClient
from flask_socketio import SocketIO
from settings import REDIRECT_URI
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
    SECRET_KEY
)
from database import (
    get_api,
    get_script,
    get_user_data,
    get_script_names,
    get_api_templates,
    get_script_version
)


app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
server = SocketIO(app, cors_allowed_origins=["http://www.psychobot.org"])
zenora_client = APIClient(API_TOKEN, client_secret=CLIENT_SECRET)

user_sessions = {}
session_users = {}

# START OF SERVER

@server.on('connect')
def on_connect():
    global user_sessions, session_users
    session_id = request.sid
    user_id = request.args.get('user_id')
    if user_id is None:
        return
    try:
        user_id = int(user_id)
        print('User ID:', user_id)
    except ValueError as ve:
        print('Invalid type for User ID:', ve)
        return
    send_message('authenticated', not user_id in user_sessions, session_id)
    if not user_id in user_sessions:
        user_sessions[user_id] = session_id
        session_users[session_id] = user_id

@server.on('disconnect')
def on_disconnect():
    global session_users
    session_id = request.sid
    if session_id in session_users:
        user_id = session_users[session_id]
        print('User', user_id, 'disconnected...')
        del user_sessions[user_id]
        del session_users[session_id]
        print(user_id, 'has disconnected!')

@server.event
def request_api_templates(data) -> None:
    sid = request.sid
    send_message('api_templates', get_api_templates(), sid)

@server.event
def request_api(data) -> None:
    session_id = request.sid
    send_message('api_files', {'files': get_api()}, session_id)

@server.event
def request_script(data) -> None:
    session_id = request.sid
    type = data['type']
    name = data['name']
    if type == 'names':
        send_message('script_names', get_script_names(), session_id)
    elif type == 'full':
        send_message('full_script', get_script(name), session_id)

def send_message(event: str, data: any, sid: any) -> None:
    try:
        server.emit(event, data, to=sid)
    except Exception as e:
        print(f'Error Send Message ({event}):', e)

# END OF SERVER

# START OF DISCORD AUTH

@app.route('/')
def root():
    auth_key = request.args.get('auth_key')
    print('Auth Key:', auth_key)
    if auth_key == '12345':
        return redirect(f'https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPE}')
    else:
        return jsonify({'Error': 'verifying file integrity!'})

@app.route('/version/<string:script_name>', methods=['GET'])
def handle_script_version(script_name: str) -> any:
    result = get_script_version(script_name)
    return jsonify({'version': result})

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

# END OF DISCORD AUTH

if __name__ == '__main__':
    server.run(app, debug=True, host='0.0.0.0', port=5000)
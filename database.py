from gridfs import GridFS
from base64 import b64encode
from pymongo import MongoClient
from datetime import datetime, timedelta
from constants import VALID, INVALID, EXPIRED, MONGO_URI, DELIMITER


mongo_client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
database = mongo_client.psychobot
users = database.users
scripts = database.scripts
source = database.source
script_templates = database.script_templates
api = database.api
api_templates = database.api_templates
fs = GridFS(database)

def get_api_files() -> list:
    files = []
    documents = api.find({})
    for entry in documents:
        files.append({'filename': entry['filename'], 'content': entry['content']})
    return files

def get_script_names() -> list:
    result = scripts.find({})
    return [script['name'] for script in result]

def get_script_version(name: str) -> float:
    print('Name:', name)
    query = {'name': name}
    result = scripts.find_one(query)
    print(result['version'])
    return float(result['version'])

def get_api_templates() -> dict:
    all_api_templates = {}
    result = api_templates.find({})
    for doc in result:
        file_name = doc['filename']
        file_data = doc['data']
        all_api_templates[file_name] = file_data
    return all_api_templates


def get_script(name: str) -> dict:
    query = {'name': name}
    result = scripts.find_one(query)
    name = result['name']
    class_ = result['class']
    version = result['version']
    file_name = result['file_name']
    result = source.find_one({'file_name': file_name})
    source_data = result['data']
    result = script_templates.find_one({'file_name': file_name})
    templates_data = result['data']
    model = fs.find_one({'file_name': file_name})
    model_data = model.read()
    model_data = b64encode(model_data).decode('utf-8')
    data = f'{source_data}{DELIMITER}{model_data}{DELIMITER}{templates_data}'
    return {
        'version': float(version),
        'name': name,
        'class': class_,
        'file_name': file_name,
        'data': data
    }
    
def get_user_data(discord_id: int) -> dict:
    query = {'user_id': discord_id}
    result = users.find_one(query)
    if not result:
        return {
            'status': INVALID,
            'expiry_date': datetime.now(),
            'instances:': 0
        }
    
    try:
        expiry_date = datetime.strptime(result['expiry_date'], "%Y-%m-%d %H:%M:%S")
    except KeyError:
        expiry_date = datetime.now()

    status = VALID if datetime.now() < expiry_date else EXPIRED
    instances = int(result.get('instances', 0))
    return {
        'status': status,
        'expiry_date': expiry_date.strftime("%Y-%m-%d %H:%M:%S"),
        'instances': instances
    }

# def get_user_data(user_id: int) -> dict:
#     query = {'user_id': user_id}
#     result = users.find_one(query)
#     if result:
#         expiry_date = datetime.strptime(result['expiry_date'], "%Y-%m-%d %H:%M:%S") if result else datetime.now()
#         status = (VALID if datetime.now() < expiry_date else EXPIRED) if result else INVALID
#         instances = int(result['instances']) if result else 0
#         return {
#             'status': status,
#             'expiry_date': expiry_date.strftime("%Y-%m-%d %H:%M:%S"),
#             'instances': instances
#         }
#     return None

def create_new_user(user_id: int, days_until_expiry: int, instances: int) -> bool:
    expiry_time = datetime.now() + timedelta(days=days_until_expiry)
    query = {
        'user_id': int(user_id),
        'instances': int(instances),
        'expiry_date': expiry_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    return users.insert_one(query).inserted_id is not None
import pymongo
from pymongo import MongoClient
from datetime import datetime, timedelta
from constants import VALID, INVALID, EXPIRED, MONGO_URI


mongo_client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
database = mongo_client.psychobot
user_collection = database.users
script_collection = database.script_files
version_collection = database.script_versions

def get_script_names() -> list:
    result = version_collection.find({})
    return [script['name'] for script in result]

def get_script(script_name: str, files=False) -> dict:
    data = {}
    query = {'name': script_name}
    result = version_collection.find_one(query)
    data['name'] = script_name
    data['version'] = float(result['version'])
    if files:
        script_id = result['script']
        query = {'_id': script_id}
        result = script_collection.find_one(query)
        data['class'] = result['class']
        data['module'] = result['module']
        data['source'] = result['files']['source']
        data['model'] = result['files']['model']
        data['templates'] = result['files']['templates']
    return data

def get_user_data(user_id: int) -> dict:
    query = {'user_id': user_id}
    result = user_collection.find_one(query)
    expiry_date = datetime.strptime(result['expiry_date'], "%Y-%m-%d %H:%M:%S") if result else datetime.now()
    status = (VALID if datetime.now() < expiry_date else EXPIRED) if result else INVALID
    instances = int(result['instances']) if result else 0
    return {
        'status': status,
        'expiry_date': expiry_date.strftime("%Y-%m-%d %H:%M:%S"),
        'instances': instances
    }

def create_new_user(user_id: int, days_until_expiry: int, instances: int) -> bool:
    expiry_time = datetime.now() + timedelta(days=days_until_expiry)
    query = {
        'user_id': int(user_id),
        'instances': int(instances),
        'expiry_date': expiry_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    return user_collection.insert_one(query).inserted_id is not None
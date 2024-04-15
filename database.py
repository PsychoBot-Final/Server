import pymongo
from pymongo import MongoClient
from datetime import datetime, timedelta
from constants import VALID, INVALID, EXPIRED, MONGO_URI

print('MONGO URI:', MONGO_URI)
print()

mongo_client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
database = mongo_client.psychobot
user_collection = database.users
script_collection = database.scripts

def get_user_data(user_id: int) -> dict:
    query = {'user_id': user_id}
    result = user_collection.find_one(query)
    if result:
        expiry_date = datetime.strptime(result['expiry_date'], "%Y-%m-%d %H:%M:%S")
        status = VALID if datetime.now() < expiry_date else EXPIRED
    else:
        status = INVALID
        expiry_date = datetime.now()
        result = {'instances': 0, 'running_instances': 0, 'expiry_date': expiry_date}
    return {
        'status': status,
        'expiry_date': expiry_date.strftime("%Y-%m-%d %H:%M:%S"),
        'instances': int(result.get('instances', 0)),
        'running_instances': int(result.get('running_instances', 0))
    }

def create_new_user(user_id: int, days_until_expiry: int, instances: int) -> bool:
    expiry_time = datetime.now() + timedelta(days=days_until_expiry)
    query = {
        'user_id': int(user_id),
        'instances': int(instances),
        'expiry_date': expiry_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    return user_collection.insert_one(query).inserted_id is not None

def get_all_script_names() -> list:
    return [script['script_name'] for script in script_collection.find({})]
    
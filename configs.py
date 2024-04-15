import json


def get_bot_version() -> float:
    with open('./configs.json', 'r') as file:
        return float(json.load(file)['BOT-VERSION'])
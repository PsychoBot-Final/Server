import base64


def encode_base64(file_path: str) -> None:
    with open(file_path, 'rb') as file:
        return base64.b64decode(file.read()).decode('utf-8')

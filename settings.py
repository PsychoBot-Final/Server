from constants import (
    REDIRECT_URI_PUBLIC, 
    REDIRECT_URI_LOCAL,
    CLIENT_ID,
    SCOPE
)


LOCAL = True
REDIRECT_URI = REDIRECT_URI_LOCAL if LOCAL else REDIRECT_URI_PUBLIC
AUTH_URL = f'https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPE}'
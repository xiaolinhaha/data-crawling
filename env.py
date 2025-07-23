import os

DEBUG_MODEL = os.getenv('DEBUG_MODEL', False)
APP_HOST = os.getenv('APP_HOST', '0.0.0.0')
APP_PORT = os.getenv('APP_PORT', 35001)

bind_search_key = os.getenv(
    'BIND_SEARCH_KEY',
    default='6d7c9a1d013746a5b71170b5cdc76efc'
)
bind_search_headers = {"Ocp-Apim-Subscription-Key": bind_search_key}

LMJJ_BASE_URL = os.getenv('LMJJ_BASE_URL_FOR_WORKFLOW_FUNCTION', '')


def get_lmjj_base_url():
    if LMJJ_BASE_URL:
        return LMJJ_BASE_URL if LMJJ_BASE_URL.endswith('/') else LMJJ_BASE_URL + '/'
    return None

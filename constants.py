# constants.py

# COROS API Endpoints
COROS_API_URL = "https://teamapi.coros.com"
COROS_LOGIN_URL = f"{COROS_API_URL}/account/login"
COROS_ACTIVITY_QUERY_URL = f"{COROS_API_URL}/activity/query"
COROS_DOWNLOAD_URL = f"{COROS_API_URL}/activity/detail/download"
COROS_UPLOAD_URL = f"{COROS_API_URL}/activity/import"

# COROS API Status Codes
COROS_SUCCESS_CODE = "0000"
COROS_SESSION_EXPIRED_CODE = "1000" # 예시, 실제 코드에 따라 조정 필요

# Directories
DEFAULT_OUTPUT_DIR = "./exports"
COROS_DIR_NAME = "coros"
GARMIN_DIR_NAME = "garmin"

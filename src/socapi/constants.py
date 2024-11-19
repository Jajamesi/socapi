
PANEL_URL =  "https://admin.online-sociology.ru/api/"
LOGIN_URL = "api/login"
EXPORT_URL = "api/poll/stat/export"
PROGRESS_URL = f"{EXPORT_URL}/progress"
DOWNLOAD_URL = f"{PROGRESS_URL}/download"
DONE_URL = f"{PROGRESS_URL}/done"

QUOTA_LIST_URL = "api/counter/list"
POLL_GET_URL = "api/poll/get"

RETRIES_NUM = 3
VALID_REQUEST_METHODS = ("post", "get")
SUCCESS_STATUS = 200
MAX_CONCURRENT_REQUESTS = 5

EXPORT_FORMATS = {
    "xlsx": 1,
    "sav":  2,
}
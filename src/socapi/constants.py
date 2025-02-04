
PANEL_URL =  "https://admin.online-sociology.ru/api/"

# ENDPOINTS
LOGIN_ENDPOINT = "api/login"
EXPORT_START_ENDPOINT = "api/poll/stat/export"
EXPORT_PROGRESS_ENDPOINT = f"{EXPORT_START_ENDPOINT}/progress"
DOWNLOAD_START_ENDPOINT = f"{EXPORT_PROGRESS_ENDPOINT}/download"
DOWNLOAD_DONE_ENDPOINT = f"{EXPORT_PROGRESS_ENDPOINT}/done"
QUOTA_LIST_ENDPOINT = "api/counter/list"
POLL_GET_ENDPOINT = "api/poll/get"
SEARCH_LIST_ENDPOINT = "api/poll/list"
STATISTIC_ENDPOINT = "api/poll/stat"
CONVERSION_ENDPOINT = f"api/poll/stat/conversion"

SEARCH_RETURNS = ['name', 'created_at']

RETRIES_NUM = 3
VALID_REQUEST_METHODS = ("post", "get")
SUCCESS_STATUS = 200
MAX_CONCURRENT_REQUESTS = 5

EXPORT_FORMATS = {
    "xlsx": 1,
    "sav":  2,
}
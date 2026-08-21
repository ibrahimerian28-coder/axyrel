"""Legacy Streamlit configuration compatibility facade.

The legacy UI still imports these names. New backend code should use
``backend.core.config.settings`` for runtime configuration.
"""
from backend.core.config import settings

APP_SCRIPT_URL = ""
COMPANY_PHONE = "01286609535"
LOGO_PATH = "assets/images/logo.png"

SHEETS = {
    "Customers": "0",
    "Maintenance": "2120582392",
    "Inventory": "1767710106",
    "Expenses": "288947510",
    "Store_Products": "1129472026",
    "Inventory_History": "26597140",
}

# Runtime backend configuration is available through `settings`.
APP_NAME = settings.app_name
APP_VERSION = settings.app_version
ENVIRONMENT = settings.environment
API_PREFIX = settings.api_prefix

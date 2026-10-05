"""Owner-approved Asset location and calendar-year warranty rules."""
from datetime import date
from urllib.parse import urlsplit
import pycountry
from dateutil.relativedelta import relativedelta

class AssetDetailError(ValueError):
    def __init__(self, field, message):
        self.field = field
        super().__init__(message)

def prepare_asset_details(data, asset=None):
    data = dict(data)
    if asset is None and not data.get("country"): data["country"] = "EG"
    country = data.get("country", getattr(asset, "country", None))
    if "country" in data and country and not pycountry.countries.get(alpha_2=country):
        raise AssetDetailError("country", "Select a valid ISO country.")
    state = data.get("state", getattr(asset, "state", None))
    if state and ("state" in data or "country" in data):
        subdivision = pycountry.subdivisions.get(code=state)
        if not subdivision or subdivision.country_code != country:
            raise AssetDetailError("state", "Select a state/governorate belonging to the selected country.")
    if data.get("location_url"):
        url = urlsplit(data["location_url"])
        if url.scheme not in {"https", "http"} or not url.netloc or url.username or url.password:
            raise AssetDetailError("location_url", "Location URL must be an HTTP(S) location link.")
    years = data.get("warranty_years", getattr(asset, "warranty_years", None))
    if "warranty_years" in data or years is not None:
        installed = data.get("installation_date", getattr(asset, "installation_date", None))
        if isinstance(installed, str): installed = date.fromisoformat(installed)
        if installed and years is not None and installed.year + years > 9999:
            raise AssetDetailError("warranty_years", "Warranty end date exceeds the supported calendar range.")
        data["warranty_end"] = installed + relativedelta(years=years) if installed and years is not None else None
    return data

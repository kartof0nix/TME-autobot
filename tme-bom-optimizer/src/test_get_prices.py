import hashlib
import hmac
import base64
import requests
import json
from urllib.parse import urlencode, quote

API_TOKEN = "d56bf3870f2226b56e7e9dd7dc4f35879ce76fa27b0d403247"
API_SECRET = "e7b81226557fb52f4ee0"

def tme_api_post(endpoint, params, token, secret):
    base_url = "https://api.tme.eu"
    url = f"{base_url}{endpoint}"

    # Add required authentication fields
    params["Token"] = token

    # Prepare signature base string
    method = "POST"
    base_string_uri = quote(url, safe='')
    sorted_params = sorted(params.items())
    encoded_params = urlencode(sorted_params)
    signature_base = f"{method}&{base_string_uri}&{quote(encoded_params, safe='')}"
    signature = hmac.new(
        secret.encode("utf-8"),
        signature_base.encode("utf-8"),
        hashlib.sha1
    ).digest()
    signature_b64 = base64.b64encode(signature).decode("utf-8")
    params["ApiSignature"] = signature_b64

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=params, headers=headers)
    print("Status code:", response.status_code)
    print("Response:", response.text)
    response.raise_for_status()
    return response.text


if __name__ == "__main__":
    params = {
        'SymbolList[0]' : 'NE555D',
        'SymbolList[1]' : '1N4007-DC',
        'Country': 'PL',
        'Currency': 'PLN',
        'Language': 'PL',
    }
    response = tme_api_post("/Products/GetPrices.json", params, API_TOKEN, API_SECRET)
    response = json.loads(response)
    print(response)
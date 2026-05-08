import os
import collections, urllib, base64, hmac, hashlib, json

import openai
import requests
import re
import base64
import hmac
import hashlib
from urllib.parse import urlencode, quote
from .get_value import get_value, ref_to_elem

SI_PREFIXES = [
    ("f", 1e-15),
    ("p", 1e-12),
    ("n", 1e-9),
    ("u", 1e-6),
    ("m", 1e-3),
    ("", 1),
    ("k", 1e3),
    ("M", 1e6),
    ("G", 1e9),
]
prefix_to_index = {p: i for i, (p, _) in enumerate(SI_PREFIXES)}

def scale_up(value_str, steps=1):
    value_str = value_str.strip().replace(",", ".")
    match = re.fullmatch(r"([0-9]*\.?[0-9]+)([fpnumkMG]?)([a-zA-ZΩ]*)", value_str)
    if not match:
        raise ValueError(f"Invalid format: {value_str}")
    value, prefix, unit = match.groups()
    value = float(value)
    if prefix not in prefix_to_index:
        raise ValueError(f"Unknown prefix: {prefix}")
    idx = prefix_to_index[prefix]
    new_idx = idx + steps
    if new_idx >= len(SI_PREFIXES):
        raise ValueError("Cannot scale beyond largest prefix")
    base_value = value * SI_PREFIXES[idx][1]
    new_prefix, new_factor = SI_PREFIXES[new_idx]
    new_value = base_value / new_factor
    return f"{new_value:g}{new_prefix}{unit}"

def normalize_search_plain(elem, obudowa, wartosc, tolerance, operating_voltage):
    parts = []
    if elem:
        parts.append(str(elem))
    if wartosc:
        v = wartosc.strip().upper()
        match = re.match(r"^(\d+)\s*NF$", v)
        if match:
            v = f"{int(match.group(1))}nF"
        match = re.match(r"^([\d\.]+)\s*UF$", v)
        if match:
            v = f"{match.group(1)}uF"
        match = re.match(r"^(\d+)\s*PF$", v)
        if match:
            v = f"{int(match.group(1))}pF"
        parts.append(v)
    if obudowa:
        parts.append(str(obudowa))
    if operating_voltage and operating_voltage not in ["", None, "0", float('inf')] and str(operating_voltage).strip() not in ["0V", "0.0V", "nan"]:
        parts.append(f"{operating_voltage}")
    if tolerance and tolerance not in ["", None, "0", float('inf')] and str(tolerance).strip() not in ["0%", "0.0%", "nan"]:
        parts.append(str(tolerance))
    return " ".join(parts)

def inch_to_mm(case_inch):
    case_inch = str(case_inch).strip()
    cases = {
        "1005": "0402", "0201": "0603", "0402": "1005", "0603": "1608", "0805": "2012",
        "1008": "2520", "1206": "3216", "1210": "3225", "1411": "3528", "1812": "4532",
        "2010": "5025", "2012": "5032", "2312": "6032", "2512": "6332"
    }
    return cases.get(case_inch.zfill(4), case_inch)

def mm_to_inch(case_mm):
    case_mm = str(case_mm).strip()
    cases = {
        "0402": "1005", "0603": "0201", "1005": "0402", "1608": "0603", "2012": "0805",
        "2520": "1008", "3216": "1206", "3225": "1210", "3528": "1411", "5025": "2010",
        "5032": "2012", "6032": "2312", "6332": "2512",
        "4532": "1812"
    }
    return cases.get(case_mm.zfill(4), case_mm)

class TMEClient:
    BASE_URL = "https://api.tme.eu"
    COUNTRY = "PL"
    LANGUAGE = "EN"

    def __init__(self, token, secret):
        self.token = token
        self.secret = secret

    def _post(self, endpoint, data):
        url = f"{self.BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data["Token"] = self.token
        if "Country" not in data:
            data["Country"] = self.COUNTRY
        if "Language" not in data:
            data["Language"] = self.LANGUAGE
        method = "POST"
        base_string_uri = quote(url, safe='')
        params_for_sig = {k: v for k, v in data.items() if k != "ApiSignature"}
        sorted_params = sorted(params_for_sig.items())
        encoded_params = "&".join(f"{quote(str(k), safe='')}={quote(str(v), safe='')}" for k, v in sorted_params)
        signature_base = f"{method}&{base_string_uri}&{quote(encoded_params, safe='')}"
        signature = hmac.new(
            self.secret.encode("utf-8"),
            signature_base.encode("utf-8"),
            hashlib.sha1
        ).digest()
        signature_b64 = base64.b64encode(signature).decode("utf-8")
        data["ApiSignature"] = signature_b64
        encoded_data = "&".join(f"{quote(str(k), safe='')}={quote(str(v), safe='')}" for k, v in data.items())
        response = requests.post(url, data=encoded_data, headers=headers)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print("TME API error:", response.text)
            raise
        return response.json()

class TMEApi:
    def __init__(self, token, secret, gpt_api_key=None):
        self.client = TMEClient(token, secret)
        self.api_key = gpt_api_key or os.getenv("OPENAI_API_KEY")

    def fetch_elements(self, ref : str, obudowa : str, operating_voltage : float, wartosc : str, tolerance : str, max_qty = 1):
        elem = ref_to_elem(ref)
        search_plain = normalize_search_plain(elem, mm_to_inch(obudowa), wartosc, tolerance, "")
        data = {
            "SearchPlain": search_plain,
            "SearchWithStock": "true",
            "SearchOrder": "PRICE_FIRST_QUANTITY",
            "SearchOrderType": "ASC",
            "SearchPage": 1
        }
        response = self.client._post("/Products/Search.json", data)
        products = []
        saved_prices = {}
        cnt = 0
        raw_products = []

        if "Data" in response and "ProductList" in response["Data"]:
            for product in response["Data"].get("ProductList", []):
                cnt += 1
                # Check if the product matches the search criteria more strictly (since SearchPlain is broad)
                print(f"Checking product: {product.get('Description', '')}", end="\r")  # Debug print
                # print("Checking " + str(product.get("Description", "")).lower() + " against " + str(obudowa).lower() + " and " + str(mm_to_inch(obudowa)).lower() + " and " + str(inch_to_mm(obudowa)).lower())  # Debug print
                a = product.get("Description", "").lower().replace('-', '')
                if not(str(obudowa).lower().replace('-', '') in a or str(mm_to_inch(obudowa)).lower() in a or str(inch_to_mm(obudowa)).lower() in a):
                    # Ask user to confirm if product matches obudowa criteria, if not, skip it
                    print("CASE_ERR")
                    continue
                voltage_match = re.search(r"(\d+\.?\d*)\s*V", product.get("Description", ""), re.IGNORECASE)
                voltage_value = float(voltage_match.group(1)) if voltage_match else None
                if operating_voltage and voltage_value is not None and voltage_value < float(operating_voltage):
                    print("MAXV_ERR")
                    continue
                if(elem == "resistor" or elem == "capacitor"):
                    if(get_value(product.get("Description", "")) - get_value(wartosc)) > 1e-12:
                        print("VAL_ERR ")
                        continue
                raw_products.append(product)
        print(f"Found {cnt} products for search: '{search_plain}'    ")  # Debug print
        return self.parse_price_list(raw_products, max_qty)
    
    def fetch_gpt(self, row: str, max_qty = 1):
        query = self.generate_query_gpt(row)
        data = {
            "SearchPlain": query,
            "SearchWithStock": "true",
            "SearchOrder": "PRICE_FIRST_QUANTITY",
            "SearchOrderType": "ASC",
            "SearchPage": 1
        }
        response = self.client._post("/Products/Search.json", data)
        raw_products = []
        if "Data" in response and "ProductList" in response["Data"]:
            for product in response["Data"].get("ProductList", []):
                raw_products.append(product)
        print(f"GPT Search found {len(raw_products)} products for query: '{query}'    ")  # Debug print
        # print(raw_products)
        return self.parse_price_list(raw_products, max_qty)
    
    def parse_price_list(self, raw_products, max_qty = 1):
        saved_prices = {}
        products = []
        for product in raw_products:
            # Find price for quantity 1 (if available)
            cena_1_sztuka = None
            price_list = product.get("PriceList", [])
            for price in price_list:
                if price.get("Amount") == 1:
                    cena_1_sztuka = price.get("PriceValue")
                    break
            # Fallback: use first price if qty=1 not found
            if cena_1_sztuka is None and saved_prices.get(product.get("Symbol")) is not None:
                cena_1_sztuka = saved_prices.get(product.get("Symbol"))
            if cena_1_sztuka is None:
                params = {
                    'SymbolList[0]' : product.get("Symbol"),
                    'Country': 'PL',
                    'Currency': 'PLN',
                    'Language': 'PL',
                }
                response = self.client._post("/Products/GetPrices.json", params)
                if "Data" in response and "ProductList" in response["Data"] and "PriceList" in response["Data"]["ProductList"][0]:
                    price_list = response["Data"]["ProductList"][0].get("PriceList", [])
                    if price_list:
                        cena_1_sztuka = price_list[0].get("PriceValue") * price_list[0].get("Amount") / min(max_qty, price_list[0].get("Amount"))
                        saved_prices[product.get("Symbol")] = cena_1_sztuka
                else:
                    print(f"Failed to get price for {product.get('Symbol')}: {response}")
            products.append({
                "Symbol": product.get("Symbol"),
                "Description": product.get("Description"),
                "Cena 1 Sztuka": cena_1_sztuka,
                "Link": f"https://www.tme.eu/pl/details/{product.get('Symbol', '').lower()}/"
            })
        print(f"Fetched {len(products)} / {len(raw_products)} products for search")  # Debug print
        return products
        

    def generate_query_gpt(self, row: str) -> str:
        """
        Uses OpenAI GPT-4o to generate a TME search query for a BOM row.
        """
        # EXAMPLES for context
        examples = [
            {
                "row": "C1;100nF;0805;2;0805;50;100nF;10%;Ceramic capacitor; ; ;",
                "query": "capacitor 100nF 0805"
            },
            {
                "row": "R2;10k;0603;1;0603;50;10k;1%;Resistor; ; ;",
                "query": "resistor 10k 0603"
            },
            {
                "row": "D1;1N4148;SOD-123;1;SOD-123;;1N4148;;Diode; ; ;",
                "query": "diode 1N4148 SOD123"
            },
            {
                "row": "C2;1uF;1206;2;1206;16;1uF;10%;Ceramic capacitor; ; ;",
                "query": "ceramic capacitor 1uF 1206"
            }
        ]

        # Compose the prompt
        prompt = (
            "You are an assistant that converts BOM CSV rows into TME search queries. "
            "Given a row, output a concise TME search string for the element. "
            "It should be no longer than 40 characters and include key attributes like type, value, and package. "
            "Here are some examples:\n"
        )
        for ex in examples:
            prompt += f"Row: {ex['row']}\nTME Query: {ex['query']}\n"
        prompt += f"\nRow: {row}\nTME Query:"

        # Call OpenAI API (make sure OPENAI_API_KEY is set in your environment)
        client = openai.OpenAI(api_key=self.api_key)  # Uses OPENAI_API_KEY from environment
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for electronics BOM processing."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=32,
            temperature=0.1,
        )
        query = response.choices[0].message.content.strip()
        print(f"GPT generated query: '{query}' for row: '{row}'")  # Debug print
        return query
    # You can use this autocomplete in your fetch_elements or as a separate step


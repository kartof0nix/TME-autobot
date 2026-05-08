import re

_MULTIPLIERS = {
    "": 1.0,
    "R": 1.0,
    "k": 1e3,
    "M": 1e6,
    "G": 1e9,
    "m": 1e-3,
    "u": 1e-6,
    "n": 1e-9,
    "p": 1e-12,
}

def _parse_value(token: str):
    token = token.replace("Ω", "R")

    # 1) embedded notation: 4k7, 1M2, 2R2
    m = re.fullmatch(r"(\d+)([RkMGmunp])(\d+)", token)
    if m:
        a, prefix, b = m.groups()
        return float(f"{a}.{b}") * _MULTIPLIERS[prefix]

    # 2) normal notation: 10k, 100R, 1k
    m = re.fullmatch(r"(\d*\.?\d+)([RkMGmunp])", token)
    if m:
        value, prefix = m.groups()
        return float(value) * _MULTIPLIERS[prefix]

    # 3) resistor/capacitor with suffix (100nF, 10uF)
    m = re.fullmatch(r"(\d*\.?\d+)([RkMGmunp]?)([A-Za-z]+)", token)
    if m:
        value, prefix, _ = m.groups()
        if prefix == "":
            return None
        return float(value) * _MULTIPLIERS[prefix]

    return None


def get_value(s: str):
    for token in re.split(r"[;\s:]+", s):
        val = _parse_value(token)
        if val is not None:
            return val
    raise ValueError("No valid value found")

def ref_to_elem(ref : str):
    if(ref[0].lower() == 'c'):
        return "capacitor"
    if(ref[0].lower() == 'r'):
        return "resistor"
    if(ref[0].lower() == 'd'):
        return "diode"
    if(ref[0].lower() == 'q'):
        return "transistor"
    if(ref[0].lower() == 'y'):
        return "crystal"
    return ""
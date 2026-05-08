import re

# Ordered SI prefixes (electronics-focused)
SI_PREFIXES = [
    ("f", 1e-15),
    ("p", 1e-12),
    ("n", 1e-9),
    ("u", 1e-6),   # micro (u instead of µ)
    ("m", 1e-3),
    ("", 1),
    ("k", 1e3),
    ("M", 1e6),
    ("G", 1e9),
]

prefix_to_index = {p: i for i, (p, _) in enumerate(SI_PREFIXES)}


def scale_up(value_str, steps=1):
    """
    Convert SI string 'up' by given number of prefix steps.
    
    Examples:
        scale_up("100pF") -> "0.1nF"
        scale_up("10nF")  -> "0.01uF"
        scale_up("100R")  -> "0.1kR"
    """
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

    # Convert to base value (no prefix)
    base_value = value * SI_PREFIXES[idx][1]

    # Convert to new prefix
    new_prefix, new_factor = SI_PREFIXES[new_idx]
    new_value = base_value / new_factor

    return f"{new_value:g}{new_prefix}{unit}"
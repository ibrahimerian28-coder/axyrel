def clean_phone(phone):
    if phone is None: return ""
    value = str(phone).strip()
    return "" if value.lower() in {"nan", "none"} else value

def wa_link(phone):
    value = clean_phone(phone).replace(" ", "")
    if value.startswith("0"): value = "2" + value
    return f"https://wa.me/{value}"

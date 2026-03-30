import re

#fix api so that its in the same structure 10-digit format
def normalize_api(api: str):

    if not api:
        return None

    # Remove everything except digits
    digits = re.sub(r'[^0-9]', '', api)

    # Must have at least 10 digits
    if len(digits) < 10:
        return None

    # Use first 10 digits only
    digits = digits[:10]

    return f"{digits[:2]}-{digits[2:5]}-{digits[5:10]}"
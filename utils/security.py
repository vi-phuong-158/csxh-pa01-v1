def sanitize_for_excel(value):
    """
    Sanitizes a value to prevent Excel Formula Injection (CSV Injection).
    If the value starts with =, +, -, or @, it prepends a single quote.
    """
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value

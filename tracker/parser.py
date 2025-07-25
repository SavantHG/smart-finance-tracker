import re

def parse_expense_input(input_text):
    """
    Expected format: "500 grocery dal, masale"
    Returns a dict or None
    """
    try:
        match = re.match(r'^(\d+)\s+(.+?)\s+(.+)$', input_text.strip())
        if not match:
            return None

        return {
            "amount": float(match.group(1)),
            "category": match.group(2),
            "description": match.group(3)
        }
    except Exception:
        return None
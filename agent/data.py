from datetime import date, timedelta


def _days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


# Dates are relative to today so the eval scenarios stay valid whenever they run.
# users_data[username][item_name] = {"price": int, "purchase_date": "YYYY-MM-DD"}
users_data = {
    "alice": {
        "Wireless Mouse": {"price": 25, "purchase_date": _days_ago(5)},
        "Mechanical Keyboard": {"price": 120, "purchase_date": _days_ago(10)},
    },
    "bob": {
        "Laptop Stand": {"price": 40, "purchase_date": _days_ago(30)},  # last valid day
        "USB-C Hub": {"price": 60, "purchase_date": _days_ago(31)},  # just expired
    },
    "carol": {
        "Monitor": {"price": 300, "purchase_date": _days_ago(-3)},  # future date: invalid
    },
}

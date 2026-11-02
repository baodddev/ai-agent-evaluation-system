from langchain.tools import tool
from data import users_data
import logging
from objects import PurchaseItem
from datetime import date
from uuid import uuid4

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s "
)

REFUND_WINDOW_DAYS = 30
# shortcut: in-memory, resets on restart; move to a DB once tickets are real
refunded_items: set[tuple[str, str]] = set()


def check_items(user: str, items: list[PurchaseItem]) -> tuple[int, list[str], list[str]]:
    """Apply the refund rules in code. Returns (total, eligible item names, per-item report lines)."""
    purchases = users_data[user]
    today = date.today()
    total, eligible, report = 0, [], []
    for name in dict.fromkeys(item.name for item in items):  # dedupe repeated names
        purchase = purchases.get(name)
        if purchase is None:
            report.append(f"{name}: REJECTED - not in the customer's purchase history")
            continue
        if (user, name) in refunded_items:
            report.append(f"{name}: REJECTED - already refunded")
            continue
        age = (today - date.fromisoformat(purchase["purchase_date"])).days
        if age < 0:
            report.append(f"{name}: REJECTED - purchase date {purchase['purchase_date']} is in the future (invalid)")
        elif age > REFUND_WINDOW_DAYS:
            report.append(f"{name}: REJECTED - purchased {age} days ago, limit is {REFUND_WINDOW_DAYS} days")
        else:
            total += purchase["price"]
            eligible.append(name)
            report.append(f"{name}: ELIGIBLE - {purchase['price']} (purchased {age} days ago)")
    return total, eligible, report


@tool
def get_user_purchase_history(user: str) -> dict:
    """Takes the customer's username and returns their purchase history:
    {item_name: {"price": ..., "purchase_date": "YYYY-MM-DD"}}."""
    logging.info(f"using get_user_purchase_history tool on user: {user}")
    if user in users_data:
        return users_data[user]
    return {"status": "there was no username found"}


@tool
def calculate_right_refund(user: str, items: list[PurchaseItem]) -> str:
    """Takes the username and the items the customer wants to return.
    Checks each item against the refund rules and returns per-item eligibility and the refund total.
    Use the exact item names from the purchase history."""
    logging.info(f"using calculate_right_refund tool to get user's: {user} refund")
    if user not in users_data:
        return "there was no username found"
    total, _, report = check_items(user, items)
    return "\n".join(report + [f"total refund: {total}"])


@tool
def issue_refund_ticket(user: str, items: list[PurchaseItem]) -> str:
    """Issues a refund ticket for the given items. The amount is recalculated here and only
    eligible items are refunded. Call this only after calculate_right_refund."""
    logging.info(f"using issue_refund_ticket for user: {user}")
    if user not in users_data:
        return "there was no username found, no ticket issued"
    total, eligible, report = check_items(user, items)
    if not eligible:
        return "no eligible items, no ticket issued:\n" + "\n".join(report)
    refunded_items.update((user, name) for name in eligible)
    ticket_id = uuid4().hex[:8]
    return (f"refund ticket {ticket_id} issued successfully for {total} "
            f"covering: {', '.join(eligible)}")


@tool
def get_today_date() -> str:
    """Return today's date in YYYY-MM-DD format.
    This tool takes no arguments.
    Only use it if the user exists and an item is present for refund."""
    logging.info("using the date tool")
    return date.today().isoformat()

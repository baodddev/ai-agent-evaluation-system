from tools import calculate_right_refund, issue_refund_ticket, refunded_items

def items(*names):
    return [{"name": n} for n in names]

def calc(user, *names):
    return calculate_right_refund.invoke({"user": user, "items": items(*names)})

def issue(user, *names):
    return issue_refund_ticket.invoke({"user": user, "items": items(*names)})

refunded_items.clear()
assert "total refund: 25" in calc("alice", "Wireless Mouse")
assert "total refund: 145" in calc("alice", "Wireless Mouse", "Mechanical Keyboard")
assert "total refund: 25" in calc("alice", "Wireless Mouse", "Wireless Mouse")  # no double count
assert "not in the customer's purchase history" in calc("alice", "Monitor")
assert "total refund: 40" in calc("bob", "Laptop Stand", "USB-C Hub")  # day 30 ok, day 31 not
assert "31 days ago" in calc("bob", "USB-C Hub")
assert "in the future" in calc("carol", "Monitor")
assert "no username" in calc("mallory", "Monitor")
assert "no ticket issued" in issue("carol", "Monitor")
assert "issued successfully for 25" in issue("alice", "Wireless Mouse")
assert "already refunded" in calc("alice", "Wireless Mouse")
assert "no ticket issued" in issue("alice", "Wireless Mouse")  # no double refund
print("all tool checks passed")

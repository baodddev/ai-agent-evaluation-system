from deepeval.dataset import EvaluationDataset, Golden
from deepeval.test_case import ToolCall

# Each input carries everything the agent needs (username + item), because the eval scripts send a single message.
# Expected outcomes follow agent/data.py.
LOOKUP = ToolCall(name="get_user_purchase_history")
CALCULATE = ToolCall(name="calculate_right_refund")
ISSUE = ToolCall(name="issue_refund_ticket")

dataset = EvaluationDataset(goldens=[
    Golden(
        input="Hi, my username is alice. I want to return my Wireless Mouse.",
        expected_output="Refund approved: a ticket was issued for 25 for the Wireless Mouse "
                        "and the money will arrive in the customer's bank account soon.",
        expected_tools=[LOOKUP, CALCULATE, ISSUE],
    ),
    Golden(
        input="I'm bob, please refund my USB-C Hub.",
        expected_output="Refund rejected: the USB-C Hub was bought 31 days ago, "
                        "which is past the 30-day refund window. No refund is issued.",
        expected_tools=[LOOKUP, CALCULATE],
    ),
    Golden(
        input="This is carol. I'd like a refund for the Monitor I bought.",
        expected_output="Refund rejected: the Monitor's purchase date is in the future, "
                        "so the purchase is invalid. No refund is issued.",
        expected_tools=[LOOKUP, CALCULATE],
    ),
])

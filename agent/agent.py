from models import model
from tools import calculate_right_refund, get_today_date
from tools import issue_refund_ticket,get_user_purchase_history,refunded_items
from dotenv import load_dotenv
from langchain.agents import create_agent
from prompts import agent_system_prompt
from objects import Answer
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage
from uuid import uuid4
from langgraph.errors import GraphRecursionError

load_dotenv()

agent = create_agent(
    model=model,
    system_prompt=agent_system_prompt,
    tools=[calculate_right_refund,get_user_purchase_history,issue_refund_ticket,get_today_date],
    response_format=Answer,
    checkpointer=InMemorySaver()
)

def run_conversation():
    config = {"configurable": {"thread_id": str(uuid4())}}

    text = "I would like to request a refund"
    print(text)
    
    question = HumanMessage(content=text)
    conversation = True

    while conversation:

        response = agent.invoke({"messages":[question]}, config=config)
        structured_response = response["structured_response"]

        print(structured_response.answer)

        conversation = structured_response.conversation

        if conversation:
            user_input = input("reply: \n")
            question = HumanMessage(content=user_input)

    print("the job is done!")

MAX_STEPS_PER_TURN = 20
STEP_LIMIT_ANSWER = "[agent hit the step limit without answering]"

def run_scripted(turns: list[str], callbacks: list | None = None) -> dict:
    """Run one eval case without input(): fresh thread, clean refund state.
    Returns the final agent state: "messages" (full trajectory incl. tool calls) and
    "structured_response". structured_response.conversation is still True if the turns
    ran out before the agent reached a decision, or if it got stuck in a loop (step limit)."""
    # shortcut: fixed turns don't adapt to the agent's questions; switch to an LLM-simulated customer if cases misalign
    assert turns, "a case needs at least one customer message"
    refunded_items.clear()  # one case's refunds must not leak into the next
    # create_agent defaults to 9999 steps, so a looping agent burns quota forever; a normal case needs ~8
    config = {"configurable": {"thread_id": str(uuid4())}, "recursion_limit": MAX_STEPS_PER_TURN,
              "callbacks": callbacks or []}  # e.g. DeepEval CallbackHandler to capture a trace
    for text in turns:
        try:
            response = agent.invoke({"messages": [HumanMessage(content=text)]}, config=config)
        except GraphRecursionError:
            response = dict(agent.get_state(config).values)  # keep the trajectory so evals can see the loop
            response["structured_response"] = Answer(answer=STEP_LIMIT_ANSWER, conversation=True)
            break
        if not response["structured_response"].conversation:
            break
    return response

if __name__ == "__main__":
    run_conversation()
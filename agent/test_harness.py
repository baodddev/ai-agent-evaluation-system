"""Checks run_scripted without calling the LLM: a stub agent calls the real refund tool."""
import os
os.environ.setdefault("GEMINI_API_KEY", "test")  # model is built at import; no request is made

import agent as agent_module
from objects import Answer
from tools import issue_refund_ticket


class StubAgent:
    def __init__(self, finish_after: int):
        self.finish_after, self.calls, self.threads = finish_after, 0, []

    def invoke(self, state, config):
        self.calls += 1
        self.threads.append(config["configurable"]["thread_id"])
        ticket = issue_refund_ticket.invoke({"user": "alice", "items": [{"name": "Wireless Mouse"}]})
        done = self.calls >= self.finish_after
        return {"messages": state["messages"], "structured_response": Answer(answer=ticket, conversation=not done)}


# same case twice: refund state must reset, so both runs issue a ticket on a fresh thread
stub = StubAgent(finish_after=1)
agent_module.agent = stub
first = agent_module.run_scripted(["I'm alice, refund my Wireless Mouse"])
stub.calls = 0
second = agent_module.run_scripted(["I'm alice, refund my Wireless Mouse"])
assert "issued successfully" in first["structured_response"].answer
assert "issued successfully" in second["structured_response"].answer, second["structured_response"].answer
assert stub.threads[0] != stub.threads[1]

# stops as soon as the agent decides, even if scripted turns remain
stub = StubAgent(finish_after=2)
agent_module.agent = stub
state = agent_module.run_scripted(["hi", "I'm alice", "extra turn never sent"])
assert stub.calls == 2 and state["structured_response"].conversation is False

# turns run out before a decision: conversation stays True so the eval can flag it
stub = StubAgent(finish_after=5)
agent_module.agent = stub
assert agent_module.run_scripted(["hi"])["structured_response"].conversation is True

# looping agent: step limit ends the case as unfinished, keeping the trajectory instead of hanging
from types import SimpleNamespace
from langgraph.errors import GraphRecursionError


class LoopingAgent:
    def invoke(self, state, config):
        assert config["recursion_limit"] == agent_module.MAX_STEPS_PER_TURN
        raise GraphRecursionError("loop")

    def get_state(self, config):
        return SimpleNamespace(values={"messages": ["trajectory so far"]})


agent_module.agent = LoopingAgent()
state = agent_module.run_scripted(["I'm bob, refund my USB-C Hub"])
assert state["structured_response"].conversation is True
assert state["structured_response"].answer == agent_module.STEP_LIMIT_ANSWER
assert state["messages"] == ["trajectory so far"]

print("all harness checks passed")

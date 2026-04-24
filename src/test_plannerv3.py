from pprint import pprint

from langchain.messages import HumanMessage

# from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI



from graphv3 import graph
from state import UserProfile

# This file is an early graph-level test for graphv3.py.
# Unlike test_plannerv2.py, this file does run the compiled LangGraph graph.
#
# Main purpose:
# - verify the create-only execution path in graphv3
# - verify planner -> route -> extract execution
# - verify that extract returns only new profiles
# - verify that the reducer merges those new profiles into top-level `existing`
#   without overwriting the profiles that were already there
#
# This file is useful when we want to debug:
# - graph wiring
# - conditional routing
# - reducer merge behavior
# - checkpointed graph state after invocation
#
# This file is NOT yet a full graph test suite.
# At this stage it does NOT cover:
# - planner/extract mismatch retry
# - human clarification path
# - update branch
# - mixed create + update path
base_existing = {
    "user_001": UserProfile(
        name="Philip de Haas",
        company="London Metals Limited",
        role="Owner",
        location="London",
    ),
    "user_002": UserProfile(
        name="Mario Fishman",
        company="Krowdy",
        role="CEO",
        location="Peru",
    ),
}


# TEST1: create only
# Purpose:
# - start from two existing profiles
# - send one message that introduces exactly one new person
# - confirm that the new person is added into `existing` under a fresh ID
# - confirm that the previous existing profiles remain intact
messages1 = [
    HumanMessage(id="hm_001", content="I met Lucia Romero, a startup lawyer from Lima."),
]


# The thread_id is important because graphv3 currently uses a checkpointer.
# Keeping this explicit makes it easier to inspect state after invocation.
config = {"configurable": {"thread_id": "1"}}
result = graph.invoke({"messages": messages1, "existing": base_existing}, config=config)

# Read the checkpointed state after the run so we can inspect the canonical
# graph state, not only the immediate return value.
state = graph.get_state(config)

# Printing the full state here helps us confirm:
# - planner output
# - merged existing profiles
# - preserved input messages
print(state.values)

# Pretty-printing returned messages is mainly for quick manual inspection during
# development. In this early test, the message stream is less important than the
# state merge, but it is still useful to see what came back from the graph.
for m in result["messages"]:
    m.pretty_print()


# Optional debugging helper:
# if uncommented later, this can be used to inspect step-by-step graph history
# in the checkpoint store.
# for snapshot in graph.get_state_history(config):
#     print("step:", snapshot.metadata.get("step"))
#     print("next:", snapshot.next)
#     print("values:", snapshot.values)
#     print()

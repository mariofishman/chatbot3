from pprint import pprint

from langchain.messages import HumanMessage
from langchain_classic.schema import BaseMessage

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
#
# Important note for the current stage:
# this file now contains several additional message fixtures for future testing,
# but the graph code is not yet expected to pass all of them. The goal for now
# is to preserve a clear set of scenarios that will be useful once mismatch
# handling, retries, and update-path logic are added to graphv3.py.
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


# TEST2: one message creates multiple new people
# Purpose:
# - test whether the planner returns one create link with new_person_count > 1
# - later, test whether extract can return multiple profiles from a single
#   human message
# - this is a direct edge case for the current total_new_person_count logic
messages2 = [
    HumanMessage(
        id="hm_002",
        content=(
            "Yesterday I met Lucia Romero, a startup lawyer from Lima, "
            "Ana Torres, a product manager from Madrid, and "
            "Diego Salazar, a software engineer from Arequipa."
        ),
    ),
]


# TEST3: two different messages each create one new person
# Purpose:
# - test whether planner can select multiple create-relevant messages at once
# - later, test whether total_new_person_count is computed as the sum across
#   multiple CreateLink objects, not just one message
messages3 = [
    HumanMessage(id="hm_003", content="I met Lucia Romero, a startup lawyer from Lima."),
    HumanMessage(id="hm_004", content="I also met Ana Torres, a product manager from Madrid."),
]


# TEST4: two different messages create multiple people in total
# Purpose:
# - stronger version of the previous case
# - test whether planner can select more than one create message, where one of
#   those messages itself contains more than one new person
# - later, this should stress total_new_person_count across both message count
#   and per-message create counts
messages4 = [
    HumanMessage(
        id="hm_005",
        content="I met Lucia Romero, a startup lawyer from Lima, and Diego Salazar, a software engineer from Arequipa.",
    ),
    HumanMessage(
        id="hm_006",
        content="I also met Ana Torres, a product manager from Madrid.",
    ),
]


# TEST5: create + irrelevant message
# Purpose:
# - verify that only the create-relevant message is selected by the planner
# - later, confirm that irrelevant chatter does not inflate total_new_person_count
#   or pollute the extract prompt
messages5 = [
    HumanMessage(id="hm_007", content="Nice weather today."),
    HumanMessage(id="hm_008", content="I met Lucia Romero, a startup lawyer from Lima."),
]


# TEST6: mixed create and update in one message
# Purpose:
# - future mixed-path scenario
# - the same message should eventually be relevant for both create and update
# - useful later to check whether the create branch still sees the correct
#   create-side count while the update branch targets an existing profile
messages6 = [
    HumanMessage(
        id="hm_009",
        content="Philip de Haas now lives in Zurich, and I also met Lucia Romero, a startup lawyer from Lima.",
    ),
]


# TEST7: multiple update-relevant messages plus one create message
# Purpose:
# - future edge case for state.plan.relevant_for_update_links having many items
# - useful later when the update branch is wired, because planner should return
#   multiple update links while still keeping exactly one create link
# - for the current stage, this is mainly a fixture to remember that planner
#   selection and create extraction must behave correctly even when there is a
#   lot of update-side material in the same state
messages7 = [
    HumanMessage(id="hm_010", content="Philip de Haas now lives in Zurich."),
    HumanMessage(id="hm_011", content="Mario Fishman is interested in tae kwon do."),
    HumanMessage(id="hm_012", content="Philip de Haas works often from Geneva now."),
    HumanMessage(id="hm_013", content="I met Lucia Romero, a startup lawyer from Lima."),
]


# TEST8: many create-relevant messages
# Purpose:
# - stress case for multiple CreateLink objects in one graph invocation
# - later, verify that total_new_person_count sums correctly over many selected
#   messages instead of only the first or last one
messages8 = [
    HumanMessage(id="hm_014", content="I met Lucia Romero, a startup lawyer from Lima."),
    HumanMessage(id="hm_015", content="I met Ana Torres, a product manager from Madrid."),
    HumanMessage(id="hm_016", content="I met Diego Salazar, a software engineer from Arequipa."),
    HumanMessage(id="hm_017", content="I met Sofia Vega, an HR consultant from Buenos Aires."),
]


# TEST9: create count mismatch candidate
# Purpose:
# - future mismatch-handling test
# - this wording may be tricky for extraction because one message references
#   multiple people in a compact way
# - later, useful to see whether the planner expects two new people while the
#   extractor returns the wrong number, which should trigger retry logic
messages9 = [
    HumanMessage(
        id="hm_018",
        content="At lunch I met the siblings Lucia Romero and Diego Romero, both startup lawyers from Lima.",
    ),
]


# TEST10: duplicate mention of the same new person across two messages
# Purpose:
# - future identity-resolution edge case
# - the current graph does not deduplicate newly extracted profiles, so this is
#   a reminder fixture for later memory/identity work
# - for now, this helps document a case where total_new_person_count may look
#   simple while canonical memory semantics are actually harder
messages10 = [
    HumanMessage(id="hm_019", content="I met Lucia Romero, a startup lawyer from Lima."),
    HumanMessage(id="hm_020", content="Lucia Romero is also very interested in fintech."),
]



def run_test(messages: list[BaseMessage], existing: dict[str, UserProfile], index: int):
    # The thread_id is important because graphv3 currently uses a checkpointer.
    # Keeping this explicit makes it easier to inspect state after invocation.
    config = {"configurable": {"thread_id": index}}
    result = graph.invoke({"messages": messages, "existing": existing}, config=config)

    # Read the checkpointed state after the run so we can inspect the canonical
    # graph state, not only the immediate return value.
    state = graph.get_state(config)

    # Printing the full state here helps us confirm:
    # - planner output
    # - merged existing profiles
    # - preserved input messages
    print("\n")
    print("EXISTING:\n")
    pprint({k: v.model_dump() for k, v in state.values["existing"].items()})
    pprint(state.values["plan"].model_dump())

    # Pretty-printing returned messages is mainly for quick manual inspection during
    # development. In this early test, the message stream is less important than the
    # state merge, but it is still useful to see what came back from the graph.
    print("\nMESSAGES:\n")
    for m in result["messages"]:
        m.pretty_print()
    print("END" + "-" * 80 + "END")

# Optional debugging helper:
# if uncommented later, this can be used to inspect step-by-step graph history
# in the checkpoint store.
# for snapshot in graph.get_state_history(config):
#     print("step:", snapshot.metadata.get("step"))
#     print("next:", snapshot.next)
#     print("values:", snapshot.values)
#     print()


# Future manual test menu:
# Use these one at a time later as graphv3 becomes more complete.
#
# messages1  -> simplest create-only success case
# messages2  -> one message, many new people
# messages3  -> many create-relevant messages, one new person each
# messages4  -> many create-relevant messages, mixed per-message create counts
# messages5  -> create + irrelevant chatter
# messages6  -> mixed create/update in one message
# messages7  -> many update-relevant messages plus one create message
# messages8  -> many create messages to stress total_new_person_count
# messages9  -> likely planner/extract mismatch candidate
# messages10 -> repeated mention of the same new person across messages


tests = [
    messages1,
    messages2,
    messages3,
    messages4,
    messages5,
    messages6,
    messages7,
    messages8,
    messages9,
    messages10,
        ]

for i, test in enumerate(tests):
    print(f"TEST{i + 1}\n")
    run_test(test, base_existing, i+1)

# run_test(tests[1], base_existing)
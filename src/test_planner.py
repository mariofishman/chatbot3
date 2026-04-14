from graphv2 import planner_node, ExtractionState, UserProfile
from langchain_core.messages import HumanMessage
from pprint import pprint

def run_test(state: ExtractionState, expected: dict, test_name: str = "TEST"):
    result = planner_node(state)

    actual = result["plan"].model_dump()

    if (
        actual["target_ids_to_update"] == expected["target_ids_to_update"]
        and actual["new_person_count"] == expected["new_person_count"]
    ):
        print(f"{test_name} PASS")
    else:
        print(f"{test_name} FAIL")
    pprint(actual)


# TEST1
state = ExtractionState(
    messages=[HumanMessage(content="My name is Mario. I work in Krowdy")],
    existing={
        "user_001": UserProfile(
            name= "Philip",
            location= "London"
            )
    }
)

# Expected:
# target_ids_to_update = []
# new_person_count = 1
expected = {
    "target_ids_to_update": [],
    "new_person_count": 1,
}

run_test(state=state, expected=expected, test_name="TEST1")

# TEST2
state2 = ExtractionState(
    messages=[HumanMessage(content="Philip now lives in Zurich.")],
    existing={
        "user_001": UserProfile(
            name="Philip",
            location="London"
        )
    }
)

# Expected:
# target_ids_to_update = ["user_001"]
# new_person_count = 0
expected2 = {
    "target_ids_to_update": ["user_001"],
    "new_person_count": 0,
}
result2 = planner_node(state2)
actual2 = result2["plan"].model_dump()

run_test(state=state2, expected=expected2, test_name="TEST2")

# TEST3
state3 = ExtractionState(
    messages=[HumanMessage(content="Philip now lives in Zurich. I also met Lucia Romero, a startup lawyer from Lima.")],
    existing={
        "user_001": UserProfile(
            name="Philip",
            location="London"
        )
    }
)

# Expected:
# target_ids_to_update = ["user_001"]
# new_person_count = 1
expected3 = {
    "target_ids_to_update": ["user_001"],
    "new_person_count": 1,
}

run_test(state=state3, expected=expected3, test_name="TEST3")

# TEST4
state4 = ExtractionState(
    messages=[HumanMessage(content="Mario is very interested in tae kwon do.")],
    existing={
        "user_001": UserProfile(
            name="Mario",
            company="Krowdy",
            location="Peru"
        )
    }
)

# Expected:
# target_ids_to_update = ["user_001"]
# new_person_count = 0
expected4 = {
    "target_ids_to_update": ["user_001"],
    "new_person_count": 0,
}

run_test(state=state4, expected=expected4, test_name="TEST4")

# TEST5
state5 = ExtractionState(
    messages=[HumanMessage(content="Nice weather today.")],
    existing={
        "user_001": UserProfile(
            name="Mario",
            company="Krowdy",
            location="Peru"
        )
    }
)

# Expected:
# target_ids_to_update = []
# new_person_count = 0
expected5 = {
    "target_ids_to_update": [],
    "new_person_count": 0,
}

run_test(state=state5, expected=expected5, test_name="TEST5")

# TEST6
state6 = ExtractionState(
    messages=[HumanMessage(content="Yesterday I met Lucia Romero, a startup lawyer from Lima, and Ana Torres, a product manager from Madrid.")],
    existing={
        "user_001": UserProfile(
            name="Philip",
            location="London"
        )
    }
)

# Expected:
# target_ids_to_update = []
# new_person_count = 2
expected6 = {
    "target_ids_to_update": [],
    "new_person_count": 2,
}

run_test(state=state6, expected=expected6, test_name="TEST6")

# TEST7
# Exploratory only:
# the current planner cannot represent ambiguity explicitly yet.
# This test is useful to inspect whether ambiguity is reflected in
# reasoning_summary, but it should not block progress right now.
state7 = ExtractionState(
    messages=[HumanMessage(content="Philip now lives in Zurich.")],
    existing={
        "user_001": UserProfile(
            name="Philip",
            location="London",
            company="London Metals Limited"
        ),
        "user_002": UserProfile(
            name="Philip",
            location="Berlin",
            company="DataBridge"
        )
    }
)

# Expected:
# ambiguous identity should not force an update
# target_ids_to_update = []
# new_person_count = 0
expected7 = {
    "target_ids_to_update": [],
    "new_person_count": 0,
}

run_test(state=state7, expected=expected7, test_name="TEST7")

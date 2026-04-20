from pprint import pprint

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from state import MessageSelectionOutput, UserProfile


load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)


def format_string_from_user_profile(user: UserProfile) -> str:
    return "\n".join([f"{k} : {v}" for k, v in user.model_dump().items()])


def run_test(messages, existing_profiles, test_name: str = "TEST"):
    planner_prompt = """
You are a planner for a structured memory extraction system.

Your job is only to identify which human messages are relevant for:
1. creating or extracting new user profiles
2. updating existing user profiles

Existing profiles:
{formatted_existing}

Rules:
- Only return IDs that belong to human messages.
- Use the IDs exactly as provided.
- Ignore the system message.
- Include every human message that contains profile-relevant information.
- A single human message may be relevant for both creating new profiles and updating existing profiles.
- If a message contains update information, add an item to relevant_for_update_links with the message_id and the correct user_profile_ids.
- If a message contains create information, add an item to relevant_for_create_links with the message_id and the number of new people mentioned in that message.
- The same message ID may appear in relevant_for_create_links and also inside relevant_for_update_links.
- Do not invent IDs.
- Do not invent existing user profile IDs.

Return output that matches the MessageSelectionOutput schema exactly.
"""

    formatted_existing = "\n".join(
        [
            f"Obj_id = {k}:\n{format_string_from_user_profile(v)}\n"
            + "-" * 60
            + "\n"
            for k, v in existing_profiles.items()
        ]
    )

    full_messages = [
        SystemMessage(content=planner_prompt.format(formatted_existing=formatted_existing)),
        *messages,
    ]

    structured_llm = llm.with_structured_output(MessageSelectionOutput)
    result = structured_llm.invoke(full_messages)

    print(f"\n{test_name}")
    pprint(result.model_dump())


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
messages1 = [
    HumanMessage(id="hm_001", content="I met Lucia Romero, a startup lawyer from Lima."),
]

run_test(messages=messages1, existing_profiles=base_existing, test_name="TEST1")


# TEST2: update only
messages2 = [
    HumanMessage(id="hm_001", content="Philip de Haas now lives in Zurich."),
]

run_test(messages=messages2, existing_profiles=base_existing, test_name="TEST2")


# TEST3: same message does both create and update
messages3 = [
    HumanMessage(
        id="hm_001",
        content="Philip de Haas now lives in Zurich, and I also met Lucia Romero, a startup lawyer from Lima.",
    ),
]

run_test(messages=messages3, existing_profiles=base_existing, test_name="TEST3")


# TEST4: irrelevant message
messages4 = [
    HumanMessage(id="hm_001", content="Nice weather today."),
]

run_test(messages=messages4, existing_profiles=base_existing, test_name="TEST4")


# TEST5: one message updates multiple existing people
messages5 = [
    HumanMessage(
        id="hm_001",
        content="Mario Fishman is interested in tae kwon do, and Philip de Haas now lives in Zurich.",
    ),
]

run_test(messages=messages5, existing_profiles=base_existing, test_name="TEST5")


# TEST6: one message creates multiple new people
messages6 = [
    HumanMessage(
        id="hm_001",
        content="Yesterday I met Lucia Romero, a startup lawyer from Lima, Ana Torres, a product manager from Madrid, and Diego Salazar, a software engineer from Arequipa.",
    ),
]

run_test(messages=messages6, existing_profiles=base_existing, test_name="TEST6")

from pathlib import Path
import sys

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import graphv3
from state import UserProfile


def test_annotation_to_text_formats_plain_optional_and_list_types():
    assert graphv3.annotation_to_text(str) == "str"
    assert graphv3.annotation_to_text(str | None) == "Optional[str]"
    assert graphv3.annotation_to_text(list[str]) == "list[str]"


def test_format_messages_keeps_human_and_ai_and_excludes_system():
    messages = [
        HumanMessage(content="Hello", id="hm_001"),
        AIMessage(content="Hi there", id="ai_001"),
        SystemMessage(content="Ignore me", id="sys_001"),
    ]

    result = graphv3.format_messages(messages)

    assert "human: Hello; id: hm_001" in result
    assert "ai: Hi there; id: ai_001" in result
    assert "sys_001" not in result
    assert "Ignore me" not in result


def test_format_string_from_user_profile_contains_expected_fields():
    user = UserProfile(
        name="Philip de Haas",
        company="London Metals Limited",
        role="Owner",
        location="London",
        interests=["metals", "finance"],
    )

    result = graphv3.format_string_from_user_profile(user)

    assert "name : Philip de Haas" in result
    assert "company : London Metals Limited" in result
    assert "location : London" in result
    assert "interests : ['metals', 'finance']" in result


def test_format_string_from_schema_contains_field_descriptions_and_types():
    result = graphv3.format_string_from_schema(UserProfile)

    assert "name:" in result
    assert "User's full name" in result
    assert "type of this field: Optional[str]" in result
    assert "company:" in result
    assert "Company the user works at" in result
    assert "type of this field: Optional[str]" in result
    assert "interests:" in result
    assert "Important interests or topics the user cares about" in result
    assert "type of this field: list[str]" in result

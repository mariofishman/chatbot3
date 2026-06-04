from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from state import UserProfile, merge_profiles


def make_profile(
    name: str,
    company: str | None = None,
    role: str | None = None,
    location: str | None = None,
    interests: list[str] | None = None,
) -> UserProfile:
    return UserProfile(
        name=name,
        company=company,
        role=role,
        location=location,
        interests=interests or [],
    )


def test_merge_profiles_adds_brand_new_id():
    existing = {
        "user_001": make_profile("Philip de Haas", location="London"),
    }
    new = {
        "user_002": make_profile("Lucia Romero", location="Lima"),
    }

    result = merge_profiles(existing, new)

    assert "user_001" in result
    assert "user_002" in result
    assert result["user_001"].name == "Philip de Haas"
    assert result["user_002"].name == "Lucia Romero"


def test_merge_profiles_keeps_profiles_missing_from_new():
    existing = {
        "user_001": make_profile("Philip de Haas", location="London"),
        "user_002": make_profile("Lucia Romero", location="Lima"),
    }
    new = {
        "user_001": make_profile("Philip de Haas", location="Zurich"),
    }

    result = merge_profiles(existing, new)

    assert result["user_001"].location == "Zurich"
    assert result["user_002"].location == "Lima"


def test_merge_profiles_replaces_whole_profile_for_shared_id():
    existing = {
        "user_001": make_profile(
            "Philip de Haas",
            company="London Metals Limited",
            role="Owner",
            location="London",
            interests=["metals"],
        )
    }
    new_profile = make_profile(
        "Philip de Haas",
        company="London Metals Limited",
        role="Chairman",
        location="Zurich",
        interests=["finance"],
    )
    new = {"user_001": new_profile}

    result = merge_profiles(existing, new)

    assert result["user_001"] == new_profile
    assert result["user_001"] is new_profile


def test_merge_profiles_handles_empty_and_none_inputs():
    new = {"user_001": make_profile("Lucia Romero", location="Lima")}
    existing = {"user_002": make_profile("Philip de Haas", location="London")}

    assert merge_profiles({}, {}) == {}
    assert merge_profiles(None, new) == new
    assert merge_profiles(existing, None) == existing


def test_merge_profiles_returns_fresh_dict_and_does_not_mutate_inputs():
    existing = {"user_001": make_profile("Philip de Haas", location="London")}
    new = {"user_002": make_profile("Lucia Romero", location="Lima")}

    existing_before = existing.copy()
    new_before = new.copy()

    result = merge_profiles(existing, new)

    assert result is not existing
    assert result is not new
    assert set(result.keys()) == {"user_001", "user_002"}
    assert existing == existing_before
    assert new == new_before

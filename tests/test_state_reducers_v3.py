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


def test_merge_profiles_accumulates_separate_create_branch_slices():
    existing = {"user_001": make_profile("Philip de Haas", location="London")}
    first_create = {"user_002": make_profile("Lucia Romero", location="Lima")}
    second_create = {"user_003": make_profile("John Smith", location="Miami")}
    existing_before = existing.copy()
    first_create_before = first_create.copy()
    second_create_before = second_create.copy()

    after_first_create = merge_profiles(existing, first_create)
    result = merge_profiles(after_first_create, second_create)

    assert set(result) == {"user_001", "user_002", "user_003"}
    assert result["user_001"] == existing["user_001"]
    assert result["user_002"] == first_create["user_002"]
    assert result["user_003"] == second_create["user_003"]
    assert existing == existing_before
    assert first_create == first_create_before
    assert second_create == second_create_before


def test_merge_profiles_mixed_distinct_id_slices_are_order_independent():
    original_profile = make_profile(
        "Philip de Haas",
        role="Owner",
        location="London",
    )
    unrelated_profile = make_profile("Lucia Romero", location="Lima")
    updated_profile = make_profile(
        "Philip de Haas",
        role="Chairman",
        location="Zurich",
    )
    created_profile = make_profile("John Smith", location="Miami")
    existing = {
        "user_001": original_profile,
        "user_002": unrelated_profile,
    }
    create_slice = {"user_003": created_profile}
    update_slice = {"user_001": updated_profile}

    create_then_update = merge_profiles(
        merge_profiles(existing, create_slice),
        update_slice,
    )
    update_then_create = merge_profiles(
        merge_profiles(existing, update_slice),
        create_slice,
    )

    assert create_then_update == update_then_create
    assert create_then_update["user_001"] is updated_profile
    assert create_then_update["user_002"] is unrelated_profile
    assert create_then_update["user_003"] is created_profile


def test_merge_profiles_same_id_slices_use_last_whole_profile():
    first_profile = make_profile(
        "Philip de Haas",
        role="Owner",
        location="London",
        interests=["metals"],
    )
    second_profile = make_profile(
        "Philip de Haas",
        role="Chairman",
        location="Zurich",
        interests=["finance"],
    )
    first_slice = {"user_001": first_profile}
    second_slice = {"user_001": second_profile}

    first_then_second = merge_profiles(
        merge_profiles({}, first_slice),
        second_slice,
    )
    second_then_first = merge_profiles(
        merge_profiles({}, second_slice),
        first_slice,
    )

    assert first_then_second["user_001"] is second_profile
    assert second_then_first["user_001"] is first_profile
    assert first_then_second["user_001"].interests == ["finance"]
    assert second_then_first["user_001"].interests == ["metals"]

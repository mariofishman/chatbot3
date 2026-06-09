from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from state import SubjectBucket


def test_subject_bucket_accepts_existing_person_with_candidate_id():
    bucket = SubjectBucket(
        subject_label="Lucia Romero",
        message_ids=["hm_001", "hm_002"],
        candidate_existing_id="user_001",
        classification="existing",
    )

    assert bucket.subject_label == "Lucia Romero"
    assert bucket.message_ids == ["hm_001", "hm_002"]
    assert bucket.candidate_existing_id == "user_001"
    assert bucket.classification == "existing"


def test_subject_bucket_accepts_new_person_without_candidate_id():
    bucket = SubjectBucket(
        subject_label="Diego Salazar",
        message_ids=["hm_001", "hm_003"],
        classification="new",
    )

    assert bucket.candidate_existing_id is None
    assert bucket.classification == "new"


def test_subject_bucket_rejects_existing_person_without_candidate_id():
    with pytest.raises(ValidationError, match="candidate_existing_id must be set"):
        SubjectBucket(
            subject_label="Lucia Romero",
            message_ids=["hm_001"],
            classification="existing",
        )


def test_subject_bucket_rejects_new_person_with_candidate_id():
    with pytest.raises(ValidationError, match="candidate_existing_id must be None"):
        SubjectBucket(
            subject_label="Diego Salazar",
            message_ids=["hm_001"],
            candidate_existing_id="user_999",
            classification="new",
        )


def test_subject_bucket_rejects_classification_outside_part_three_scope():
    with pytest.raises(ValidationError):
        SubjectBucket(
            subject_label="Unknown person",
            message_ids=["hm_001"],
            classification="ambiguous",
        )


@pytest.mark.parametrize(
    ("subject_label", "message_ids", "candidate_existing_id", "classification"),
    [
        ("", ["hm_001"], None, "new"),
        ("Lucia Romero", [], None, "new"),
        ("Lucia Romero", ["hm_001"], "", "existing"),
    ],
)
def test_subject_bucket_rejects_empty_required_identity_evidence(
    subject_label,
    message_ids,
    candidate_existing_id,
    classification,
):
    with pytest.raises(ValidationError):
        SubjectBucket(
            subject_label=subject_label,
            message_ids=message_ids,
            candidate_existing_id=candidate_existing_id,
            classification=classification,
        )

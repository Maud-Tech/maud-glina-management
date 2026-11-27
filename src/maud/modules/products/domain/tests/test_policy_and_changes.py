from datetime import date

import pytest

from maud.modules.products.domain.changes import changed_fields
from maud.modules.products.domain.policy import PolicyStatus, is_effective, validate_policy
from maud.shared.errors import DomainError

START = date(2026, 1, 1)
END = date(2026, 12, 31)


def test_effective_until_must_be_after_effective_from() -> None:
    with pytest.raises(DomainError) as error:
        validate_policy(
            policy_number="AP-1", issue_date=None, effective_from=END, effective_until=START
        )

    assert error.value.code == "policy_dates_invalid"


def test_blank_policy_number_is_rejected() -> None:
    with pytest.raises(DomainError) as error:
        validate_policy(
            policy_number="  ", issue_date=None, effective_from=START, effective_until=None
        )

    assert error.value.code == "policy_number_required"


@pytest.mark.parametrize(
    ("on", "expected"),
    [(date(2025, 12, 31), False), (START, True), (END, True), (date(2027, 1, 1), False)],
)
def test_policy_is_effective_inside_its_period_including_last_day(on: date, expected: bool) -> None:
    assert is_effective(PolicyStatus.ACTIVE, START, END, on) is expected


def test_expired_policy_is_never_effective() -> None:
    assert not is_effective(PolicyStatus.EXPIRED, START, None, date(2026, 6, 1))


def test_changed_fields_keeps_only_what_changed_with_before_and_after() -> None:
    before = {"name": "A", "status": "DRAFT", "notes": None}
    after = {"name": "B", "status": "DRAFT", "notes": "x"}

    assert changed_fields(before, after) == {"name": ["A", "B"], "notes": [None, "x"]}


def test_changed_fields_from_nothing_lists_filled_fields_only() -> None:
    assert changed_fields({}, {"code": "P1", "closing_date": None}) == {"code": [None, "P1"]}

"""Unit tests for pure reservation domain rules."""

import builtins
from datetime import datetime, timedelta, timezone

import pytest

from app import erros
from app.dominio.regras import (
    StatusReserva,
    is_overlapping_interval,
    material_stock_available,
    transition_reservation_status,
)
from app.erros import PermissaoNegadaError, ValidationError


def test_permission_denied_exception_does_not_shadow_builtin() -> None:
    assert erros.PermissaoNegadaError is PermissaoNegadaError
    assert not hasattr(erros, "PermissionError")
    assert builtins.PermissionError is PermissionError


def test_interval_overlap_rule_detects_conflict() -> None:
    """Verifica FR-06, RN02, CT-15."""
    assert is_overlapping_interval(
        datetime(2026, 1, 10, 9, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 11, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc),
    )
    assert not is_overlapping_interval(
        datetime(2026, 1, 10, 9, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 11, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 11, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc),
    )

    aware = datetime(2026, 1, 10, 9, 0, tzinfo=timezone.utc)
    later = aware + timedelta(hours=1)
    naive = datetime(2026, 1, 10, 9, 0)
    for arguments in (
        (naive, later, aware, later),
        (aware, naive, aware, later),
        (aware, later, naive, later),
        (aware, later, aware, naive),
        (later, aware, aware, later),
        (aware, later, later, aware),
    ):
        with pytest.raises(ValidationError):
            is_overlapping_interval(*arguments)


def test_material_stock_is_rejected_when_exceeded() -> None:
    """Verifica FR-06, RN02, CT-18 e CT-20."""
    assert material_stock_available(available=5, reserved=3, requested=2) is True
    assert material_stock_available(available=5, reserved=3, requested=3) is False
    assert material_stock_available(available=4, reserved=3, requested=2) is False
    assert material_stock_available(available=1, reserved=5, requested=1) is False

    for arguments in (
        {"available": -1, "reserved": 0, "requested": 1},
        {"available": 1, "reserved": -1, "requested": 1},
        {"available": 1, "reserved": 0, "requested": 0},
        {"available": 1, "reserved": 0, "requested": -1},
    ):
        with pytest.raises(ValidationError):
            material_stock_available(**arguments)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (StatusReserva.SOLICITADA, StatusReserva.PENDENTE),
        (StatusReserva.PENDENTE, StatusReserva.APROVADA),
        (StatusReserva.APROVADA, StatusReserva.CONFIRMADA),
        (StatusReserva.CONFIRMADA, StatusReserva.EM_USO),
        (StatusReserva.EM_USO, StatusReserva.CONCLUIDA),
    ],
)
def test_reservation_status_transition_follows_the_confirmed_lifecycle(current, target) -> None:
    assert transition_reservation_status(current, target) is target


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (StatusReserva.CANCELADA, StatusReserva.PENDENTE),
        (StatusReserva.CONCLUIDA, StatusReserva.APROVADA),
        (StatusReserva.SOLICITADA, StatusReserva.CONCLUIDA),
        (StatusReserva.PENDENTE, StatusReserva.PENDENTE),
        ("INVALIDO", StatusReserva.PENDENTE),
        (StatusReserva.SOLICITADA, "INVALIDO"),
    ],
)
def test_final_reservation_status_cannot_transition(current, target) -> None:
    with pytest.raises(ValidationError):
        transition_reservation_status(current, target)

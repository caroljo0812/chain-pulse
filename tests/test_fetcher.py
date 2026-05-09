import dataclasses
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from chain_pulse.chains import CHAINS
from chain_pulse.fetcher import Balance, Fetcher, FetchError


def _make(monkeypatch, *, balance_return=None, balance_raise=None):
    f = Fetcher(CHAINS["sepolia"])
    eth = MagicMock()
    if balance_raise is not None:
        eth.get_balance.side_effect = balance_raise
    else:
        eth.get_balance.return_value = balance_return
    monkeypatch.setattr(f, "_w3", MagicMock(eth=eth))
    return f


def test_balance_returns_wei_and_symbol(monkeypatch):
    f = _make(monkeypatch, balance_return=10**18)
    b = f.balance("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
    assert b.wei == 10**18
    assert b.eth == Decimal("1")
    assert b.symbol == "ETH"
    assert b.chain == "sepolia"


def test_balance_zero(monkeypatch):
    f = _make(monkeypatch, balance_return=0)
    b = f.balance("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
    assert b.wei == 0
    assert b.eth == Decimal("0")


def test_balance_fractional_eth(monkeypatch):
    f = _make(monkeypatch, balance_return=123_456_789_000_000_000)
    b = f.balance("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
    assert b.eth == Decimal("0.123456789")


def test_balance_network_error_wraps(monkeypatch):
    f = _make(monkeypatch, balance_raise=ConnectionError("boom"))
    with pytest.raises(FetchError, match="sepolia"):
        f.balance("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")


def test_balance_dataclass_is_frozen():
    b = Balance(chain="base", address="0x" + "a" * 40, wei=1, symbol="ETH")
    with pytest.raises(dataclasses.FrozenInstanceError):
        b.wei = 2  # type: ignore[misc]

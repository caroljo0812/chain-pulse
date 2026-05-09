from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from chain_pulse.chains import CHAINS
from chain_pulse.fetcher import Fetcher, FetchError


def test_gas_price_gwei(monkeypatch):
    f = Fetcher(CHAINS["base"])
    eth = MagicMock()
    eth.gas_price = 25 * 10**9  # 25 gwei
    monkeypatch.setattr(f, "_w3", MagicMock(eth=eth))
    assert f.gas_price_gwei() == Decimal("25")


def test_gas_price_sub_gwei(monkeypatch):
    f = Fetcher(CHAINS["arbitrum"])
    eth = MagicMock()
    eth.gas_price = 100_000_000  # 0.1 gwei (Arbitrum-style)
    monkeypatch.setattr(f, "_w3", MagicMock(eth=eth))
    assert f.gas_price_gwei() == Decimal("0.1")


def test_gas_price_error_wraps(monkeypatch):
    f = Fetcher(CHAINS["base"])
    eth = MagicMock()
    type(eth).gas_price = property(lambda _self: (_ for _ in ()).throw(ConnectionError("boom")))
    monkeypatch.setattr(f, "_w3", MagicMock(eth=eth))
    with pytest.raises(FetchError, match="base/gas"):
        f.gas_price_gwei()

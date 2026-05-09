from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from chain_pulse.chains import CHAINS
from chain_pulse.fetcher import Fetcher, FetchError, TokenBalance
from chain_pulse.tokens import for_chain


def _fetcher_with_token(monkeypatch, *, raw_return=None, raise_=None):
    f = Fetcher(CHAINS["base"])
    contract = MagicMock()
    if raise_ is not None:
        contract.functions.balanceOf.return_value.call.side_effect = raise_
    else:
        contract.functions.balanceOf.return_value.call.return_value = raw_return
    eth = MagicMock()
    eth.contract.return_value = contract
    monkeypatch.setattr(f, "_w3", MagicMock(eth=eth))
    return f


def test_token_balance_decodes_decimals(monkeypatch):
    f = _fetcher_with_token(monkeypatch, raw_return=1_500_000)  # 1.5 USDC
    usdc = for_chain("base")[0]
    b = f.token_balance("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", usdc)
    assert isinstance(b, TokenBalance)
    assert b.raw == 1_500_000
    assert b.amount == Decimal("1.5")
    assert b.token.symbol == "USDC"


def test_token_balance_zero(monkeypatch):
    f = _fetcher_with_token(monkeypatch, raw_return=0)
    usdc = for_chain("base")[0]
    b = f.token_balance("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", usdc)
    assert b.amount == Decimal("0")


def test_token_balance_wraps_error(monkeypatch):
    f = _fetcher_with_token(monkeypatch, raise_=ConnectionError("rpc died"))
    usdc = for_chain("base")[0]
    with pytest.raises(FetchError, match="base/USDC"):
        f.token_balance("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", usdc)


def test_token_registry_has_all_default_chains():
    for key in CHAINS:
        toks = for_chain(key)
        assert toks, f"missing tokens for {key}"
        assert toks[0].symbol == "USDC"

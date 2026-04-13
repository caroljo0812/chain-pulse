import pytest

from chain_pulse.chains import CHAINS, resolve


def test_all_four_default_chains_present():
    assert set(CHAINS) == {"sepolia", "base", "arbitrum", "optimism"}


def test_resolve_none_returns_all():
    assert len(resolve(None)) == 4


def test_resolve_subset_preserves_order():
    out = resolve("base,sepolia")
    assert [c.key for c in out] == ["base", "sepolia"]


def test_resolve_handles_whitespace_and_case():
    out = resolve(" Base , SEPOLIA ")
    assert [c.key for c in out] == ["base", "sepolia"]


def test_resolve_unknown_chain_raises():
    with pytest.raises(ValueError, match="unknown chain"):
        resolve("base,solana")


def test_rpc_env_override(monkeypatch):
    monkeypatch.setenv("BASE_RPC", "https://my-private-base.example/v1")
    assert CHAINS["base"].rpc == "https://my-private-base.example/v1"

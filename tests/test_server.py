from unittest.mock import patch

from fastapi.testclient import TestClient

from chain_pulse.chains import CHAINS
from chain_pulse.fetcher import Balance
from chain_pulse.runner import ChainResult
from chain_pulse.server import create_app


def _fake(addr: str, *, with_tokens=False, with_gas=False) -> list[ChainResult]:
    out = []
    from decimal import Decimal

    from chain_pulse.fetcher import TokenBalance
    from chain_pulse.tokens import for_chain
    for k, c in CHAINS.items():
        toks = []
        if with_tokens:
            for t in for_chain(k):
                toks.append(TokenBalance(chain=k, address=addr, token=t, raw=2_500_000))
        out.append(ChainResult(
            chain=c,
            balance=Balance(chain=k, address=addr, wei=10**17, symbol="ETH"),
            error=None,
            tokens=toks,
            gas_gwei=Decimal("12.5") if with_gas else None,
        ))
    return out


def test_index_serves_html():
    client = TestClient(create_app())
    r = client.get("/")
    assert r.status_code == 200
    assert "chain-pulse" in r.text
    assert "<title>" in r.text


def test_health():
    client = TestClient(create_app())
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_chains_lists_defaults():
    client = TestClient(create_app())
    r = client.get("/api/chains")
    assert r.status_code == 200
    keys = {c["key"] for c in r.json()["chains"]}
    assert keys == set(CHAINS)


def test_scan_invalid_address_400():
    client = TestClient(create_app())
    r = client.get("/api/scan", params={"address": "garbage"})
    assert r.status_code == 400
    assert "error" in r.json()


def test_scan_unknown_chain_400():
    client = TestClient(create_app())
    addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    r = client.get("/api/scan", params={"address": addr, "chains": "solana"})
    assert r.status_code == 400


def test_scan_returns_per_chain_payload():
    addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    client = TestClient(create_app())
    with patch("chain_pulse.server.query_all", return_value=_fake(addr, with_tokens=True, with_gas=True)):
        r = client.get("/api/scan", params={"address": addr.lower(), "tokens": "true", "gas": "true"})
    assert r.status_code == 200
    body = r.json()
    assert body["address"] == addr  # checksum normalized
    assert {c["key"] for c in body["chains"]} == set(CHAINS)
    base = next(c for c in body["chains"] if c["key"] == "base")
    assert base["ok"] is True
    assert base["balance"]["formatted"] == "0.1"
    assert base["balance"]["symbol"] == "ETH"
    assert base["tokens"][0]["symbol"] == "USDC"
    assert base["tokens"][0]["formatted"] == "2.5"
    assert base["gas_gwei"] == "12.5"
    assert base["explorer"].endswith(addr)

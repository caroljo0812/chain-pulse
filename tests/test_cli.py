from unittest.mock import patch

from click.testing import CliRunner

from chain_pulse.chains import CHAINS
from chain_pulse.cli import main
from chain_pulse.fetcher import Balance
from chain_pulse.runner import ChainResult


def _fake_results(address: str, *, wei_per_chain: dict[str, int] | None = None,
                  errors: dict[str, str] | None = None) -> list[ChainResult]:
    wei_per_chain = wei_per_chain or {}
    errors = errors or {}
    out = []
    for key, chain in CHAINS.items():
        if key in errors:
            out.append(ChainResult(chain=chain, balance=None, error=errors[key]))
        else:
            wei = wei_per_chain.get(key, 0)
            out.append(ChainResult(
                chain=chain,
                balance=Balance(chain=key, address=address, wei=wei, symbol="ETH"),
                error=None,
            ))
    return out


def test_help_works():
    r = CliRunner().invoke(main, ["--help"])
    assert r.exit_code == 0
    assert "chain-pulse" in r.output.lower()


def test_no_args_exits_with_usage_error():
    r = CliRunner().invoke(main, [])
    assert r.exit_code == 2


def test_invalid_address_is_rejected():
    r = CliRunner().invoke(main, ["not-an-address"])
    assert r.exit_code == 2
    assert "error" in r.output.lower()


def test_table_output_for_single_address():
    addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    fake = _fake_results(addr, wei_per_chain={"sepolia": 10**18, "base": 5 * 10**17})
    with patch("chain_pulse.cli.query_all", return_value=fake):
        r = CliRunner().invoke(main, [addr])
    assert r.exit_code == 0
    assert "Ethereum Sepolia" in r.output
    assert "1 ETH" in r.output


def test_json_output_shape():
    addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    fake = _fake_results(addr, wei_per_chain={"base": 10**17})
    with patch("chain_pulse.cli.query_all", return_value=fake):
        r = CliRunner().invoke(main, [addr, "--json"])
    assert r.exit_code == 0
    import json as _j
    payload = _j.loads(r.output)
    assert payload["address"] == addr
    assert {c["key"] for c in payload["chains"]} == set(CHAINS)
    base = next(c for c in payload["chains"] if c["key"] == "base")
    assert base["ok"] is True
    assert base["balance_wei"] == 10**17


def test_unknown_chain_filter():
    addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    r = CliRunner().invoke(main, [addr, "--chains", "solana"])
    assert r.exit_code == 2
    assert "unknown chain" in r.output


def test_file_mode(tmp_path):
    addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    f = tmp_path / "wallets.txt"
    f.write_text(f"# comment\n{addr}\n\n")
    fake = _fake_results(addr, wei_per_chain={"sepolia": 0})
    with patch("chain_pulse.cli.query_all", return_value=fake):
        r = CliRunner().invoke(main, ["--file", str(f)])
    assert r.exit_code == 0
    assert addr in r.output

from unittest.mock import patch

from click.testing import CliRunner

from chain_pulse.chains import CHAINS
from chain_pulse.cli import main
from chain_pulse.fetcher import Balance
from chain_pulse.runner import ChainResult


def _fake(addr: str) -> list[ChainResult]:
    return [
        ChainResult(
            chain=c,
            balance=Balance(chain=k, address=addr, wei=0, symbol="ETH"),
            error=None,
        )
        for k, c in CHAINS.items()
    ]


def test_watch_zero_rejected():
    addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    r = CliRunner().invoke(main, [addr, "--watch", "0"])
    assert r.exit_code == 2
    assert ">= 1 second" in r.output


def test_watch_with_json_rejected():
    addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    r = CliRunner().invoke(main, [addr, "--watch", "5", "--json"])
    assert r.exit_code == 2
    assert "not compatible" in r.output


def test_watch_loop_exits_on_interrupt():
    addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

    sleep_calls = {"n": 0}

    def fake_sleep(_secs):
        sleep_calls["n"] += 1
        if sleep_calls["n"] >= 2:
            raise KeyboardInterrupt
        return None

    with patch("chain_pulse.cli.query_all", return_value=_fake(addr)), \
         patch("time.sleep", side_effect=fake_sleep):
        r = CliRunner().invoke(main, [addr, "--watch", "1"])

    assert r.exit_code == 0
    assert "stopped" in r.output
    # rendered the table at least twice before Ctrl-C
    assert r.output.count("Ethereum Sepolia") >= 2

"""chain-pulse CLI entry point."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from . import __version__
from .address import InvalidAddress, normalize
from .chains import CHAINS, resolve
from .runner import ChainResult, query_all


def _format_eth(wei: int) -> str:
    # use Decimal — float division of large wei values silently drops precision
    # past ~15 sig figs, which made dust balances and exact 1.000000000000000001
    # ETH inputs both render as "1".
    from decimal import Decimal
    eth = Decimal(wei) / Decimal(10**18)
    if eth == 0:
        return "0"
    s = format(eth, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def _render_table(address: str, results: list[ChainResult], console: Console) -> None:
    t = Table(title=f"chain-pulse · {address}", show_lines=False)
    t.add_column("chain", style="cyan", no_wrap=True)
    t.add_column("balance", justify="right")
    t.add_column("tokens", justify="right")
    t.add_column("explorer", style="dim")
    for r in results:
        if r.ok and r.balance is not None:
            tokens_cell = (
                ", ".join(
                    f"{format(tb.amount.normalize(), 'f').rstrip('0').rstrip('.') or '0'} {tb.token.symbol}"
                    for tb in r.tokens
                )
                if r.tokens
                else "—"
            )
            t.add_row(
                r.chain.name,
                f"{_format_eth(r.balance.wei)} {r.balance.symbol}",
                tokens_cell,
                f"{r.chain.explorer}/address/{address}",
            )
        else:
            t.add_row(r.chain.name, "[red]error[/red]", "—", r.error or "")
    console.print(t)


def _render_json(address: str, results: list[ChainResult]) -> None:
    payload = {
        "address": address,
        "chains": [
            {
                "key": r.chain.key,
                "chain_id": r.chain.chain_id,
                "ok": r.ok,
                "balance_wei": r.balance.wei if r.balance else None,
                "symbol": r.balance.symbol if r.balance else None,
                "tokens": [
                    {
                        "symbol": tb.token.symbol,
                        "address": tb.token.address,
                        "raw": tb.raw,
                        "decimals": tb.token.decimals,
                    }
                    for tb in r.tokens
                ],
                "token_errors": list(r.token_errors),
                "gas_gwei": str(r.gas_gwei) if r.gas_gwei is not None else None,
                "error": r.error,
            }
            for r in results
        ],
    }
    print(json.dumps(payload, indent=2))


def _read_addresses(path: Path) -> list[str]:
    out: list[str] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


@click.command(name="chain-pulse")
@click.argument("address", required=False)
@click.option("--file", "-f", "file_", type=click.Path(exists=True, path_type=Path),
              help="Read addresses from a file (one per line, # comments allowed).")
@click.option("--chains", "chains_csv", default=None,
              help=f"Comma-separated chain keys. Default: all ({', '.join(CHAINS)}).")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON instead of a table.")
@click.option("--tokens/--no-tokens", default=False, show_default=True,
              help="Also fetch ERC-20 balances for the curated token list.")
@click.option("--gas/--no-gas", default=False, show_default=True,
              help="Also fetch current gas price per chain (gwei).")
@click.option("--watch", "watch_secs", type=int, default=None,
              help="Re-poll every N seconds. Ctrl-C to stop.")
@click.option("--timeout", default=10, show_default=True, help="Per-RPC timeout in seconds.")
@click.version_option(__version__, prog_name="chain-pulse")
def main(address: str | None, file_: Path | None, chains_csv: str | None,
         as_json: bool, tokens: bool, gas: bool, watch_secs: int | None,
         timeout: int) -> None:
    """Inspect EVM wallet balances across multiple chains."""
    load_dotenv()
    console = Console()

    if not address and not file_:
        click.echo("error: pass an ADDRESS or --file", err=True)
        sys.exit(2)
    if address and file_:
        click.echo("error: ADDRESS and --file are mutually exclusive", err=True)
        sys.exit(2)

    try:
        chains = resolve(chains_csv)
    except ValueError as e:
        click.echo(f"error: {e}", err=True)
        sys.exit(2)

    raw_addrs = [address] if address else _read_addresses(file_)  # type: ignore[arg-type]
    try:
        addrs = [normalize(a) for a in raw_addrs]
    except InvalidAddress as e:
        click.echo(f"error: {e}", err=True)
        sys.exit(2)

    def _run_once() -> None:
        for a in addrs:
            results = query_all(
                a, chains, timeout=timeout, include_tokens=tokens, include_gas=gas,
            )
            if as_json:
                _render_json(a, results)
            else:
                _render_table(a, results, console)

    if watch_secs is None:
        _run_once()
        return

    if watch_secs < 1:
        click.echo("error: --watch must be >= 1 second", err=True)
        sys.exit(2)
    if as_json:
        click.echo("error: --watch and --json are not compatible", err=True)
        sys.exit(2)

    import time
    try:
        while True:
            console.clear()
            console.rule(f"[dim]chain-pulse · {time.strftime('%H:%M:%S')} · ^C to stop[/dim]")
            _run_once()
            time.sleep(watch_secs)
    except KeyboardInterrupt:
        console.print("[dim]stopped[/dim]")


if __name__ == "__main__":
    main()

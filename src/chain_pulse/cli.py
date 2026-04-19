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
    eth = wei / 10**18
    if eth == 0:
        return "0"
    if eth < 0.0001:
        return f"{eth:.8f}".rstrip("0")
    return f"{eth:.6f}".rstrip("0").rstrip(".")


def _render_table(address: str, results: list[ChainResult], console: Console) -> None:
    t = Table(title=f"chain-pulse · {address}", show_lines=False)
    t.add_column("chain", style="cyan", no_wrap=True)
    t.add_column("balance", justify="right")
    t.add_column("explorer", style="dim")
    for r in results:
        if r.ok and r.balance is not None:
            t.add_row(
                r.chain.name,
                f"{_format_eth(r.balance.wei)} {r.balance.symbol}",
                f"{r.chain.explorer}/address/{address}",
            )
        else:
            t.add_row(r.chain.name, "[red]error[/red]", r.error or "")
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
@click.option("--timeout", default=10, show_default=True, help="Per-RPC timeout in seconds.")
@click.version_option(__version__, prog_name="chain-pulse")
def main(address: str | None, file_: Path | None, chains_csv: str | None,
         as_json: bool, timeout: int) -> None:
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

    for a in addrs:
        results = query_all(a, chains, timeout=timeout)
        if as_json:
            _render_json(a, results)
        else:
            _render_table(a, results, console)


if __name__ == "__main__":
    main()

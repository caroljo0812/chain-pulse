"""FastAPI dashboard for chain-pulse.

Single-page UI: enter an EVM address, optionally toggle tokens/gas, hit Refresh,
get a live render of every default chain. Server-side rendered Jinja-free
template (string substitution is enough for one page).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse

from . import __version__
from .address import InvalidAddress, normalize
from .chains import CHAINS, resolve
from .runner import query_all

_TEMPLATE_PATH = Path(__file__).parent / "static" / "index.html"


def _format_eth(wei: int) -> str:
    eth = Decimal(wei) / Decimal(10**18)
    if eth == 0:
        return "0"
    s = format(eth, "f")
    return s.rstrip("0").rstrip(".") if "." in s else s


def _format_token_amount(raw: int, decimals: int) -> str:
    amt = Decimal(raw) / Decimal(10**decimals)
    if amt == 0:
        return "0"
    s = format(amt, "f")
    return s.rstrip("0").rstrip(".") if "." in s else s


def create_app() -> FastAPI:
    app = FastAPI(
        title="chain-pulse",
        version=__version__,
        docs_url="/api/docs",
        redoc_url=None,
    )

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        return HTMLResponse(_TEMPLATE_PATH.read_text())

    @app.get("/api/scan")
    def scan(
        address: str = Query(..., description="EVM address (0x...)"),
        chains: str | None = Query(None, description="Comma-separated chain keys"),
        tokens: bool = Query(False),
        gas: bool = Query(False),
        timeout: int = Query(10, ge=1, le=60),
    ) -> JSONResponse:
        try:
            addr = normalize(address)
        except InvalidAddress as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        try:
            chain_list = resolve(chains)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)

        results = query_all(
            addr, chain_list, timeout=timeout, include_tokens=tokens, include_gas=gas,
        )

        payload = {
            "address": addr,
            "chains": [
                {
                    "key": r.chain.key,
                    "name": r.chain.name,
                    "chain_id": r.chain.chain_id,
                    "explorer": f"{r.chain.explorer}/address/{addr}",
                    "ok": r.ok,
                    "error": r.error,
                    "balance": (
                        {
                            "wei": r.balance.wei,
                            "formatted": _format_eth(r.balance.wei),
                            "symbol": r.balance.symbol,
                        }
                        if r.balance is not None else None
                    ),
                    "tokens": [
                        {
                            "symbol": tb.token.symbol,
                            "address": tb.token.address,
                            "raw": tb.raw,
                            "decimals": tb.token.decimals,
                            "formatted": _format_token_amount(tb.raw, tb.token.decimals),
                        }
                        for tb in r.tokens
                    ],
                    "token_errors": list(r.token_errors),
                    "gas_gwei": str(r.gas_gwei) if r.gas_gwei is not None else None,
                }
                for r in results
            ],
        }
        return JSONResponse(payload)

    @app.get("/api/chains")
    def list_chains() -> JSONResponse:
        return JSONResponse(
            {
                "chains": [
                    {"key": c.key, "name": c.name, "chain_id": c.chain_id}
                    for c in CHAINS.values()
                ],
            }
        )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    return app


app = create_app()

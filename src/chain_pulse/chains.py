"""Built-in EVM chain registry.

RPC URLs can be overridden via env vars (see `.env.example`). Defaults point at
publicnode.com — no key required, fine for casual use, will rate-limit you if
you hammer it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Chain:
    key: str
    name: str
    chain_id: int
    rpc_env: str
    default_rpc: str
    explorer: str
    native_symbol: str = "ETH"

    @property
    def rpc(self) -> str:
        return os.environ.get(self.rpc_env, self.default_rpc)


CHAINS: dict[str, Chain] = {
    c.key: c
    for c in [
        Chain(
            key="sepolia",
            name="Ethereum Sepolia",
            chain_id=11155111,
            rpc_env="SEPOLIA_RPC",
            default_rpc="https://ethereum-sepolia-rpc.publicnode.com",
            explorer="https://sepolia.etherscan.io",
        ),
        Chain(
            key="base",
            name="Base",
            chain_id=8453,
            rpc_env="BASE_RPC",
            default_rpc="https://base-rpc.publicnode.com",
            explorer="https://basescan.org",
        ),
        Chain(
            key="arbitrum",
            name="Arbitrum One",
            chain_id=42161,
            rpc_env="ARBITRUM_RPC",
            default_rpc="https://arbitrum-one-rpc.publicnode.com",
            explorer="https://arbiscan.io",
        ),
        Chain(
            key="optimism",
            name="Optimism",
            chain_id=10,
            rpc_env="OPTIMISM_RPC",
            default_rpc="https://optimism-rpc.publicnode.com",
            explorer="https://optimistic.etherscan.io",
        ),
    ]
}


def resolve(keys: str | None) -> list[Chain]:
    """Resolve a comma-separated chain list (or None for all)."""
    if not keys:
        return list(CHAINS.values())
    out: list[Chain] = []
    for raw in keys.split(","):
        k = raw.strip().lower()
        if not k:
            continue
        if k not in CHAINS:
            raise ValueError(f"unknown chain: {k!r} (have: {', '.join(CHAINS)})")
        out.append(CHAINS[k])
    return out

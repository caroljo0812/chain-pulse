"""Parallel multi-chain query runner."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from .chains import Chain
from .fetcher import Balance, FetchError, Fetcher


@dataclass
class ChainResult:
    chain: Chain
    balance: Balance | None
    error: str | None

    @property
    def ok(self) -> bool:
        return self.error is None


def query_all(address: str, chains: list[Chain], *, timeout: int = 10) -> list[ChainResult]:
    """Hit every chain in parallel and return results in the same order as `chains`."""

    def _one(chain: Chain) -> ChainResult:
        try:
            bal = Fetcher(chain, timeout=timeout).balance(address)
            return ChainResult(chain=chain, balance=bal, error=None)
        except FetchError as e:
            return ChainResult(chain=chain, balance=None, error=str(e))
        except Exception as e:  # last-resort safety net
            return ChainResult(chain=chain, balance=None, error=f"{type(e).__name__}: {e}")

    if not chains:
        return []

    by_key: dict[str, ChainResult] = {}
    with ThreadPoolExecutor(max_workers=min(8, len(chains))) as pool:
        futures = {pool.submit(_one, c): c for c in chains}
        for fut in as_completed(futures):
            res = fut.result()
            by_key[res.chain.key] = res
    return [by_key[c.key] for c in chains]

"""Parallel multi-chain query runner."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from .chains import Chain
from .fetcher import Balance, FetchError, Fetcher, TokenBalance
from .tokens import for_chain


@dataclass
class ChainResult:
    chain: Chain
    balance: Balance | None
    error: str | None
    tokens: list[TokenBalance] = field(default_factory=list)
    token_errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.error is None


def query_all(
    address: str,
    chains: list[Chain],
    *,
    timeout: int = 10,
    include_tokens: bool = False,
) -> list[ChainResult]:
    """Hit every chain in parallel and return results in the same order as `chains`."""

    def _one(chain: Chain) -> ChainResult:
        f = Fetcher(chain, timeout=timeout)
        try:
            bal = f.balance(address)
        except FetchError as e:
            return ChainResult(chain=chain, balance=None, error=str(e))
        except Exception as e:
            return ChainResult(chain=chain, balance=None, error=f"{type(e).__name__}: {e}")

        toks: list[TokenBalance] = []
        tok_errs: list[str] = []
        if include_tokens:
            for t in for_chain(chain.key):
                try:
                    toks.append(f.token_balance(address, t))
                except FetchError as e:
                    tok_errs.append(str(e))
                except Exception as e:
                    tok_errs.append(f"{type(e).__name__}: {e}")

        return ChainResult(
            chain=chain, balance=bal, error=None, tokens=toks, token_errors=tok_errs
        )

    if not chains:
        return []

    by_key: dict[str, ChainResult] = {}
    with ThreadPoolExecutor(max_workers=min(8, len(chains))) as pool:
        futures = {pool.submit(_one, c): c for c in chains}
        for fut in as_completed(futures):
            res = fut.result()
            by_key[res.chain.key] = res
    return [by_key[c.key] for c in chains]

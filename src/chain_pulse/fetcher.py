"""Per-chain JSON-RPC client.

Thin wrapper over web3.py — we only need a handful of methods, so we don't drag
in the full Provider abstraction. Keeping it small also makes mocking trivial.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from web3 import HTTPProvider, Web3
from web3.exceptions import Web3Exception

from .chains import Chain

WEI_PER_ETH = Decimal(10**18)


class FetchError(RuntimeError):
    """Raised when an RPC call fails after retries."""


@dataclass(frozen=True)
class Balance:
    chain: str
    address: str
    wei: int
    symbol: str

    @property
    def eth(self) -> Decimal:
        return Decimal(self.wei) / WEI_PER_ETH


class Fetcher:
    """Stateless-ish RPC client bound to a single chain."""

    def __init__(self, chain: Chain, *, timeout: int = 10):
        self.chain = chain
        self._w3 = Web3(HTTPProvider(chain.rpc, request_kwargs={"timeout": timeout}))

    def balance(self, address: str) -> Balance:
        try:
            wei = self._w3.eth.get_balance(address)
        except Web3Exception as e:
            raise FetchError(f"{self.chain.key}: {e}") from e
        except Exception as e:  # network, json decode, etc.
            raise FetchError(f"{self.chain.key}: {type(e).__name__}: {e}") from e
        return Balance(
            chain=self.chain.key,
            address=address,
            wei=int(wei),
            symbol=self.chain.native_symbol,
        )

    def block_number(self) -> int:
        try:
            return int(self._w3.eth.block_number)
        except Exception as e:
            raise FetchError(f"{self.chain.key}: {type(e).__name__}: {e}") from e

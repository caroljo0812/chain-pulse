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
from .tokens import Token

WEI_PER_ETH = Decimal(10**18)

# Minimal ERC-20 ABI — we only need balanceOf for now.
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    }
]


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


@dataclass(frozen=True)
class TokenBalance:
    chain: str
    address: str
    token: Token
    raw: int

    @property
    def amount(self) -> Decimal:
        return Decimal(self.raw) / Decimal(10**self.token.decimals)


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

    def token_balance(self, address: str, token: Token) -> TokenBalance:
        try:
            c = self._w3.eth.contract(address=token.address, abi=ERC20_ABI)
            raw = c.functions.balanceOf(address).call()
        except Web3Exception as e:
            raise FetchError(f"{self.chain.key}/{token.symbol}: {e}") from e
        except Exception as e:
            raise FetchError(
                f"{self.chain.key}/{token.symbol}: {type(e).__name__}: {e}"
            ) from e
        return TokenBalance(chain=self.chain.key, address=address, token=token, raw=int(raw))

    def gas_price_gwei(self) -> Decimal:
        """Current gas price in gwei (eth_gasPrice)."""
        try:
            wei = self._w3.eth.gas_price
        except Web3Exception as e:
            raise FetchError(f"{self.chain.key}/gas: {e}") from e
        except Exception as e:
            raise FetchError(f"{self.chain.key}/gas: {type(e).__name__}: {e}") from e
        return Decimal(int(wei)) / Decimal(10**9)

    def block_number(self) -> int:
        try:
            return int(self._w3.eth.block_number)
        except Exception as e:
            raise FetchError(f"{self.chain.key}: {type(e).__name__}: {e}") from e

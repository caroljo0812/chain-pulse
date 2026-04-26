"""Curated ERC-20 token list per chain.

Small on purpose — this is a wallet inspector, not a token directory. Adding
USDC for each chain covers >80% of "did the bridge land?" questions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    chain: str
    symbol: str
    address: str  # checksum
    decimals: int


# Mainnet USDC contracts. Sepolia USDC is Circle's official testnet deployment.
TOKENS: dict[str, list[Token]] = {
    "sepolia": [
        Token("sepolia", "USDC", "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238", 6),
    ],
    "base": [
        Token("base", "USDC", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", 6),
    ],
    "arbitrum": [
        Token("arbitrum", "USDC", "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", 6),
    ],
    "optimism": [
        Token("optimism", "USDC", "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85", 6),
    ],
}


def for_chain(key: str) -> list[Token]:
    return TOKENS.get(key, [])

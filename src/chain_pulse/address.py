"""Address validation + checksum normalization."""

from __future__ import annotations

import re

from web3 import Web3

_HEX = re.compile(r"^0x[0-9a-fA-F]{40}$")


class InvalidAddress(ValueError):
    pass


def normalize(addr: str) -> str:
    """Validate and return a checksum-cased address.

    Raises InvalidAddress on bad input. Checksum is recomputed — input
    casing is not trusted, so a wallet that pasted a lowercase address still
    gets the canonical EIP-55 form.
    """
    if not isinstance(addr, str):
        raise InvalidAddress(f"address must be str, got {type(addr).__name__}")
    s = addr.strip()
    if not _HEX.match(s):
        raise InvalidAddress(f"not a 0x-prefixed 40-hex-char address: {s!r}")
    return Web3.to_checksum_address(s)

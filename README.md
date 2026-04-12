# chain-pulse

Quick multi-chain EVM wallet inspector. Point it at an address, get balances and recent activity across Sepolia, Base, Arbitrum, and Optimism in one shot.

Built this because flipping between four block explorers to track testnet wallets got old.

Status: early. Works on my machine.

## Install

```bash
git clone https://github.com/caroljo0812/chain-pulse.git
cd chain-pulse
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Quick start

```bash
# Single address, all default chains
chain-pulse 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

# Specific chains only
chain-pulse 0xd8dA... --chains sepolia,base

# Batch mode from file (one address per line)
chain-pulse --file wallets.txt

# JSON output for piping
chain-pulse 0xd8dA... --json
```

## Configuration

Override default RPC endpoints with a `.env` file (see `.env.example`):

```
SEPOLIA_RPC=https://ethereum-sepolia-rpc.publicnode.com
BASE_RPC=https://base-rpc.publicnode.com
ARBITRUM_RPC=https://arbitrum-one-rpc.publicnode.com
OPTIMISM_RPC=https://optimism-rpc.publicnode.com
```

Public RPCs work out of the box. Bring your own Alchemy/Infura keys for heavier usage.

## License

MIT

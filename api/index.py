"""Vercel serverless entry for chain-pulse dashboard.

Vercel's Python runtime expects a top-level `app` (FastAPI) or a `handler`
function in `api/<path>.py`. We import the FastAPI app from the package and
re-export it so `/api/index` resolves to the dashboard, then a vercel.json
rewrite maps every other path to `/api/index` so the SPA shell works.
"""
from chain_pulse.server import app  # noqa: F401  re-exported for Vercel runtime

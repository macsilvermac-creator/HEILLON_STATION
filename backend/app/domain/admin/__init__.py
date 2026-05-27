"""Admin endpoints — read-only metrics for monitoring beta + production.

Strictly limited to safe aggregate queries. NO PII exposure (no individual
prompts/responses). Authenticated via X-Heillon-Admin-Token env var (separate
from user JWT and API keys).
"""

"""Extension capture domain — Browser Extension (Chrome/Edge/Firefox) ingestion.

The browser extension observes user interactions with AI providers (ChatGPT,
Claude, Gemini, etc.) and POSTs structured captures to /api/v1/extension/capture.
Authentication is via X-Heillon-Api-Key header (long-lived API keys from
/api/v1/me/api-keys), not JWT (extension has no session cookie).

Each successful capture generates an HDR of type "analysis" with full
cryptographic chain of custody (SHA-256 of prompt+response, RFC3161 timestamp,
corpus normativo check).
"""

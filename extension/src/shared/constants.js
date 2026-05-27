/**
 * Heillon Extension — shared constants.
 *
 * Single source of truth for endpoints, storage keys, and defaults.
 */

export const DEFAULT_SERVER_URL = "http://127.0.0.1:8000";

export const STORAGE_KEYS = Object.freeze({
  apiKey:           "heillon_api_key",
  serverUrl:        "heillon_server_url",
  enabledProviders: "heillon_enabled_providers",
  lastQuota:        "heillon_last_quota",
  recentHdrs:       "heillon_recent_hdrs",   // ring buffer, last 20
  metrics:          "heillon_metrics",        // counts since install
});

export const DEFAULT_ENABLED_PROVIDERS = Object.freeze({
  openai:    true,
  anthropic: true,
  google:    true,
});

export const RECENT_HDR_BUFFER_SIZE = 20;

export const QUOTA_REFRESH_ALARM = "heillon_quota_refresh";
export const QUOTA_REFRESH_PERIOD_MIN = 15;

export const API_PATHS = Object.freeze({
  health:  "/api/v1/extension/health",
  capture: "/api/v1/extension/capture",
});

export const PROVIDER_BY_HOSTNAME = Object.freeze({
  "chat.openai.com":     "openai",
  "chatgpt.com":         "openai",
  "claude.ai":           "anthropic",
  "gemini.google.com":   "google",
});

export const EXTENSION_VERSION = "0.1.0";

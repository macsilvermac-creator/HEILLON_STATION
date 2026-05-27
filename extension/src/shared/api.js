/**
 * Heillon Extension — HTTP client for the Heillon backend.
 *
 * All collectors call into here so retry/error handling lives in one place.
 */

import { API_PATHS, EXTENSION_VERSION } from "./constants.js";
import { getApiKey, getServerUrl } from "./storage.js";

const CAPTURE_TIMEOUT_MS = 12_000;
const HEALTH_TIMEOUT_MS = 6_000;

class HeillonApiError extends Error {
  /**
   * @param {string} message
   * @param {number|null} status
   * @param {unknown} body
   */
  constructor(message, status, body) {
    super(message);
    this.name = "HeillonApiError";
    this.status = status;
    this.body = body;
  }
}

export { HeillonApiError };

async function _request(path, { method = "GET", body = null, timeoutMs = CAPTURE_TIMEOUT_MS } = {}) {
  const [apiKey, serverUrl] = await Promise.all([getApiKey(), getServerUrl()]);
  if (!apiKey) {
    throw new HeillonApiError("API key não configurada — abra Opções para configurar.", null, null);
  }

  const url = `${serverUrl.replace(/\/+$/, "")}${path}`;
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), timeoutMs);

  let response;
  try {
    response = await fetch(url, {
      method,
      headers: {
        "X-Heillon-Api-Key": apiKey,
        "Content-Type": "application/json",
        "X-Heillon-Extension-Version": EXTENSION_VERSION,
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: ctl.signal,
      credentials: "omit", // extension uses API key, not cookies
    });
  } catch (err) {
    clearTimeout(timer);
    if (err.name === "AbortError") {
      throw new HeillonApiError(`Timeout após ${timeoutMs}ms`, null, null);
    }
    throw new HeillonApiError(`Falha de rede: ${err.message}`, null, null);
  }
  clearTimeout(timer);

  let parsed = null;
  try {
    const text = await response.text();
    parsed = text ? JSON.parse(text) : null;
  } catch {
    parsed = null;
  }

  if (!response.ok) {
    const detail = parsed?.detail;
    const msg =
      typeof detail === "string" ? detail :
      detail?.message ? detail.message :
      `HTTP ${response.status}`;
    throw new HeillonApiError(msg, response.status, parsed);
  }

  return parsed;
}

/**
 * GET /api/v1/extension/health
 * @returns {Promise<{ok: true, organization_id: string, tier: string, quota: object, server_time: string, capture_endpoint: string}>}
 */
export async function fetchHealth() {
  return _request(API_PATHS.health, { method: "GET", timeoutMs: HEALTH_TIMEOUT_MS });
}

/**
 * POST /api/v1/extension/capture
 * @param {object} payload
 * @returns {Promise<{status: string, hdr_id: string, mission_id: string, verification_url: string, quota: object}>}
 */
export async function postCapture(payload) {
  return _request(API_PATHS.capture, { method: "POST", body: payload });
}

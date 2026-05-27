/**
 * Heillon Extension — chrome.storage.local async wrappers.
 *
 * Why local (not sync): API key is sensitive; sync replicates across all
 * signed-in Chrome instances. Local stays on this device only.
 */

import {
  STORAGE_KEYS,
  DEFAULT_ENABLED_PROVIDERS,
  DEFAULT_SERVER_URL,
  RECENT_HDR_BUFFER_SIZE,
} from "./constants.js";

/** @returns {Promise<string|null>} */
export async function getApiKey() {
  const r = await chrome.storage.local.get(STORAGE_KEYS.apiKey);
  return r[STORAGE_KEYS.apiKey] || null;
}

/** @param {string|null} key */
export async function setApiKey(key) {
  if (!key) {
    await chrome.storage.local.remove(STORAGE_KEYS.apiKey);
  } else {
    await chrome.storage.local.set({ [STORAGE_KEYS.apiKey]: key });
  }
}

/** @returns {Promise<string>} */
export async function getServerUrl() {
  const r = await chrome.storage.local.get(STORAGE_KEYS.serverUrl);
  return r[STORAGE_KEYS.serverUrl] || DEFAULT_SERVER_URL;
}

/** @param {string} url */
export async function setServerUrl(url) {
  await chrome.storage.local.set({ [STORAGE_KEYS.serverUrl]: url.trim() });
}

/** @returns {Promise<Record<string, boolean>>} */
export async function getEnabledProviders() {
  const r = await chrome.storage.local.get(STORAGE_KEYS.enabledProviders);
  return { ...DEFAULT_ENABLED_PROVIDERS, ...(r[STORAGE_KEYS.enabledProviders] || {}) };
}

/** @param {Record<string, boolean>} providers */
export async function setEnabledProviders(providers) {
  await chrome.storage.local.set({ [STORAGE_KEYS.enabledProviders]: providers });
}

/**
 * @typedef QuotaSnapshot
 * @property {number} used
 * @property {number|null} limit
 * @property {number|null} remaining
 * @property {string} tier
 */

/** @returns {Promise<QuotaSnapshot|null>} */
export async function getLastQuota() {
  const r = await chrome.storage.local.get(STORAGE_KEYS.lastQuota);
  return r[STORAGE_KEYS.lastQuota] || null;
}

/** @param {QuotaSnapshot} snapshot */
export async function setLastQuota(snapshot) {
  await chrome.storage.local.set({ [STORAGE_KEYS.lastQuota]: snapshot });
}

/**
 * @typedef RecentHdr
 * @property {string} hdr_id
 * @property {string} mission_id
 * @property {string} verification_url
 * @property {string} provider
 * @property {string} model
 * @property {string} captured_at
 */

/** @returns {Promise<RecentHdr[]>} */
export async function getRecentHdrs() {
  const r = await chrome.storage.local.get(STORAGE_KEYS.recentHdrs);
  return r[STORAGE_KEYS.recentHdrs] || [];
}

/** @param {RecentHdr} entry */
export async function pushRecentHdr(entry) {
  const list = await getRecentHdrs();
  list.unshift(entry);
  list.length = Math.min(list.length, RECENT_HDR_BUFFER_SIZE);
  await chrome.storage.local.set({ [STORAGE_KEYS.recentHdrs]: list });
}

/**
 * @typedef Metrics
 * @property {number} captured_total
 * @property {number} captured_today
 * @property {number} errors
 * @property {string|null} last_capture_at
 * @property {string|null} last_error_at
 * @property {string|null} last_error_message
 */

/** @returns {Promise<Metrics>} */
export async function getMetrics() {
  const r = await chrome.storage.local.get(STORAGE_KEYS.metrics);
  return r[STORAGE_KEYS.metrics] || {
    captured_total: 0,
    captured_today: 0,
    errors: 0,
    last_capture_at: null,
    last_error_at: null,
    last_error_message: null,
  };
}

export async function incrementCaptureMetric() {
  const m = await getMetrics();
  const now = new Date();
  const today = now.toISOString().slice(0, 10);
  const lastDay = (m.last_capture_at || "").slice(0, 10);
  m.captured_total += 1;
  m.captured_today = lastDay === today ? m.captured_today + 1 : 1;
  m.last_capture_at = now.toISOString();
  await chrome.storage.local.set({ [STORAGE_KEYS.metrics]: m });
}

/** @param {string} message */
export async function recordError(message) {
  const m = await getMetrics();
  m.errors += 1;
  m.last_error_at = new Date().toISOString();
  m.last_error_message = String(message).slice(0, 200);
  await chrome.storage.local.set({ [STORAGE_KEYS.metrics]: m });
}

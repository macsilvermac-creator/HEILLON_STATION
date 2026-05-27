/**
 * Heillon Extension — background service worker (MV3).
 *
 * Responsibilities:
 *  1. Receive `capture` messages from content scripts and POST to backend
 *  2. Maintain a cached quota snapshot (refreshed via chrome.alarms every 15min)
 *  3. Update extension badge with usage indicator
 *  4. Handle errors centrally and surface them via metrics
 */

import { fetchHealth, postCapture, HeillonApiError } from "../shared/api.js";
import {
  QUOTA_REFRESH_ALARM,
  QUOTA_REFRESH_PERIOD_MIN,
  PROVIDER_BY_HOSTNAME,
  EXTENSION_VERSION,
} from "../shared/constants.js";
import {
  getApiKey,
  getEnabledProviders,
  incrementCaptureMetric,
  pushRecentHdr,
  recordError,
  setLastQuota,
} from "../shared/storage.js";

// ── Badge management ──────────────────────────────────────────────────────────

const BADGE_COLORS = {
  ok:        "#4ade80",  // emerald-400
  warn:      "#facc15",  // yellow-400
  exceeded:  "#ef4444",  // red-500
  unauth:    "#9ca3af",  // gray-400
};

async function updateBadge(quota) {
  if (!quota) {
    await chrome.action.setBadgeText({ text: "?" });
    await chrome.action.setBadgeBackgroundColor({ color: BADGE_COLORS.unauth });
    return;
  }
  if (quota.limit === null) {
    // Unlimited — no badge clutter
    await chrome.action.setBadgeText({ text: "" });
    return;
  }
  const remaining = quota.remaining ?? 0;
  const text = remaining > 99 ? "99+" : String(remaining);
  const color =
    remaining === 0 ? BADGE_COLORS.exceeded :
    remaining < 10  ? BADGE_COLORS.warn :
    BADGE_COLORS.ok;
  await chrome.action.setBadgeText({ text });
  await chrome.action.setBadgeBackgroundColor({ color });
}

// ── Health / quota refresh ────────────────────────────────────────────────────

async function refreshQuota() {
  try {
    const apiKey = await getApiKey();
    if (!apiKey) {
      await updateBadge(null);
      return;
    }
    const health = await fetchHealth();
    await setLastQuota(health.quota);
    await updateBadge(health.quota);
  } catch (err) {
    await recordError(err.message);
    await updateBadge(null);
  }
}

chrome.runtime.onInstalled.addListener(async () => {
  await chrome.alarms.create(QUOTA_REFRESH_ALARM, {
    periodInMinutes: QUOTA_REFRESH_PERIOD_MIN,
    delayInMinutes: 0.1,
  });
  await refreshQuota();
});

chrome.runtime.onStartup.addListener(refreshQuota);

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === QUOTA_REFRESH_ALARM) refreshQuota();
});

// ── Capture handler ───────────────────────────────────────────────────────────

/**
 * @typedef CaptureMessage
 * @property {"capture"} type
 * @property {string} prompt
 * @property {string} response
 * @property {string} model
 * @property {string} source_url
 * @property {string|null} ai_session_id
 * @property {string|null} page_title
 */

/**
 * Build the API payload from a content-script capture message.
 * Provider is inferred from the source URL hostname.
 */
function buildPayload(msg) {
  let provider = "other";
  try {
    const host = new URL(msg.source_url).hostname;
    provider = PROVIDER_BY_HOSTNAME[host] || "other";
  } catch {
    // keep "other"
  }
  return {
    provider,
    model: msg.model || "unknown",
    prompt: msg.prompt,
    response: msg.response,
    source_url: msg.source_url,
    captured_at: new Date().toISOString(),
    ai_session_id: msg.ai_session_id || null,
    extension_version: EXTENSION_VERSION,
    page_title: msg.page_title || null,
  };
}

/**
 * Per-provider opt-in gate. If user disabled this provider in Options,
 * we silently drop the capture (returning {skipped: true}).
 */
async function isProviderEnabled(provider) {
  const enabled = await getEnabledProviders();
  return enabled[provider] !== false;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || message.type !== "capture") return false;

  // Async handler — return true to keep the response channel open
  (async () => {
    try {
      const payload = buildPayload(message);

      if (!(await isProviderEnabled(payload.provider))) {
        sendResponse({ ok: false, skipped: true, reason: "provider_disabled" });
        return;
      }

      const result = await postCapture(payload);
      await Promise.all([
        incrementCaptureMetric(),
        setLastQuota(result.quota),
        pushRecentHdr({
          hdr_id: result.hdr_id,
          mission_id: result.mission_id,
          verification_url: result.verification_url,
          provider: payload.provider,
          model: payload.model,
          captured_at: payload.captured_at,
        }),
      ]);
      await updateBadge(result.quota);

      sendResponse({
        ok: true,
        hdr_id: result.hdr_id,
        mission_id: result.mission_id,
        verification_url: result.verification_url,
        quota: result.quota,
      });
    } catch (err) {
      const apiErr = err instanceof HeillonApiError ? err : null;
      const status = apiErr?.status ?? null;
      await recordError(err.message);
      sendResponse({
        ok: false,
        error: err.message,
        status,
        quota_exceeded: status === 402,
        unauthorized: status === 401,
      });
    }
  })();
  return true;
});

// Listen for options/popup changes that should trigger immediate badge refresh
chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName !== "local") return;
  if (changes.heillon_api_key || changes.heillon_server_url) {
    refreshQuota();
  }
});

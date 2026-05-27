/**
 * Heillon Options page — manage API key, server URL, opt-in providers.
 */

import { fetchHealth, HeillonApiError } from "../shared/api.js";
import {
  DEFAULT_ENABLED_PROVIDERS,
  DEFAULT_SERVER_URL,
} from "../shared/constants.js";
import {
  getApiKey,
  getEnabledProviders,
  getMetrics,
  getServerUrl,
  setApiKey,
  setEnabledProviders,
  setServerUrl,
} from "../shared/storage.js";

const TIER_LABEL = {
  free: "Free",
  pro: "Pro",
  team: "Team",
  enterprise: "Enterprise",
};

function setConnectionStatus(message, variant) {
  const el = document.getElementById("connection-status");
  el.textContent = message;
  el.className = `status ${variant || ""}`;
}

async function loadInitial() {
  const [serverUrl, apiKey, providers, metrics] = await Promise.all([
    getServerUrl(),
    getApiKey(),
    getEnabledProviders(),
    getMetrics(),
  ]);

  document.getElementById("server-url").value = serverUrl || DEFAULT_SERVER_URL;
  document.getElementById("api-key").value = apiKey || "";
  document.getElementById("opt-openai").checked = providers.openai !== false;
  document.getElementById("opt-anthropic").checked = providers.anthropic !== false;
  document.getElementById("opt-google").checked = providers.google !== false;

  // Stats
  document.getElementById("metric-total").textContent = String(metrics.captured_total);
  document.getElementById("metric-today").textContent = String(metrics.captured_today);
  document.getElementById("metric-errors").textContent = String(metrics.errors);
  if (metrics.last_error_message) {
    document.getElementById("metric-last-error").textContent =
      `Último erro: ${metrics.last_error_message}`;
  }

  // Console links
  const baseUrl = (serverUrl || DEFAULT_SERVER_URL).replace(/\/+$/, "");
  // Convention: marketing/console site is on the same origin as the API
  // Most installations will use a separate frontend URL; users can override.
  document.getElementById("link-keys").href = `${baseUrl}/conta/api-keys`;
  document.getElementById("link-quota").href = `${baseUrl}/conta/quota`;
}

async function saveAndTest() {
  const btn = document.getElementById("save-connection");
  btn.disabled = true;
  setConnectionStatus("Salvando e testando…", "");

  const serverUrl = document.getElementById("server-url").value.trim();
  const apiKey = document.getElementById("api-key").value.trim();

  if (!serverUrl || !/^https?:\/\//.test(serverUrl)) {
    setConnectionStatus("URL inválida — use http(s)://…", "error");
    btn.disabled = false;
    return;
  }
  if (apiKey && !apiKey.startsWith("heillon_live_")) {
    setConnectionStatus("Chave deve começar com heillon_live_", "error");
    btn.disabled = false;
    return;
  }

  await setServerUrl(serverUrl);
  await setApiKey(apiKey || null);

  if (!apiKey) {
    setConnectionStatus("URL salva. Adicione uma chave para começar.", "warn");
    btn.disabled = false;
    return;
  }

  try {
    const health = await fetchHealth();
    const tier = TIER_LABEL[health.tier] || health.tier;
    const usedTxt = health.quota.limit === null
      ? `${health.quota.used} HDRs (ilimitado)`
      : `${health.quota.used}/${health.quota.limit} HDRs este mês`;
    setConnectionStatus(`Conectado · plano ${tier} · ${usedTxt}`, "ok");
  } catch (err) {
    if (err instanceof HeillonApiError && err.status === 401) {
      setConnectionStatus("Chave inválida — verifique no console.", "error");
    } else {
      setConnectionStatus(`Erro: ${err.message}`, "error");
    }
  } finally {
    btn.disabled = false;
  }
}

async function saveProviders() {
  const providers = {
    openai: document.getElementById("opt-openai").checked,
    anthropic: document.getElementById("opt-anthropic").checked,
    google: document.getElementById("opt-google").checked,
  };
  await setEnabledProviders(providers);
}

document.addEventListener("DOMContentLoaded", async () => {
  await loadInitial();
  document.getElementById("save-connection").addEventListener("click", saveAndTest);
  document.getElementById("opt-openai").addEventListener("change", saveProviders);
  document.getElementById("opt-anthropic").addEventListener("change", saveProviders);
  document.getElementById("opt-google").addEventListener("change", saveProviders);
});

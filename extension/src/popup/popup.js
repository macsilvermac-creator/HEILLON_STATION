/**
 * Heillon popup — renders status, quota, last 5 HDRs.
 *
 * Reads from chrome.storage.local (populated by sw.js background refresh)
 * for instant display, then triggers a fresh refresh via message to SW.
 */

import { fetchHealth, HeillonApiError } from "../shared/api.js";
import { getApiKey, getLastQuota, getRecentHdrs, getServerUrl, setLastQuota } from "../shared/storage.js";

const TIER_LABEL = {
  free: "Free",
  pro: "Pro",
  team: "Team",
  enterprise: "Enterprise",
};

function setStatus(message, variant = "ok") {
  const section = document.getElementById("status");
  const msg = document.getElementById("status-message");
  section.className = `status ${variant}`;
  msg.textContent = message;
}

function renderQuota(quota) {
  const card = document.getElementById("quota-card");
  if (!quota) {
    card.classList.add("hidden");
    return;
  }
  card.classList.remove("hidden");
  document.getElementById("tier-value").textContent = TIER_LABEL[quota.tier] || quota.tier;
  document.getElementById("quota-used").textContent = String(quota.used);
  document.getElementById("quota-limit").textContent =
    quota.limit === null ? "∞" : String(quota.limit);

  const bar = document.getElementById("progress-bar");
  if (quota.limit === null) {
    bar.style.width = "100%";
    bar.className = "progress-bar";
  } else {
    const pct = Math.min((quota.used / Math.max(quota.limit, 1)) * 100, 100);
    bar.style.width = `${pct}%`;
    bar.className = `progress-bar${pct >= 100 ? " exceeded" : pct >= 70 ? " warn" : ""}`;
  }
}

function renderRecent(list) {
  const ul = document.getElementById("recent-list");
  ul.innerHTML = "";
  if (!list || list.length === 0) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "Nenhum registo ainda. Use ChatGPT, Claude ou Gemini para começar.";
    ul.appendChild(li);
    return;
  }
  for (const entry of list.slice(0, 5)) {
    const li = document.createElement("li");
    li.className = "entry";

    const meta = document.createElement("span");
    meta.className = "meta";
    const date = new Date(entry.captured_at).toLocaleString("pt-BR", {
      day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
    });
    meta.textContent = `${entry.provider} · ${entry.model} · ${date}`;

    const link = document.createElement("a");
    link.href = entry.verification_url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = `HDR ${entry.hdr_id.slice(0, 12)}…`;

    li.appendChild(meta);
    li.appendChild(link);
    ul.appendChild(li);
  }
}

async function initConsoleLink() {
  const serverUrl = await getServerUrl();
  document.getElementById("open-console").href = `${serverUrl.replace(/\/+$/, "")}/conta/quota`;
}

async function refresh() {
  setStatus("Sincronizando…");
  const apiKey = await getApiKey();
  if (!apiKey) {
    setStatus("Sem API key — abra Opções para configurar.", "warn");
    return;
  }
  try {
    const health = await fetchHealth();
    await setLastQuota(health.quota);
    renderQuota(health.quota);
    setStatus(`Conectado · org ${health.organization_id}`, "ok");
  } catch (err) {
    if (err instanceof HeillonApiError && err.status === 401) {
      setStatus("API key inválida — abra Opções.", "error");
    } else {
      setStatus(`Falha: ${err.message}`, "error");
    }
  }
}

async function init() {
  await initConsoleLink();

  // Optimistic render from cached snapshot
  const [cached, recents] = await Promise.all([getLastQuota(), getRecentHdrs()]);
  if (cached) renderQuota(cached);
  renderRecent(recents);

  document.getElementById("refresh").addEventListener("click", refresh);
  document.getElementById("open-options").addEventListener("click", () => {
    chrome.runtime.openOptionsPage();
  });

  await refresh();
}

document.addEventListener("DOMContentLoaded", init);

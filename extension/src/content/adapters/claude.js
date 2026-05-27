/**
 * Heillon adapter — Claude (claude.ai).
 *
 * Claude renders user messages and assistant responses inside the chat
 * container with distinct DOM markers. We detect each pair and emit a
 * capture when the response is no longer being typed.
 */

(function () {
  if (window.__HEILLON_CLAUDE_ADAPTER) return;
  window.__HEILLON_CLAUDE_ADAPTER = true;

  const STABILITY_DEBOUNCE_MS = 1800;
  const MIN_CHARS = 4;
  const PROCESSED_ATTR = "data-heillon-processed";

  /** Session ID = path /chat/<uuid> */
  function getSessionId() {
    const m = location.pathname.match(/\/chat\/([0-9a-f-]+)/i);
    return m ? m[1] : null;
  }

  function getModelName() {
    // Claude shows model name in the topbar selector
    const selectors = [
      '[data-testid="model-selector"]',
      '[data-testid="model-selector-dropdown"]',
      'button[aria-label*="model" i]',
    ];
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      const text = el?.textContent?.trim();
      if (text && text.length > 0 && text.length < 60) return text;
    }
    return "claude-unknown";
  }

  /** Selector for user prompts (Claude uses data-testid="user-message"). */
  function getMessagePairs() {
    const userNodes = Array.from(document.querySelectorAll('[data-testid="user-message"]'));
    const pairs = [];
    for (const userNode of userNodes) {
      // Assistant response is the next sibling .group element (Claude convention)
      // We walk forward in DOM order to find the next [data-is-streaming] or .font-claude-response
      let next = userNode.parentElement?.nextElementSibling;
      while (next && !next.querySelector('.font-claude-response, [data-is-streaming]')) {
        next = next.nextElementSibling;
      }
      const assistantNode = next?.querySelector('.font-claude-response') || next;
      if (assistantNode) {
        pairs.push({ user: userNode, assistant: assistantNode });
      }
    }
    return pairs;
  }

  function getTextOf(node) {
    if (!node) return "";
    return (node.innerText || node.textContent || "").trim();
  }

  function isStillStreaming(assistantNode) {
    if (!assistantNode) return true;
    if (assistantNode.querySelector('[data-is-streaming="true"]')) return true;
    if (assistantNode.getAttribute("data-is-streaming") === "true") return true;
    return false;
  }

  function scanAndCapture() {
    for (const { user, assistant } of getMessagePairs()) {
      if (assistant.hasAttribute(PROCESSED_ATTR)) continue;
      if (isStillStreaming(assistant)) continue;
      const promptText = getTextOf(user);
      const responseText = getTextOf(assistant);
      if (promptText.length < MIN_CHARS || responseText.length < MIN_CHARS) continue;

      assistant.setAttribute(PROCESSED_ATTR, "1");
      sendCapture({
        prompt: promptText,
        response: responseText,
        ai_session_id: getSessionId(),
        model: getModelName(),
        source_url: location.href,
        page_title: document.title,
      });
    }
  }

  function sendCapture(payload) {
    chrome.runtime.sendMessage(
      { type: "capture", ...payload },
      (resp) => {
        if (chrome.runtime.lastError || !resp) {
          window.__HEILLON_NOTIFY?.({
            variant: "error",
            message: "Heillon: falha ao registar (sem ligação ao backend?)",
          });
          return;
        }
        if (resp.skipped) return;
        if (resp.ok) {
          window.__HEILLON_NOTIFY?.({
            variant: "success", message: "Auditado", link: resp.verification_url,
          });
        } else if (resp.unauthorized) {
          window.__HEILLON_NOTIFY?.({ variant: "error", message: "Heillon: API key inválida — abra Opções." });
        } else if (resp.quota_exceeded) {
          window.__HEILLON_NOTIFY?.({ variant: "warning", message: "Heillon: limite mensal atingido — faça upgrade.", durationMs: 7000 });
        } else {
          window.__HEILLON_NOTIFY?.({ variant: "error", message: `Heillon: ${resp.error || "erro desconhecido"}` });
        }
      }
    );
  }

  let timer = null;
  function schedule() {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => { timer = null; scanAndCapture(); }, STABILITY_DEBOUNCE_MS);
  }

  const observer = new MutationObserver(schedule);
  function attach() {
    const root = document.querySelector('[class*="main"]') || document.body;
    observer.observe(root, { childList: true, subtree: true, characterData: true });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attach, { once: true });
  } else {
    attach();
  }
})();

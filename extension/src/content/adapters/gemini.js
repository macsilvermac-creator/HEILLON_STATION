/**
 * Heillon adapter — Gemini (gemini.google.com).
 *
 * Gemini wraps each conversation turn in a <user-query> for prompts and
 * <model-response> for responses. We pair them in DOM order and capture when
 * the response element has stopped mutating.
 */

(function () {
  if (window.__HEILLON_GEMINI_ADAPTER) return;
  window.__HEILLON_GEMINI_ADAPTER = true;

  const STABILITY_DEBOUNCE_MS = 1800;
  const MIN_CHARS = 4;
  const PROCESSED_ATTR = "data-heillon-processed";

  function getSessionId() {
    // Gemini URLs include the conversation ID after /app/
    const m = location.pathname.match(/\/app\/([a-z0-9-]+)/i);
    return m ? m[1] : null;
  }

  function getModelName() {
    // Gemini header shows the model name (e.g. "2.5 Pro")
    const el = document.querySelector('[class*="model-selector"], [data-test-id="model-selector"]');
    const text = el?.textContent?.trim();
    return text && text.length < 60 ? `gemini-${text.replace(/\s+/g, "-").toLowerCase()}` : "gemini-unknown";
  }

  function getPairs() {
    const userTurns = Array.from(document.querySelectorAll('user-query'));
    const modelTurns = Array.from(document.querySelectorAll('model-response'));
    const pairs = [];
    const len = Math.min(userTurns.length, modelTurns.length);
    for (let i = 0; i < len; i++) {
      pairs.push({ user: userTurns[i], assistant: modelTurns[i] });
    }
    return pairs;
  }

  function getTextOf(node) {
    if (!node) return "";
    return (node.innerText || node.textContent || "").trim();
  }

  function isStillStreaming(modelNode) {
    if (!modelNode) return true;
    // Gemini exposes a `data-is-loading` or has the loading spinner inside
    if (modelNode.querySelector('[data-loading="true"], [class*="loading"]')) return true;
    if (modelNode.getAttribute("data-loading") === "true") return true;
    return false;
  }

  function scanAndCapture() {
    for (const { user, assistant } of getPairs()) {
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
    chrome.runtime.sendMessage({ type: "capture", ...payload }, (resp) => {
      if (chrome.runtime.lastError || !resp) {
        window.__HEILLON_NOTIFY?.({ variant: "error", message: "Heillon: falha ao registar (sem ligação ao backend?)" });
        return;
      }
      if (resp.skipped) return;
      if (resp.ok) {
        window.__HEILLON_NOTIFY?.({ variant: "success", message: "Auditado", link: resp.verification_url });
      } else if (resp.unauthorized) {
        window.__HEILLON_NOTIFY?.({ variant: "error", message: "Heillon: API key inválida — abra Opções." });
      } else if (resp.quota_exceeded) {
        window.__HEILLON_NOTIFY?.({ variant: "warning", message: "Heillon: limite mensal atingido — faça upgrade.", durationMs: 7000 });
      } else {
        window.__HEILLON_NOTIFY?.({ variant: "error", message: `Heillon: ${resp.error || "erro desconhecido"}` });
      }
    });
  }

  let timer = null;
  function schedule() {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => { timer = null; scanAndCapture(); }, STABILITY_DEBOUNCE_MS);
  }

  const observer = new MutationObserver(schedule);
  function attach() {
    const root = document.querySelector('chat-window, main') || document.body;
    observer.observe(root, { childList: true, subtree: true, characterData: true });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attach, { once: true });
  } else {
    attach();
  }
})();

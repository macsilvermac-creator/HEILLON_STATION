/**
 * Heillon adapter — ChatGPT (chat.openai.com, chatgpt.com).
 *
 * Strategy: MutationObserver watches the conversation container. We pair each
 * user message with the next assistant message (one capture per Q→A pair) and
 * post to the background SW once the assistant's response finishes streaming.
 *
 * Streaming detection: an assistant message is "done" when its
 * `data-message-streaming` attribute disappears (current selector). We also
 * debounce by 1.5s of DOM-stability as a safety net for layout changes.
 */

(function () {
  if (window.__HEILLON_CHATGPT_ADAPTER) return;
  window.__HEILLON_CHATGPT_ADAPTER = true;

  const STABILITY_DEBOUNCE_MS = 1500;
  const MIN_RESPONSE_CHARS = 4;     // skip empty responses
  const MIN_PROMPT_CHARS = 1;
  const PROCESSED_ATTR = "data-heillon-processed";

  /** Extract session id from URL: /c/<uuid> */
  function getSessionId() {
    const m = location.pathname.match(/\/c\/([0-9a-f-]+)/i);
    return m ? m[1] : null;
  }

  /** Extract model name from page if available (best-effort). */
  function getModelName() {
    // The model selector in ChatGPT exposes it in different places over time;
    // we try a few selectors then fall back to "gpt-unknown".
    const selectors = [
      '[data-testid="model-switcher-dropdown-button"]',
      '[aria-label*="Model" i]',
      'button[id*="model"]',
    ];
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      const text = el?.textContent?.trim();
      if (text && text.length > 0 && text.length < 60) return text;
    }
    return "gpt-unknown";
  }

  /** All articles in conversation order. ChatGPT marks each turn with data-message-author-role. */
  function getMessageNodes() {
    return Array.from(document.querySelectorAll('[data-message-author-role]'));
  }

  /** Extract plain text from a message node, ignoring code-fence chrome. */
  function getTextOf(node) {
    if (!node) return "";
    return (node.innerText || node.textContent || "").trim();
  }

  /** Pair user msg N with assistant msg N+1; emit when assistant is no longer streaming. */
  function scanAndCapture() {
    const messages = getMessageNodes();
    for (let i = 0; i < messages.length - 1; i++) {
      const user = messages[i];
      const assistant = messages[i + 1];
      if (user.getAttribute("data-message-author-role") !== "user") continue;
      if (assistant.getAttribute("data-message-author-role") !== "assistant") continue;
      if (assistant.hasAttribute(PROCESSED_ATTR)) continue;

      const stillStreaming = assistant.querySelector('[data-message-streaming="true"]')
        || assistant.getAttribute("data-message-streaming") === "true";
      if (stillStreaming) continue;

      const promptText = getTextOf(user);
      const responseText = getTextOf(assistant);
      if (promptText.length < MIN_PROMPT_CHARS) continue;
      if (responseText.length < MIN_RESPONSE_CHARS) continue;

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
        if (resp.skipped) {
          return; // provider disabled — silent
        }
        if (resp.ok) {
          window.__HEILLON_NOTIFY?.({
            variant: "success",
            message: "Auditado",
            link: resp.verification_url,
          });
        } else if (resp.unauthorized) {
          window.__HEILLON_NOTIFY?.({
            variant: "error",
            message: "Heillon: API key inválida — abra Opções da extensão.",
          });
        } else if (resp.quota_exceeded) {
          window.__HEILLON_NOTIFY?.({
            variant: "warning",
            message: "Heillon: limite mensal atingido — faça upgrade.",
            durationMs: 7000,
          });
        } else {
          window.__HEILLON_NOTIFY?.({
            variant: "error",
            message: `Heillon: ${resp.error || "erro desconhecido"}`,
          });
        }
      }
    );
  }

  // Debounced observer: triggers a scan only after the DOM has been quiet
  // for STABILITY_DEBOUNCE_MS, which catches the end-of-stream consistently.
  let timer = null;
  function schedule() {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      timer = null;
      scanAndCapture();
    }, STABILITY_DEBOUNCE_MS);
  }

  const observer = new MutationObserver(schedule);
  function attach() {
    // ChatGPT's main container changes over time; observe body as fallback
    const root = document.querySelector("main") || document.body;
    observer.observe(root, { childList: true, subtree: true, characterData: true });
  }

  // Defer attach until DOM is interactive enough
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attach, { once: true });
  } else {
    attach();
  }
})();

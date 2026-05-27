/**
 * Heillon Extension — non-intrusive toast notifier (content script, top file).
 *
 * Loaded BEFORE adapter scripts so they can call window.__HEILLON_NOTIFY().
 * Renders a small fixed-position chip in the bottom-right corner that fades
 * out after a few seconds. Uses Shadow DOM to avoid CSS collisions with the
 * host site (ChatGPT, Claude, Gemini all have aggressive global styles).
 */

(function () {
  // Idempotent guard: avoid double-injection on SPA navigation
  if (window.__HEILLON_NOTIFIER_LOADED) return;
  window.__HEILLON_NOTIFIER_LOADED = true;

  let shadowRoot = null;

  function ensureShadow() {
    if (shadowRoot) return shadowRoot;
    const host = document.createElement("div");
    host.id = "heillon-notifier-host";
    host.style.cssText = "all: initial; position: fixed; z-index: 2147483647; bottom: 16px; right: 16px;";
    document.documentElement.appendChild(host);
    shadowRoot = host.attachShadow({ mode: "closed" });

    const style = document.createElement("style");
    style.textContent = `
      :host, .toast {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, system-ui, sans-serif;
      }
      .toast {
        display: flex; align-items: center; gap: 10px;
        background: rgba(15, 23, 41, 0.96); color: #f4f4f5;
        border: 1px solid rgba(212, 175, 55, 0.4);
        border-radius: 10px;
        padding: 10px 14px;
        font-size: 13px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        max-width: 320px;
        opacity: 0; transform: translateY(8px);
        transition: opacity 220ms ease, transform 220ms ease;
        pointer-events: auto;
      }
      .toast.visible { opacity: 1; transform: translateY(0); }
      .toast.success { border-color: rgba(74, 222, 128, 0.45); }
      .toast.warning { border-color: rgba(250, 204, 21, 0.5); }
      .toast.error   { border-color: rgba(239, 68, 68, 0.55); background: rgba(60, 12, 12, 0.94); }
      .icon { font-size: 14px; line-height: 1; flex-shrink: 0; }
      .body { line-height: 1.35; }
      a { color: #fbbf24; text-decoration: underline; text-underline-offset: 2px; }
      .close { all: unset; cursor: pointer; opacity: 0.45; padding: 4px; line-height: 1; }
      .close:hover { opacity: 0.95; }
    `;
    shadowRoot.appendChild(style);
    return shadowRoot;
  }

  /**
   * @param {Object} opts
   * @param {string} opts.message - HTML-safe message (will be rendered as text)
   * @param {"success"|"warning"|"error"} [opts.variant]
   * @param {string} [opts.link] - optional URL shown as "Ver registo"
   * @param {number} [opts.durationMs] - default 4500
   */
  function notify({ message, variant = "success", link, durationMs = 4500 }) {
    const root = ensureShadow();
    const toast = document.createElement("div");
    toast.className = `toast ${variant}`;

    const icon = document.createElement("span");
    icon.className = "icon";
    icon.textContent = variant === "success" ? "✓" : variant === "warning" ? "!" : "✕";

    const body = document.createElement("span");
    body.className = "body";
    body.textContent = message;

    if (link) {
      body.appendChild(document.createTextNode(" "));
      const a = document.createElement("a");
      a.href = link;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = "Ver registo →";
      body.appendChild(a);
    }

    const closeBtn = document.createElement("button");
    closeBtn.className = "close";
    closeBtn.setAttribute("aria-label", "Fechar");
    closeBtn.textContent = "×";
    closeBtn.addEventListener("click", () => toast.remove());

    toast.appendChild(icon);
    toast.appendChild(body);
    toast.appendChild(closeBtn);
    root.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => toast.classList.add("visible"));

    // Auto-dismiss
    setTimeout(() => {
      toast.classList.remove("visible");
      setTimeout(() => toast.remove(), 300);
    }, durationMs);
  }

  window.__HEILLON_NOTIFY = notify;
})();

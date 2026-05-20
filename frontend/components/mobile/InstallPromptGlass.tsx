"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

const KEY = "heillon_pwa_install_seen";

export function InstallPromptGlass() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.matchMedia("(display-mode: standalone)").matches) return;

    const n = Number.parseInt(window.localStorage.getItem(KEY) || "0", 10) || 0;
    const next = n + 1;
    window.localStorage.setItem(KEY, String(next));
    if (next >= 3) {
      const dismissed = window.sessionStorage.getItem("heillon_pwa_prompt_dismissed");
      if (!dismissed) setVisible(true);
    }
  }, []);

  return (
    <AnimatePresence>
      {visible ? (
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[190] flex items-end justify-center bg-black/42 p-6 backdrop-blur-sm sm:items-center"
        >
          <div className="glass-elite w-full max-w-sm rounded-[1.75rem] p-6 text-center shadow-2xl">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gold-500 text-lg font-black text-deep-space-900">
              H
            </div>
            <h3 className="text-lg font-semibold text-white">Instalar Heillon Legal</h3>
            <p className="mt-2 text-sm text-white/50">Adicionar ao ecrã inicial para modo standalone e uso em campo.</p>
            <div className="mt-6 grid gap-2">
              <button type="button" className="btn-gold min-h-[48px]" onClick={() => setVisible(false)}>
                Entendido · usar menu «Adicionar ao ecrã»
              </button>
              <button
                type="button"
                className="text-[11px] text-white/40 underline"
                onClick={() => {
                  window.sessionStorage.setItem("heillon_pwa_prompt_dismissed", "1");
                  setVisible(false);
                }}
              >
                Agora não
              </button>
            </div>
          </div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

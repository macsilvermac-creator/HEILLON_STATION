"use client";

import { useEffect } from "react";

import { registerPushSubscriptionOnServer } from "@/lib/notifications";

/** Pedido de permissões + opcional eco para backend (subscription JSON quando Web Push disponível). */
export function PushNotificationManager() {
  useEffect(() => {
    if (typeof window === "undefined" || typeof Notification === "undefined") return;

    const run = async () => {
      if (Notification.permission !== "default") return;
      /* Não obrigar prompt automático — reservado ao perfil quando activar toggle */
      void Promise.resolve(null);
    };
    run();
  }, []);

  async function subscribe() {
    const perm = await Notification.requestPermission();
    if (perm !== "granted") return;

    try {
      new Notification("Heillon Legal", {
        body: "Canal preparado para alertas de missão (MVP)",
        silent: false,
      });
    } catch {
      /* Alguns navegadores bloqueiam fora SW */
    }

    await registerPushSubscriptionOnServer();
  }

  return (
    <div className="mt-10 rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3">
      <p className="text-xs text-white/50">Alertas remotos · Web Push requer HTTPS + VAPID no servidor nas próximas iterações.</p>
      <button type="button" className="btn-glass mt-3 min-h-[48px] w-full text-xs" onClick={subscribe}>
        Activar permissões nativas / testar alerta local
      </button>
    </div>
  );
}

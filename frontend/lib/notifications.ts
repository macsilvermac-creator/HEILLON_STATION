"use client";

import { registerPushTokenJson } from "@/lib/api";

/**
 * Persiste envelope push MVP — servidor aceita JSON arbitrário válido até VAPID.
 */
export async function registerPushSubscriptionOnServer(): Promise<boolean> {
  try {
    await registerPushTokenJson(
      JSON.stringify({
        awaiting_vapid: true,
        ts: Date.now(),
        ua: typeof navigator !== "undefined" ? navigator.userAgent : "",
      }),
    );
    return true;
  } catch {
    return false;
  }
}

"use client";

import { useEffect, useState } from "react";

export function OfflineBanner() {
  const [online, setOnline] = useState(true);

  useEffect(() => {
    setOnline(navigator.onLine);
    function up() {
      setOnline(true);
    }
    function down() {
      setOnline(false);
    }
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    return () => {
      window.removeEventListener("online", up);
      window.removeEventListener("offline", down);
    };
  }, []);

  if (online) return null;

  return (
    <div className="border-b border-amber-500/40 bg-amber-950/95 px-4 py-3 text-center text-xs text-amber-100 backdrop-blur-md">
      Sem ligação — modo offline limitado (cache/SW). Funcionalidades remotas ficam suspensas.
    </div>
  );
}

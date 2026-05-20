"use client";

export async function runNativeShare(opts: { title: string; text?: string; url?: string }): Promise<boolean> {
  if (typeof navigator !== "undefined" && navigator.share) {
    try {
      await navigator.share({ title: opts.title, text: opts.text ?? opts.title, url: opts.url });
      return true;
    } catch {
      return false;
    }
  }
  if (opts.url && typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(opts.url);
    return true;
  }
  return false;
}

export function ShareSheet({
  hdrId,
  missionId,
}: {
  hdrId?: string;
  missionId?: string | null;
}) {
  const base =
    typeof window !== "undefined" ? `${window.location.origin}` : "";

  function whatsapp() {
    let url = base;
    if (hdrId && hdrId.length === 64) {
      url = `${base}/m/verify?hdr=${hdrId}`;
    } else if (missionId) {
      url = `${base}/verification?missionHint=${encodeURIComponent(missionId)}`;
    }
    window.open(`https://wa.me/?text=${encodeURIComponent(`Heillon Legal · ${url}`)}`, "_blank");
  }

  function mail() {
    const url =
      hdrId && hdrId.length === 64
        ? `${base}/m/verify?hdr=${hdrId}`
        : missionId
          ? `${base}/m/missions/${missionId}`
          : base;
    window.location.href = `mailto:?subject=${encodeURIComponent("Heillon Legal · verificação")}&body=${encodeURIComponent(url)}`;
  }

  async function clipboard() {
    const url =
      hdrId && hdrId.length === 64
        ? `${base}/m/verify?hdr=${hdrId}`
        : missionId
          ? `${base}/m/missions/${missionId}`
          : base;
    await runNativeShare({ title: "Heillon Legal", url });
  }

  return (
    <div className="flex flex-wrap gap-2 pt-4">
      <button type="button" onClick={whatsapp} className="btn-glass min-h-[48px] touch-manipulation px-5 py-3 text-xs">
        WhatsApp
      </button>
      <button type="button" onClick={mail} className="btn-glass min-h-[48px] px-5 py-3 text-xs">
        Email
      </button>
      <button
        type="button"
        onClick={clipboard}
        className="min-h-[48px] rounded-full border border-white/15 px-5 py-3 text-xs text-white/70 hover:border-gold-500/40 hover:text-white"
      >
        Copiar / Partilhar
      </button>
    </div>
  );
}

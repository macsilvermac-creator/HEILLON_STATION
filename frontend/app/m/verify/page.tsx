"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Suspense, useState } from "react";

import { QRScannerOverlay } from "@/components/mobile/QRScanner";
import { VerificationChecker } from "@/components/VerificationChecker";

export default function MobileVerificationPage() {
  const router = useRouter();
  const [scanner, setScanner] = useState(false);

  return (
    <div className="px-5 pb-40">
      <h1 className="text-xl font-semibold text-white">Verificar prova HDR</h1>
      <p className="mt-3 text-[11px] leading-relaxed text-white/48">
        Público e sem conta — mesmo motor do portal desktop, UX para polegares.
      </p>

      <button type="button" className="btn-gold mb-12 mt-8 w-full min-h-[54px]" onClick={() => setScanner(true)}>
        Digitalizar QR
      </button>

      <Suspense fallback={<p className="text-xs text-white/45">…</p>}>
        <div className="glass-elite rounded-3xl px-6 py-7">
          <VerificationChecker />
        </div>
      </Suspense>

      <Link href="/verification" prefetch={false} className="mt-12 inline-block text-[11px] text-white/30 underline decoration-dashed">
        Ver layout desktop ›
      </Link>

      {scanner ? (
        <QRScannerOverlay
          onDecoded={(id) => {
            router.replace(`/m/verify?hdr=${encodeURIComponent(id)}`);
            setScanner(false);
          }}
          onClose={() => setScanner(false)}
        />
      ) : null}
    </div>
  );
}

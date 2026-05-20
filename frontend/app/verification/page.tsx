"use client";

import Link from "next/link";
import { Suspense } from "react";

import { VerificationChecker } from "@/components/VerificationChecker";

export default function VerificationPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-8 px-4 pb-28 pt-28 md:pb-36 md:pt-36 lg:space-y-8">
      <div>
        <h1 className="text-gradient text-3xl font-semibold tracking-tight">Portal de verificação público</h1>
        <p className="mt-2 max-w-2xl text-sm text-white/60">
          Sem autenticação. Prefill automático através de <span className="font-mono text-xs text-white">?hdr=</span>.
          {" "}
          <Link href="/m/verify" className="text-gold-400 underline-offset-4 hover:underline">
            Modo handheld (camera / QR)
          </Link>
          .
        </p>
      </div>
      <Suspense fallback={<p className="text-sm text-white/50">A carregar verificação…</p>}>
        <VerificationChecker />
      </Suspense>
    </div>
  );
}

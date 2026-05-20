"use client";

import Link from "next/link";
import packageJson from "../../../package.json";

import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { PushNotificationManager } from "@/components/mobile/PushNotificationManager";

export default function MobileProfilePage() {
  const router = useRouter();
  const { user, logout, isAuthenticated } = useAuth();

  return (
    <div className="px-5 pb-40">
      <h1 className="text-xl font-semibold text-white">Perfil</h1>
      {isAuthenticated && user ? (
        <div className="glass-elite mt-10 rounded-[1.6rem] p-8 text-sm">
          <p className="text-xs uppercase tracking-[0.2em] text-white/45">Nome</p>
          <p className="mt-3 text-white">{user.name}</p>
          <p className="mt-6 text-xs uppercase tracking-[0.2em] text-white/45">Email</p>
          <p className="mt-3 font-mono text-[12px] text-gold-200/90">{user.email}</p>
          <p className="mt-6 text-xs uppercase tracking-[0.2em] text-white/45">Papel normativo</p>
          <p className="mt-3 text-white/70">{user.role}</p>
          {user.organization_id ? (
            <>
              <p className="mt-6 text-xs uppercase tracking-[0.2em] text-white/45">Organização</p>
              <p className="mt-3 font-mono text-[11px] text-white/55">{user.organization_id}</p>
            </>
          ) : null}
        </div>
      ) : (
        <p className="mt-10 text-sm text-white/50">Sem sessão — <Link href="/login" className="text-gold-400 underline">entre.</Link></p>
      )}

      <PushNotificationManager />

      <button
        type="button"
        className="mt-12 w-full rounded-2xl border border-white/15 py-5 text-xs font-semibold text-white/65"
        onClick={() => {
          logout();
          router.push("/m");
        }}
      >
        Sair
      </button>

      <p className="mt-14 text-center text-[10px] text-white/30">
        Heillon Legal mobile · versão declarada frontend {typeof packageJson?.version === "string" ? packageJson.version : "—"}
      </p>

      <Link href="/" className="mt-8 inline-block text-xs text-white/35 underline decoration-dashed">
        Ir para modo desktop ›
      </Link>
    </div>
  );
}

"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="pt">
      <body
        style={{
          minHeight: "100vh",
          background: "#0a0d14",
          color: "#fff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "system-ui, -apple-system, sans-serif",
          padding: "2rem",
        }}
      >
        <div style={{ maxWidth: "32rem", textAlign: "center" }}>
          <p style={{ fontSize: "0.75rem", letterSpacing: "0.2em", color: "#f87171" }}>
            FALHA CRÍTICA
          </p>
          <h1 style={{ marginTop: "0.75rem", fontSize: "1.875rem", fontWeight: 600 }}>
            A plataforma travou.
          </h1>
          <p style={{ marginTop: "1rem", fontSize: "0.875rem", color: "rgba(255,255,255,0.6)" }}>
            Recarregue a página. Se persistir, contate o suporte.
          </p>
          {error.digest ? (
            <p style={{ marginTop: "1.5rem", fontFamily: "monospace", fontSize: "0.6875rem", color: "rgba(255,255,255,0.3)" }}>
              ref: {error.digest}
            </p>
          ) : null}
          <button
            type="button"
            onClick={reset}
            style={{
              marginTop: "2.5rem",
              padding: "0.5rem 1.25rem",
              borderRadius: "9999px",
              border: "1px solid rgba(212,175,55,0.4)",
              background: "rgba(212,175,55,0.1)",
              color: "#f4d784",
              fontSize: "0.875rem",
              cursor: "pointer",
            }}
          >
            Recarregar
          </button>
        </div>
      </body>
    </html>
  );
}

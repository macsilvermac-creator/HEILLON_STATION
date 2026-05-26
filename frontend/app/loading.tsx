export default function Loading() {
  return (
    <div
      role="status"
      aria-live="polite"
      className="mx-auto flex max-w-3xl items-center justify-center px-6 py-24"
    >
      <span className="text-sm text-white/50">Carregando…</span>
    </div>
  );
}

import { LogoMark } from "@/components/shared/logo";

export function TypingIndicator() {
  return (
    <div className="flex animate-fade-up gap-2.5 py-1.5">
      <LogoMark className="mt-1 size-7 rounded-full text-[11px]" />
      <div
        className="flex items-center gap-1 rounded-2xl rounded-tl-md border border-border bg-card px-4 py-3 shadow-sm"
        aria-hidden="true"
      >
        <span className="size-1.5 animate-bounce rounded-full bg-futuro-corp/50 [animation-delay:-0.3s]" />
        <span className="size-1.5 animate-bounce rounded-full bg-futuro-corp/50 [animation-delay:-0.15s]" />
        <span className="size-1.5 animate-bounce rounded-full bg-futuro-corp/50" />
      </div>
      <span className="sr-only" role="status">
        El asistente está escribiendo
      </span>
    </div>
  );
}

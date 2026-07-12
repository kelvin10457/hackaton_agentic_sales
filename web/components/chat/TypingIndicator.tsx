export function TypingIndicator() {
  return (
    <div className="flex justify-start mb-3">
      <div className="bg-slate-100 rounded-2xl px-4 py-3 flex gap-1">
        <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:-0.3s]" />
        <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:-0.15s]" />
        <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" />
      </div>
    </div>
  );
}

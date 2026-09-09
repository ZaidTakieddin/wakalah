import { ShieldCheck } from "lucide-react";

export function Logo() {
  return (
    <a href="#top" aria-label="Wakalah home" className="inline-flex shrink-0 items-center gap-2.5 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-teal-400">
      <span className="grid size-10 place-items-center rounded-xl border border-teal-300/25 bg-gradient-to-br from-teal-700/70 to-teal-700/15 text-teal-200 shadow-inner shadow-white/10">
        <ShieldCheck size={21} strokeWidth={2.2} />
      </span>
      <span className="flex items-baseline gap-2">
        <strong className="text-lg tracking-[-0.03em] text-white">Wakalah</strong>
        <span className="text-sm text-teal-200">وكالة</span>
      </span>
    </a>
  );
}

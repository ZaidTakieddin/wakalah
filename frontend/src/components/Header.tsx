import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Menu, X } from "lucide-react";
import { Logo } from "./Logo";

const navItems = [
  ["Overview", "#overview"],
  ["Agentic core", "#agentic-core"],
  ["Scenarios", "#scenarios"],
  ["Network APIs", "#network-apis"],
  ["Team", "#team"],
];

export function Header() {
  const [open, setOpen] = useState(false);

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-white/10 bg-[#061824]/90 text-white backdrop-blur-xl">
      <div className="mx-auto flex h-[70px] w-[min(1240px,calc(100%-48px))] items-center gap-8 max-md:h-16 max-md:w-[calc(100%-24px)]">
        <Logo />
        <nav aria-label="Primary navigation" className="ml-auto flex items-center gap-7 max-lg:gap-4 max-md:hidden">
          {navItems.map(([label, href]) => (
            <a key={href} href={href} className="text-[13px] font-medium text-slate-300 transition hover:text-white">{label}</a>
          ))}
        </nav>
        <a href="#scenarios" className="flex items-center gap-2 rounded-lg border border-teal-300/20 bg-teal-700/20 px-4 py-2.5 text-xs font-semibold text-teal-50 transition hover:bg-teal-700/40 max-lg:hidden">
          Watch the trust decision <ArrowRight size={15} />
        </a>
        <button type="button" aria-label={open ? "Close navigation menu" : "Open navigation menu"} aria-expanded={open} onClick={() => setOpen(!open)} className="ml-auto hidden size-11 place-items-center rounded-xl border border-white/15 bg-white/5 text-white max-md:grid">
          {open ? <X size={21} /> : <Menu size={21} />}
        </button>
      </div>
      {open && (
        <motion.nav initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} aria-label="Mobile navigation" className="grid border-t border-white/10 bg-[#061824] px-4 pb-5 pt-3 md:hidden">
          {navItems.map(([label, href]) => (
            <a key={href} href={href} onClick={() => setOpen(false)} className="border-b border-white/10 px-2 py-3 text-sm text-slate-300">{label}</a>
          ))}
          <a href="#scenarios" onClick={() => setOpen(false)} className="mt-3 flex items-center justify-center gap-2 rounded-lg bg-teal-700 px-4 py-3 text-sm font-semibold text-white">Watch the trust decision <ArrowRight size={15} /></a>
        </motion.nav>
      )}
    </header>
  );
}

import { motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  Bot,
  Check,
  CheckCircle2,
  Database,
  FileKey,
  Fingerprint,
  KeyRound,
  Landmark,
  Radio,
  Scale,
  ShieldCheck,
  Smartphone,
  Sparkles,
  UserRound,
  Workflow,
} from "lucide-react";

function ArchitectureVisual() {
  return (
    <div aria-label="Wakalah trust architecture" className="relative rounded-2xl border border-teal-200/20 bg-gradient-to-br from-[#0d2d3b] to-[#061a27] p-5 shadow-[0_35px_70px_rgba(0,0,0,.35)] max-sm:p-3">
      <div className="flex items-center gap-2 border-b border-white/10 pb-3 text-[10px] text-slate-400">
        <span className="size-2 rounded-full bg-emerald-400 shadow-[0_0_0_5px_rgba(85,211,156,.09)]" />
        Live trust orchestration
        <span className="ml-auto font-mono text-slate-600">WKL-2841</span>
      </div>

      <div className="my-4 grid grid-cols-[1fr_42px_1fr] items-center max-sm:grid-cols-[1fr_24px_1fr]">
        <Actor icon={UserRound} label="Principal" name="Amina" tone="teal" />
        <div className="flex items-center text-teal-500/60"><span className="h-px flex-1 bg-teal-400/30" /><ArrowRight size={14} /></div>
        <Actor icon={Bot} label="External AI agent" name="Rasheed" tone="gold" />
      </div>

      <div className="rounded-xl border border-teal-300/25 bg-teal-800/15 p-3.5">
        <div className="flex items-center justify-between gap-3 text-[11px] font-semibold text-teal-50">
          <span className="flex items-center gap-1.5"><Sparkles size={16} className="text-teal-300" /> Wakalah supervisor</span>
          <span className="rounded-md border border-emerald-300/20 bg-emerald-500/10 px-2 py-1 text-[8px] tracking-widest text-emerald-300">LOW RISK</span>
        </div>
        <p className="mt-2 flex items-center gap-2 text-[10px] text-slate-400"><Check size={14} className="text-emerald-400" /> Mandate and beneficiary match</p>
        <p className="mt-1.5 flex items-center gap-2 text-[10px] text-slate-400"><Check size={14} className="text-emerald-400" /> Amount is inside the monthly limit</p>
        <div className="mt-3 border-t border-white/10 pt-2.5">
          <p className="flex items-center gap-1.5 text-[8px] uppercase tracking-widest text-slate-500"><Workflow size={14} /> Verification plan</p>
          <div className="mt-2 grid grid-cols-2 gap-2">
            <span className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[.03] px-2 py-2 text-[9px] text-slate-300"><Radio size={14} className="text-teal-300" /> SIM Swap</span>
            <span className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[.03] px-2 py-2 text-[9px] text-slate-300"><Smartphone size={14} className="text-teal-300" /> Device Swap</span>
          </div>
        </div>
      </div>

      <div className="mx-[14%] flex h-11 items-center justify-between border-b border-dashed border-teal-300/30 text-[8px] text-slate-500">
        <span>Nokia Network as Code</span><Radio size={17} className="text-teal-400" />
      </div>

      <div className="mt-4 grid grid-cols-[1.25fr_18px_1fr_18px_1fr] items-center gap-1.5 max-sm:grid-cols-[1fr_14px_1fr]">
        <Decision icon={Scale} label="Policy v3.2" value="All rules passed" />
        <ArrowRight size={16} className="text-slate-600" />
        <Decision icon={ShieldCheck} label="Final verdict" value="ALLOW" success />
        <ArrowRight size={16} className="text-slate-600 max-sm:hidden" />
        <Decision icon={Landmark} label="Relying party" value="Bank / PSP" className="max-sm:hidden" />
      </div>
      <div className="mt-3 flex justify-between gap-4 text-[8px] text-slate-500">
        <span className="flex items-center gap-1"><Fingerprint size={14} /> Agent key matched</span>
        <span className="flex items-center gap-1"><Database size={14} /> Evidence recorded</span>
      </div>
    </div>
  );
}

function Actor({ icon: Icon, label, name, tone }: { icon: typeof UserRound; label: string; name: string; tone: "teal" | "gold" }) {
  return (
    <div className="flex min-w-0 items-center gap-2 rounded-xl border border-white/10 bg-white/[.035] p-2.5 max-sm:p-2">
      <span className={`grid size-9 shrink-0 place-items-center rounded-lg ${tone === "teal" ? "bg-teal-600/20 text-teal-200" : "bg-amber-500/15 text-amber-200"}`}><Icon size={20} /></span>
      <span className="flex min-w-0 flex-col"><small className="text-[8px] uppercase tracking-wide text-slate-500">{label}</small><strong className="truncate text-[11px] text-slate-200">{name}</strong></span>
      <CheckCircle2 size={15} className="ml-auto shrink-0 text-emerald-400 max-sm:hidden" />
    </div>
  );
}

function Decision({ icon: Icon, label, value, success, className = "" }: { icon: typeof Scale; label: string; value: string; success?: boolean; className?: string }) {
  return (
    <div className={`flex min-w-0 items-center gap-2 rounded-lg border p-2.5 ${success ? "border-emerald-300/25 bg-emerald-500/10" : "border-white/10 bg-white/[.035]"} ${className}`}>
      <Icon size={18} className={success ? "text-emerald-400" : "text-amber-200"} />
      <span className="flex min-w-0 flex-col"><small className="text-[8px] uppercase text-slate-500">{label}</small><strong className={`truncate text-[9px] ${success ? "tracking-widest text-emerald-300" : "text-slate-200"}`}>{value}</strong></span>
    </div>
  );
}

export function Hero() {
  const reduceMotion = useReducedMotion();
  return (
    <section id="top" className="relative overflow-hidden bg-[radial-gradient(circle_at_75%_20%,rgba(14,129,119,.18),transparent_28%),linear-gradient(135deg,#061824_0%,#071e2b_58%,#0a2634_100%)] pt-[70px] text-white max-md:pt-16">
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 opacity-[.08] [background-image:linear-gradient(rgba(144,226,214,.5)_1px,transparent_1px),linear-gradient(90deg,rgba(144,226,214,.45)_1px,transparent_1px)] [background-size:54px_54px] [mask-image:linear-gradient(to_right,transparent,#000_44%,#000)]" />
      <div className="relative z-10 mx-auto grid min-h-[720px] w-[min(1180px,calc(100%-48px))] grid-cols-[.92fr_1.08fr] items-center gap-[72px] py-[72px] max-lg:gap-10 max-md:min-h-0 max-md:w-[calc(100%-32px)] max-md:grid-cols-1 max-md:gap-14 max-sm:w-[calc(100%-24px)] max-sm:py-14">
        <motion.div initial={reduceMotion ? false : { opacity: 0, y: 22 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: reduceMotion ? 0 : .65 }} className="max-md:text-center">
          <div className="mb-6 flex flex-wrap gap-2 max-md:justify-center">
            {["MENA Ignite Hackathon", "Secure FinTech + Anti-Fraud", "AI Agent + CAMARA APIs"].map((badge) => <span key={badge} className="rounded-md border border-slate-300/15 bg-white/[.025] px-2.5 py-1.5 text-[9px] font-bold uppercase tracking-wider text-slate-400">{badge}</span>)}
          </div>
          <p className="mb-4 flex items-center gap-2.5 text-[11px] font-bold tracking-[.16em] text-teal-300 max-md:justify-center"><span className="h-px w-7 bg-teal-400" /> THE TRUST LAYER FOR AGENTIC COMMERCE</p>
          <h1 className="max-w-[620px] text-[clamp(48px,5vw,75px)] font-semibold leading-[.98] tracking-[-.055em] max-md:mx-auto max-sm:text-[47px]">Trust every action an <em className="not-italic text-teal-300">AI agent</em> takes.</h1>
          <p className="mt-6 max-w-[580px] text-base leading-7 text-slate-300 max-md:mx-auto max-sm:text-sm">Wakalah independently verifies whether an AI-initiated transaction is still authorized—then returns an explainable <strong className="text-[13px] tracking-wide text-white">ALLOW</strong>, <strong className="text-[13px] tracking-wide text-white">STEP-UP</strong>, or <strong className="text-[13px] tracking-wide text-white">DENY</strong> through deterministic policy.</p>
          <div className="mt-8 flex flex-wrap gap-3 max-md:justify-center max-sm:grid">
            <a href="#scenarios" className="flex min-h-12 items-center justify-center gap-2 rounded-lg bg-teal-600 px-5 text-sm font-bold shadow-xl shadow-teal-950/30 transition hover:-translate-y-0.5 hover:bg-teal-500">Compare both scenarios <ArrowRight size={17} /></a>
            <a href="#network-apis" className="flex min-h-12 items-center justify-center rounded-lg border border-white/15 bg-white/[.035] px-5 text-sm font-bold text-slate-200 transition hover:-translate-y-0.5 hover:bg-white/10">Explore the API plan</a>
          </div>
          <div className="mt-7 flex flex-wrap gap-4 text-[11px] text-slate-400 max-md:justify-center"><span className="flex items-center gap-1.5"><FileKey size={15} className="text-teal-300" /> Scoped mandates</span><span className="flex items-center gap-1.5"><KeyRound size={15} className="text-teal-300" /> Agent-bound proof</span><span className="flex items-center gap-1.5"><Scale size={15} className="text-teal-300" /> Fixed policy</span></div>
        </motion.div>
        <motion.div initial={reduceMotion ? false : { opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: reduceMotion ? 0 : .7, delay: .12 }} className="relative pt-7">
          <p className="absolute left-3 top-0 text-[9px] font-bold tracking-[.15em] text-slate-500"><span className="mr-2 text-teal-400">01</span> TRUST DECISION IN PROGRESS</p>
          <ArchitectureVisual />
          <div className="absolute right-[-14px] top-20 flex items-center gap-2 rounded-lg border border-teal-300/30 bg-[#0c2a38] px-3 py-2.5 text-teal-300 shadow-xl max-sm:right-[-4px]"><KeyRound size={15} /><span className="flex flex-col"><small className="text-[7px] text-slate-500">Proof of possession</small><strong className="text-[8px] tracking-wider">VERIFIED</strong></span></div>
        </motion.div>
      </div>
      <div className="relative z-10 border-t border-white/10 bg-black/15">
        <div className="mx-auto flex min-h-[68px] w-[min(1180px,calc(100%-48px))] items-center justify-between gap-6 max-md:w-[calc(100%-32px)] max-md:flex-col max-md:justify-center max-md:gap-1 max-md:py-4 max-md:text-center">
          <p className="flex items-center gap-2 text-xs text-slate-300"><ShieldCheck size={18} className="text-teal-300" /> The agent plans and explains. <strong className="text-white">Policy decides.</strong></p>
          <span className="text-[10px] text-slate-500">No language model independently authorizes a financial transaction.</span>
        </div>
      </div>
    </section>
  );
}

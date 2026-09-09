import { motion } from "framer-motion";
import { AlertTriangle, ArrowRight, Bot, BrainCircuit, Check, Gauge, Scale, Workflow } from "lucide-react";

const cards = [
  { number: "01", icon: BrainCircuit, title: "Understand the task", copy: "Read the intended action, transaction context, mandate token, and agent proof." },
  { number: "02", icon: Gauge, title: "Propose the risk", copy: "Classify LOW, MEDIUM, HIGH, or CRITICAL and expose every reason." },
  { number: "03", icon: Workflow, title: "Build the plan", copy: "Select only approved CAMARA checks required for the current risk." },
  { number: "04", icon: Scale, title: "Apply fixed policy", copy: "Submit verified evidence to versioned rules that issue the final verdict." },
];

export function Overview() {
  return (
    <section id="overview" className="py-24 max-md:py-20 max-sm:py-16">
      <div className="mx-auto w-[min(1180px,calc(100%-48px))] max-md:w-[calc(100%-32px)] max-sm:w-[calc(100%-24px)]">
        <div className="mb-11 grid grid-cols-[1.3fr_.7fr] items-end gap-20 max-md:grid-cols-1 max-md:gap-5">
          <div><p className="mb-3 text-[10px] font-extrabold tracking-[.16em] text-teal-700">HOW WAKALAH WORKS</p><h2 className="max-w-3xl text-[clamp(36px,4.4vw,58px)] font-semibold leading-[1.04] tracking-[-.05em]">An intelligent verification planner with <span className="text-teal-700">strict security rails.</span></h2></div>
          <p className="mb-1 text-sm leading-7 text-slate-600">Wakalah does not control the consumer’s AI agent or replace the bank’s fraud platform. It independently checks whether each delegated action remains authorized.</p>
        </div>

        <div id="agentic-core" className="grid grid-cols-4 gap-3 max-lg:grid-cols-2 max-sm:grid-cols-1">
          {cards.map((card, index) => {
            const Icon = card.icon;
            return (
              <motion.article key={card.number} initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: .3 }} transition={{ delay: index * .08 }} className="relative min-h-56 rounded-xl border border-slate-200 bg-white p-5 shadow-[0_8px_26px_rgba(6,34,43,.035)] transition hover:border-teal-200 hover:shadow-lg max-sm:min-h-48">
                <span className="absolute right-5 top-4 font-mono text-[10px] text-slate-400">{card.number}</span>
                <span className="grid size-11 place-items-center rounded-xl border border-teal-200 bg-teal-50 text-teal-700"><Icon size={22} /></span>
                <h3 className="mb-2 mt-7 text-base font-semibold tracking-tight">{card.title}</h3>
                <p className="text-xs leading-5 text-slate-600">{card.copy}</p>
                {index < 3 && <span aria-hidden="true" className="absolute -right-5 top-[47%] z-10 grid size-6 place-items-center rounded-full border border-slate-200 bg-[#f6f9f8] text-slate-400 max-lg:hidden"><ArrowRight size={14} /></span>}
              </motion.article>
            );
          })}
        </div>

        <div className="mt-14 grid grid-cols-2 gap-5 max-md:grid-cols-1">
          <div className="overflow-hidden rounded-2xl border border-[#153340] bg-[#061824] text-slate-300 shadow-2xl shadow-slate-900/15">
            <div className="flex h-10 items-center gap-1.5 border-b border-white/10 bg-white/[.025] px-4"><i className="size-2 rounded-full bg-slate-600" /><i className="size-2 rounded-full bg-amber-700" /><i className="size-2 rounded-full bg-emerald-800" /><small className="ml-2 font-mono text-[8px] text-slate-500">agent-proposal.json</small></div>
            <pre className="overflow-x-auto p-6 font-mono text-[11px] leading-5 text-slate-300 max-sm:p-5"><code>{`{
  "riskLevel": "MEDIUM",
  "reasons": [
    "amount higher than normal",
    "principal currently roaming"
  ],
  "requiredChecks": [
    "simSwap", "deviceSwap", "roamingStatus"
  ],
  "recommendedAction": "STEP_UP"
}`}</code></pre>
            <div className="flex items-center gap-2 border-t border-white/10 px-4 py-3 text-[9px] text-slate-500"><Bot size={15} className="text-teal-300" /> Agent proposal — not the final verdict</div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-7 max-sm:p-5">
            <p className="mb-3 text-[10px] font-extrabold tracking-[.16em] text-teal-700">DETERMINISTIC POLICY ENGINE</p>
            <h3 className="text-3xl font-semibold leading-tight tracking-[-.04em]">Same verified inputs.<br />Same security result.</h3>
            <p className="my-3 text-xs leading-5 text-slate-600">A strict, versioned rules engine cannot improvise, edit thresholds, or bypass mandatory evidence.</p>
            <div className="flex gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
              <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-amber-200 text-amber-700"><AlertTriangle size={20} /></span>
              <div className="flex flex-col"><small className="text-[8px] uppercase tracking-widest text-amber-700">Policy result</small><strong className="text-xs text-amber-800">STEP-UP REQUIRED</strong><p className="mt-1 text-[9px] text-amber-900/70">Mandatory verification is incomplete for this risk tier.</p></div>
            </div>
            <PolicyRule label="Invalid signature" result="DENY" danger />
            <PolicyRule label="All mandatory checks pass" result="ALLOW" />
          </div>
        </div>
      </div>
    </section>
  );
}

function PolicyRule({ label, result, danger }: { label: string; result: string; danger?: boolean }) {
  return <div className="grid grid-cols-[1fr_18px_auto] items-center gap-2 border-b border-slate-100 px-0.5 py-2.5 text-[10px] text-slate-500 last:border-0"><span>{label}</span><ArrowRight size={14} /><strong className={danger ? "text-red-600" : "text-emerald-700"}>{result}</strong></div>;
}

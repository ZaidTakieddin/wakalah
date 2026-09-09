import { useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  Ban,
  Bot,
  BrainCircuit,
  Check,
  CheckCircle2,
  ChevronDown,
  CircleDollarSign,
  FileKey,
  Gauge,
  KeyRound,
  Landmark,
  LockKeyhole,
  Network,
  Radio,
  RotateCcw,
  Scale,
  ShieldAlert,
  ShieldCheck,
  Signal,
  Smartphone,
  UserRound,
  Workflow,
  X,
  XCircle,
  type LucideIcon,
} from "lucide-react";
import { scenarioStages, type ScenarioStep } from "../data";

const iconMap: Record<string, [LucideIcon, LucideIcon]> = {
  mandate: [UserRound, FileKey],
  clone: [Bot, ShieldAlert],
  identity: [Smartphone, KeyRound],
  "key-fail": [KeyRound, XCircle],
  transfer: [CircleDollarSign, ArrowRight],
  "stop-plan": [Workflow, Ban],
  "risk-low": [Gauge, CheckCircle2],
  "signals-bad": [Radio, ShieldAlert],
  "api-plan": [Network, Workflow],
  explain: [BrainCircuit, FileKey],
  "signals-good": [Signal, CheckCircle2],
  "policy-deny": [Scale, XCircle],
  "policy-allow": [Scale, ShieldCheck],
  revoke: [FileKey, Ban],
  success: [Landmark, CheckCircle2],
  blocked: [Landmark, ShieldAlert],
};

type Tone = "happy" | "threat";

function ScenarioGraphic({ visual, tone }: { visual: string; tone: Tone }) {
  const [Primary, Secondary] = iconMap[visual] ?? [ShieldCheck, Check];
  const happy = tone === "happy";
  return (
    <div
      aria-hidden="true"
      className={`relative flex min-h-40 items-center justify-center overflow-hidden rounded-xl ${happy ? "bg-gradient-to-br from-emerald-50 to-teal-50 text-teal-700" : "bg-gradient-to-br from-red-50 to-rose-50 text-red-600"}`}
    >
      <span
        className={`absolute size-24 rounded-full border ${happy ? "border-teal-700/10" : "border-red-600/10"}`}
      />
      <span
        className={`absolute size-32 rounded-full border ${happy ? "border-teal-700/10" : "border-red-600/10"}`}
      />
      <span
        className={`relative z-10 grid size-14 place-items-center rounded-2xl border bg-white/85 shadow-lg ${happy ? "border-teal-200 shadow-teal-800/10" : "border-red-200 shadow-red-800/10"}`}
      >
        <Primary size={29} />
      </span>
      <ArrowRight
        size={14}
        className={
          happy
            ? "relative z-10 mx-1 text-teal-500"
            : "relative z-10 mx-1 text-red-400"
        }
      />
      <span
        className={`relative z-10 grid size-10 place-items-center rounded-xl border bg-white/85 shadow-md ${happy ? "border-teal-200" : "border-red-200"}`}
      >
        <Secondary size={21} />
      </span>
      <i
        className={`absolute left-5 top-5 size-1.5 rounded-full ${happy ? "bg-teal-500" : "bg-red-500"}`}
      />
      <i
        className={`absolute bottom-6 right-6 size-1.5 rounded-full ${happy ? "bg-teal-500" : "bg-red-500"}`}
      />
    </div>
  );
}

function ScenarioCard({ step, tone }: { step: ScenarioStep; tone: Tone }) {
  const happy = tone === "happy";
  return (
    <article
      className={`grid h-full min-h-56 grid-cols-[37%_1fr] gap-4 rounded-xl border bg-white/95 p-3.5 shadow-sm max-lg:grid-cols-[32%_1fr] max-lg:gap-2.5 max-md:min-h-0 max-sm:grid-cols-1 ${happy ? "border-l-[3px] border-l-emerald-500 border-y-slate-200 border-r-slate-200" : "border-r-[3px] border-r-red-500 border-y-slate-200 border-l-slate-200 max-md:border-l-[3px] max-md:border-l-red-500 max-md:border-r-slate-200"}`}
    >
      <ScenarioGraphic visual={step.visual} tone={tone} />
      <div className="min-w-0 py-1">
        <div className="flex items-center justify-between gap-2">
          <span className="text-[10px] font-extrabold uppercase tracking-[.11em] text-slate-500">
            {step.eyebrow}
          </span>
          <em
            className={`whitespace-nowrap rounded px-1.5 py-1 text-[10px] font-bold not-italic ${happy ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}
          >
            {step.status}
          </em>
        </div>
        <h4 className="mb-1.5 mt-2.5 text-lg font-semibold leading-snug tracking-tight max-lg:text-[15px] max-sm:text-[17px]">
          {step.title}
        </h4>
        <p className="text-[12px] leading-4 text-slate-600 max-sm:text-[14px]">
          {step.summary}
        </p>
        <ul className="mt-3 flex flex-wrap gap-1.5">
          {step.bullets.map((bullet) => (
            <li
              key={bullet}
              className="flex items-center gap-1 rounded-md border border-slate-200 bg-slate-50 px-1.5 py-1 text-[10px] text-slate-600 max-sm:text-[9px]"
            >
              {happy ? (
                <Check size={12} className="text-emerald-600" />
              ) : (
                <X size={12} className="text-red-600" />
              )}
              {bullet}
            </li>
          ))}
        </ul>
      </div>
    </article>
  );
}

function OverviewArt({ tone }: { tone: Tone }) {
  const happy = tone === "happy";
  return (
    <div
      aria-hidden="true"
      className={`relative flex h-40 items-center justify-center gap-3 overflow-hidden text-white ${happy ? "bg-gradient-to-br from-[#092d34] to-[#0a3b3c]" : "bg-gradient-to-br from-[#2a1720] to-[#431c22]"}`}
    >
      <div className="absolute inset-0 opacity-10 [background-image:linear-gradient(rgba(255,255,255,.4)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.4)_1px,transparent_1px)] [background-size:28px_28px]" />
      <ArtActor icon={UserRound} label="Amina" />
      <span
        className={`h-px w-8 ${happy ? "bg-teal-300/50" : "bg-red-300/50"}`}
      />
      <ArtActor
        icon={happy ? Bot : ShieldAlert}
        label={happy ? "Rasheed" : "Clone"}
        active
        tone={tone}
      />
      <span
        className={`h-px w-8 ${happy ? "bg-teal-300/50" : "bg-red-300/50"}`}
      />
      <div className="relative z-10 grid size-16 place-items-center rounded-2xl border border-teal-300/40 bg-teal-700/30">
        <ShieldCheck size={28} />
        <strong className="absolute bottom-1 text-[7px] text-teal-200">
          W
        </strong>
      </div>
      <span
        className={`absolute right-4 top-3 flex items-center gap-1 rounded-lg px-2 py-2 text-[8px] font-bold ${happy ? "bg-emerald-800 text-emerald-200" : "bg-red-900 text-red-200"}`}
      >
        {happy ? <Check size={20} /> : <X size={20} />}
        {happy ? "ALLOW" : "DENY"}
      </span>
      <span className="absolute bottom-3 left-4 text-[8px] uppercase tracking-widest text-white/50">
        {happy ? "Trusted delegated payment" : "Compromised request contained"}
      </span>
    </div>
  );
}

function ArtActor({
  icon: Icon,
  label,
  active,
  tone,
}: {
  icon: LucideIcon;
  label: string;
  active?: boolean;
  tone?: Tone;
}) {
  return (
    <div
      className={`relative z-10 flex h-16 w-14 flex-col items-center justify-center gap-1 rounded-xl border text-white ${active ? (tone === "happy" ? "border-teal-300/30 bg-teal-600/20" : "border-red-300/30 bg-red-600/20") : "border-white/15 bg-white/5"}`}
    >
      <Icon size={25} />
      <small className="text-[7px] text-white/60">{label}</small>
    </div>
  );
}

function LaneHeader({ tone }: { tone: Tone }) {
  const happy = tone === "happy";
  return (
    <div className="overflow-hidden rounded-t-2xl border border-slate-200 bg-white/90">
      <OverviewArt tone={tone} />
      <div className="flex items-center gap-3 px-4 pb-2 pt-4">
        <span
          className={`grid size-10 shrink-0 place-items-center rounded-xl ${happy ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}
        >
          {happy ? <ShieldCheck size={20} /> : <ShieldAlert size={20} />}
        </span>
        <div className="min-w-0">
          <p className="text-[8px] font-extrabold tracking-[.13em] text-slate-500">
            {happy ? "HAPPY SCENARIO" : "ATTACK SCENARIO"}
          </p>
          <h3 className="text-lg font-semibold tracking-tight">
            {happy ? "Authorized agent" : "Cloned or compromised agent"}
          </h3>
        </div>
        <span
          className={`ml-auto whitespace-nowrap rounded-md px-2 py-1 text-[9px] font-bold ${happy ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}
        >
          {happy ? "Trusted flow" : "Threat detected"}
        </span>
      </div>
      <p className="px-4 pb-4 text-[11px] leading-[1.6] text-slate-600">
        {happy
          ? "Amina authorizes Rasheed to send up to 2,000 QAR monthly to her mother through an approved provider."
          : "An attacker uses stolen application credentials to request money after suspicious mobile-account changes."}
      </p>
    </div>
  );
}

export function Scenarios() {
  const reduceMotion = useReducedMotion();
  return (
    <section
      id="scenarios"
      className="relative border-y border-slate-200 bg-[#eef4f2] py-24 max-md:py-20 max-sm:py-16"
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 opacity-10 [background-image:radial-gradient(#9cb1ad_1px,transparent_1px)] [background-size:24px_24px]"
      />
      <div className="relative mx-auto w-[min(1180px,calc(100%-48px))] max-md:w-[calc(100%-32px)] max-sm:w-[calc(100%-24px)]">
        <div className="mx-auto mb-10 max-w-3xl text-center">
          <p className="mb-3 text-[10px] font-extrabold tracking-[.16em] text-teal-700">
            THE TRUST DECISION
          </p>
          <h2 className="text-[clamp(36px,4.4vw,58px)] font-semibold leading-[1.04] tracking-[-.05em]">
            Same delegated payment.{" "}
            <span className="text-teal-700">Two different outcomes.</span>
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-sm leading-7 text-slate-600">
            Wakalah gathers only the evidence the risk requires, explains it,
            and hands final authority to strict policy.
          </p>
        </div>

        <div className="mx-auto mb-7 flex w-max max-w-full flex-wrap justify-center gap-4 rounded-lg border border-slate-200 bg-white/75 px-3 py-2 text-[9px] text-slate-500">
          <span className="flex items-center gap-1.5">
            <i className="size-2 rounded-full bg-emerald-600" /> Authorized path
          </span>
          <span className="flex items-center gap-1.5">
            <i className="h-px w-4 bg-slate-400" /> Matched decision stage
          </span>
          <span className="flex items-center gap-1.5">
            <i className="size-2 rounded-full bg-red-600" /> Contained attack
          </span>
        </div>

        <div
          key="desktop" 
          className="grid grid-cols-[minmax(0,1fr)_76px_minmax(0,1fr)] max-md:hidden"
        >
          <LaneHeader tone="happy" />
          <div className="relative flex items-center justify-center before:absolute before:inset-y-0 before:left-1/2 before:w-px before:bg-slate-300">
            <span className="relative rounded bg-slate-200 px-1.5 py-1 text-[7px] font-extrabold tracking-widest text-slate-500">
              COMPARE
            </span>
          </div>
          <LaneHeader tone="threat" />
          {scenarioStages.map((stage, index) => (
            <div
              key={stage.number}
              className="col-span-3 mt-3.5 grid grid-cols-[minmax(0,1fr)_76px_minmax(0,1fr)] items-stretch"
            >
              <motion.div
                initial={reduceMotion ? false : { opacity: 0, x: -18 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, amount: 0.25 }}
                transition={{ delay: index * 0.035 }}
              >
                <ScenarioCard step={stage.happy} tone="happy" />
              </motion.div>
              <div className="relative flex flex-col items-center before:absolute before:inset-y-0 before:left-1/2 before:w-px before:bg-slate-300">
                <span className="relative z-10 mt-5 grid size-8 place-items-center rounded-full border border-slate-400 bg-[#eef4f2] font-mono text-[9px] text-slate-600 shadow-[0_0_0_6px_#eef4f2]">
                  {stage.number}
                </span>
                <small className="relative z-10 mt-2 bg-[#eef4f2] px-1 text-[7px] uppercase tracking-wider text-slate-500">
                  {stage.label}
                </small>
                {stage.number < scenarioStages.length && (
                  <ChevronDown
                    size={14}
                    className="absolute -bottom-2 z-10 bg-[#eef4f2] text-slate-500"
                  />
                )}
              </div>
              <motion.div
                initial={reduceMotion ? false : { opacity: 0, x: 18 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, amount: 0.25 }}
                transition={{ delay: index * 0.035 + 0.04 }}
              >
                <ScenarioCard step={stage.threat} tone="threat" />
              </motion.div>
            </div>
          ))}
        </div>

        <div key="mobile" className="hidden gap-8 max-md:grid">
          {(["happy", "threat"] as const).map((tone) => (
            <div key={tone} className="overflow-hidden rounded-2xl">
              <LaneHeader tone={tone} />
              <div className="relative pl-10 pt-3 before:absolute before:bottom-7 before:left-4 before:top-0 before:w-px before:bg-slate-300">
                {scenarioStages.map((stage, index) => (
                  <motion.div
                    key={stage.number}
                    initial={reduceMotion ? false : { opacity: 0, y: 18 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, amount: 0.22 }}
                    transition={{ delay: index * 0.04 }}
                    className="relative mb-3.5"
                  >
                    <div className="absolute -left-10 top-5 z-10 flex flex-col items-center">
                      <span className="grid size-8 place-items-center rounded-full border border-slate-400 bg-[#eef4f2] font-mono text-[9px] text-slate-600 shadow-[0_0_0_5px_#eef4f2]">
                        {stage.number}
                      </span>
                      {stage.number < 8 && (
                        <ChevronDown
                          size={13}
                          className="mt-2 bg-[#eef4f2] text-slate-500"
                        />
                      )}
                    </div>
                    <ScenarioCard step={stage[tone]} tone={tone} />
                  </motion.div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 flex items-center justify-between gap-5 rounded-xl border border-slate-200 bg-white/75 p-4 max-sm:flex-col max-sm:items-start">
          <p className="flex items-center gap-2 text-[12px] text-slate-600">
            <LockKeyhole size={18} className="text-teal-700" /> Final decisions
            originate from the policy engine—not the agent recommendation.
          </p>
         
        </div>
      </div>
    </section>
  );
}

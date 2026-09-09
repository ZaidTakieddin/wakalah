import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Clock3,
  Code2,
  Forward,
  Globe2,
  Layers3,
  MapPin,
  Network,
  Phone,
  Radio,
  Recycle,
  ScanFace,
  Signal,
  Smartphone,
  type LucideIcon,
} from "lucide-react";
import { networkApis, type NetworkApi } from "../data";

const icons: Record<string, LucideIcon> = {
  phone: Phone,
  badge: ScanFace,
  sim: Radio,
  device: Smartphone,
  forward: Forward,
  clock: Clock3,
  recycle: Recycle,
  signal: Signal,
  globe: Globe2,
  location: MapPin,
};
const filters = [
  "All",
  "Core MVP",
  "Identity",
  "Hijack protection",
  "Continuity",
  "Context",
];

function ApiCard({ api, index }: { api: NetworkApi; index: number }) {
  const Icon = icons[api.icon] ?? Network;
  return (
    <motion.article
      initial={{ opacity: 0, y: 15 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.25 }}
      transition={{ delay: (index % 4) * 0.05 }}
      className="group relative min-h-75 overflow-hidden rounded-xl border border-slate-200 bg-white p-5 transition hover:-translate-y-1 hover:border-teal-200 hover:shadow-xl hover:shadow-teal-950/5"
    >
      <div className="flex items-center justify-between gap-3">
        <span className="grid size-11 place-items-center rounded-xl bg-teal-50 text-teal-700">
          <Icon size={26} />
        </span>
        <span
          className={`rounded-md px-2 py-1 text-[9px] font-bold ${api.priority === "Core MVP" ? "bg-teal-50 text-teal-700" : "bg-amber-50 text-amber-800"}`}
        >
          {api.priority}
        </span>
      </div>
      <p className="mb-1 mt-5 text-[8px] font-bold uppercase tracking-widest text-teal-700">
        {api.category}
      </p>
      <h3 className="text-lg font-semibold tracking-tight">{api.name}</h3>
      <p className="mb-3.5 mt-2.5 min-h-14 text-[12px] leading-4 text-slate-600">
        {api.description}
      </p>
      <div className="flex flex-col gap-1 rounded-lg bg-slate-50 p-2.5 mb-7">
        <strong className="text-[10px] text-slate-700">
          Used by Wakalah for
        </strong>
        <span className="text-[11px] leading-4 text-slate-600">{api.use}</span>
      </div>
      <div className="absolute inset-x-5 bottom-4 flex items-center justify-between gap-2 text-[9px] text-slate-400">
        <span className="flex items-center gap-1">
          <Layers3 size={13} /> {api.stage}
        </span>
        {api.priority !== "Core MVP" && (
          <em className="not-italic text-amber-700">
            Called only when required
          </em>
        )}
      </div>
      <span
        aria-hidden="true"
        className="absolute right-14 top-10 size-2 rounded-full bg-teal-600 opacity-0 transition duration-500 group-hover:-translate-x-11 group-hover:opacity-70 group-hover:shadow-[0_0_8px_#0f766e]"
      />
    </motion.article>
  );
}

export function NetworkApis() {
  const [active, setActive] = useState("All");
  const visible = useMemo(
    () =>
      networkApis.filter(
        (api) =>
          active === "All" ||
          (active === "Core MVP"
            ? api.priority === "Core MVP"
            : api.category === active),
      ),
    [active],
  );
  return (
    <section
      id="network-apis"
      className="bg-white py-24 max-md:py-20 max-sm:py-16"
    >
      <div className="mx-auto w-[min(1180px,calc(100%-48px))] max-md:w-[calc(100%-32px)] max-sm:w-[calc(100%-24px)]">
        <div className="mb-11 grid grid-cols-[1.3fr_.7fr] items-end gap-20 max-md:grid-cols-1 max-md:gap-5">
          <div>
            <p className="mb-3 text-[10px] font-extrabold tracking-[.16em] text-teal-700">
              NETWORK INTELLIGENCE
            </p>
            <h2 className="max-w-3xl text-[clamp(36px,4.4vw,58px)] font-semibold leading-[1.04] tracking-tighter">
              CAMARA evidence through{" "}
              <span className="text-teal-700">Nokia Network as Code.</span>
            </h2>
          </div>
          <p className="mb-1 text-sm leading-7 text-slate-600">
            Operator-held signals add phone, identity, continuity, and device
            context. The agent selects a controlled plan—it never calls every
            API on every transaction.
          </p>
        </div>
        <div className="mb-6 flex items-center justify-between gap-5 max-sm:flex-col max-sm:items-start">
          <div
            role="tablist"
            aria-label="Filter network APIs"
            className="flex flex-wrap gap-2"
          >
            {filters.map((filter) => (
              <button
                key={filter}
                type="button"
                role="tab"
                aria-selected={active === filter}
                onClick={() => setActive(filter)}
                className={`rounded-lg border px-3 py-2 text-[10px] transition ${active === filter ? "border-teal-700 bg-teal-700 text-white" : "border-slate-200 bg-slate-50 text-slate-600 hover:border-teal-300"}`}
              >
                {filter}
              </button>
            ))}
          </div>
          <span className="text-[10px] text-slate-400">
            {visible.length} APIs
          </span>
        </div>
        <div className="grid grid-cols-4 gap-3.5 max-lg:grid-cols-3 max-md:grid-cols-2 max-sm:grid-cols-1">
          {visible.map((api, index) => (
            <ApiCard key={api.name} api={api} index={index} />
          ))}
        </div>

        <div className="mt-8 grid grid-cols-[.8fr_1.2fr] gap-7 rounded-2xl border border-teal-100 bg-teal-50/70 p-6 max-md:grid-cols-1">
          <div className="flex items-start gap-3">
            <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-teal-100 text-teal-700">
              <Radio size={22} />
            </span>
            <div>
              <p className="mb-2 text-[10px] font-extrabold tracking-[.16em] text-teal-700">
                GRACEFUL DEGRADATION
              </p>
              <h3 className="text-xl font-semibold tracking-tight">
                What if a network signal is unavailable?
              </h3>
              <p className="mt-2 text-[10px] text-slate-600">
                Availability changes the policy path—never the meaning of the
                evidence.
              </p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 max-sm:grid-cols-1">
            <RiskAction tone="low" label="LOW">
              Use approved fresh cached evidence only when policy allows.
            </RiskAction>
            <RiskAction tone="medium" label="MEDIUM">
              Require STEP-UP when mandatory evidence is unavailable.
            </RiskAction>
            <RiskAction tone="high" label="HIGH / CRITICAL">
              Fail closed when required evidence cannot be obtained.
            </RiskAction>
          </div>
          <div className="col-span-full flex items-center justify-center gap-2 border-t border-teal-100 pt-4 text-[9px] text-slate-600 max-sm:items-start">
            <Code2 size={15} /> Demo data is labeled{" "}
            <strong>Recorded sandbox response</strong>. Simulated events are
            never presented as live operator events.
          </div>
        </div>
        <p className="mt-3 flex items-center justify-center gap-2 text-[9px] text-slate-500 max-sm:items-start">
          <AlertTriangle size={15} /> API availability and supported operations
          depend on the assigned Nokia Network as Code sandbox and operator
          exposure.
        </p>
      </div>
    </section>
  );
}

function RiskAction({
  tone,
  label,
  children,
}: {
  tone: "low" | "medium" | "high";
  label: string;
  children: string;
}) {
  const colors =
    tone === "low"
      ? "bg-emerald-50 text-emerald-700"
      : tone === "medium"
        ? "bg-amber-50 text-amber-800"
        : "bg-red-50 text-red-700";
  return (
    <div className="rounded-lg border border-slate-200 bg-white/80 p-3">
      <span
        className={`inline-flex rounded px-1.5 py-1 text-[7px] font-extrabold ${colors}`}
      >
        {label}
      </span>
      <p className="mt-2 text-[9px] leading-4 text-slate-600">{children}</p>
    </div>
  );
}

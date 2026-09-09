import { ArrowUpRight, Mail, PhoneCall } from "lucide-react";
import { Logo } from "./Logo";

const members = [
  {
    initials: "MY",
    name: "Mohammad Yasser Al-Koudmany",
    email: "alkoudmanyyasser@gmail.com",
    phone: "+963 940 830 950",
    phoneHref: "+963940830950",
  },
  {
    initials: "ZT",
    name: "Zaid Takieddin",
    email: "zaidtakieddin@gmail.com",
    phone: "+963 940 464 733",
    phoneHref: "+963940464733",
  },
];

export function Footer() {
  return (
    <footer id="team" className="relative overflow-hidden bg-[#061824] pt-20 text-white max-sm:pt-16">
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 opacity-[.055] [background-image:linear-gradient(rgba(255,255,255,.5)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.5)_1px,transparent_1px)] [background-size:50px_50px]" />
      <div aria-hidden="true" className="absolute -bottom-28 right-3 text-[420px] font-extrabold leading-none text-white/[.025]">W</div>

      <div className="relative z-10 mx-auto grid w-[min(1180px,calc(100%-48px))] grid-cols-2 gap-20 max-md:w-[calc(100%-32px)] max-md:grid-cols-1 max-md:gap-12 max-sm:w-[calc(100%-24px)]">
        <div>
          <Logo />
          <h2 className="mt-6 max-w-lg text-4xl font-semibold leading-tight tracking-[-.045em] max-sm:text-3xl">The trust layer for AI-agent transactions.</h2>
          <p className="mt-4 max-w-xl text-[11px] leading-5 text-slate-400">Built for the GSMA MENA Ignite Hackathon using agentic risk assessment, controlled CAMARA orchestration, deterministic security policy, and Nokia Network as Code.</p>
          <div className="mt-5 flex flex-wrap gap-2">
            {["Agentic AI", "CAMARA", "Deterministic policy"].map((tag) => <span key={tag} className="rounded-md border border-white/10 px-2 py-1.5 text-[8px] text-slate-400">{tag}</span>)}
          </div>
        </div>

        <div>
          <p className="mb-4 text-[9px] font-extrabold tracking-[.15em] text-teal-300">BUILD TEAM</p>
          <div className="grid gap-2.5">
            {members.map((member) => (
              <article key={member.email} className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/[.035] p-4">
                <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-teal-700/30 text-[10px] font-bold text-teal-200">{member.initials}</span>
                <div className="flex min-w-0 flex-col gap-1">
                  <h3 className="mb-1 text-xs font-semibold">{member.name}</h3>
                  <a href={`mailto:${member.email}`} className="flex items-center gap-1.5 text-[9px] text-slate-400 transition hover:text-teal-200"><Mail size={14} /> {member.email}</a>
                  <a href={`tel:${member.phoneHref}`} className="flex items-center gap-1.5 text-[9px] text-slate-400 transition hover:text-teal-200"><PhoneCall size={14} /> {member.phone}</a>
                </div>
              </article>
            ))}
          </div>
        </div>
      </div>

      <div className="relative z-10 mx-auto mt-16 flex min-h-16 w-[min(1180px,calc(100%-48px))] items-center justify-between gap-5 border-t border-white/10 text-[9px] text-slate-500 max-md:w-[calc(100%-32px)] max-sm:w-[calc(100%-24px)] max-sm:flex-col max-sm:items-start max-sm:justify-center max-sm:gap-2 max-sm:py-5">
        <span>Wakalah — MENA Ignite Hackathon 2026</span>
        <span>Prototype for demonstration purposes</span>
        <a href="#top" className="flex items-center gap-1.5 text-slate-300 transition hover:text-white">Back to top <ArrowUpRight size={14} /></a>
      </div>
    </footer>
  );
}

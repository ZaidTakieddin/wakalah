export type Tone = "trust" | "danger" | "warning" | "neutral";

export type ScenarioStep = {
  title: string;
  eyebrow: string;
  summary: string;
  bullets: string[];
  visual: string;
  status: string;
};

export type ScenarioStage = {
  number: number;
  label: string;
  happy: ScenarioStep;
  threat: ScenarioStep;
};

export const scenarioStages: ScenarioStage[] = [
  {
    number: 1,
    label: "Request",
    happy: {
      eyebrow: "Mandate created",
      title: "Amina defines a narrow authority",
      summary:
        "Rasheed may send up to 2,000 QAR per month to one approved beneficiary.",
      bullets: ["Scoped remittance only", "Expires automatically", "Bound to Rasheed’s public key"],
      visual: "mandate",
      status: "Mandate active",
    },
    threat: {
      eyebrow: "Suspicious request",
      title: "A cloned agent changes the terms",
      summary:
        "A stolen credential is used to request a transfer to an unknown beneficiary.",
      bullets: ["New beneficiary", "Amount above mandate limit", "Key proof missing"],
      visual: "clone",
      status: "Request challenged",
    },
  },
  {
    number: 2,
    label: "Binding",
    happy: {
      eyebrow: "Identity & mandate checks",
      title: "The agent and mandate match",
      summary:
        "Network-confirmed phone context and operator-record identity evidence support the mandate.",
      bullets: ["Number Verification", "KYC Match", "Proof of possession"],
      visual: "identity",
      status: "Key matched",
    },
    threat: {
      eyebrow: "Hard violation found",
      title: "Proof of possession fails",
      summary:
        "The presenting agent cannot prove control of the private key bound to the mandate.",
      bullets: ["Agent key mismatch", "Beneficiary outside scope", "Amount over limit"],
      visual: "key-fail",
      status: "Critical risk",
    },
  },
  {
    number: 3,
    label: "Intent",
    happy: {
      eyebrow: "Transaction intent",
      title: "Send 450 QAR to the approved beneficiary",
      summary:
        "The external agent submits the intent, context, mandate token, and a fresh signed proof.",
      bullets: ["Action in scope", "Amount in limit", "Token active"],
      visual: "transfer",
      status: "Inside scope",
    },
    threat: {
      eyebrow: "Plan adapts",
      title: "Unnecessary checks stop early",
      summary:
        "Wakalah does not waste time gathering evidence that cannot reverse a hard policy violation.",
      bullets: ["Stop normal flow", "Collect revocation evidence only", "Prepare fail-closed result"],
      visual: "stop-plan",
      status: "Flow contained",
    },
  },
  {
    number: 4,
    label: "Risk",
    happy: {
      eyebrow: "Agent risk proposal",
      title: "LOW risk, with visible reasons",
      summary:
        "The request matches the mandate, the amount is normal, and the beneficiary is pre-approved.",
      bullets: ["Mandate match", "No known anomaly", "Approved behavior"],
      visual: "risk-low",
      status: "Risk: LOW",
    },
    threat: {
      eyebrow: "Network evidence",
      title: "Compromise signals add context",
      summary:
        "A recent SIM swap and device change reinforce the account-takeover hypothesis.",
      bullets: ["Recent SIM swap", "Device changed", "Recorded sandbox response"],
      visual: "signals-bad",
      status: "Signals elevated",
    },
  },
  {
    number: 5,
    label: "Plan",
    happy: {
      eyebrow: "Verification plan",
      title: "Only the required tools are selected",
      summary:
        "The supervisor assembles a controlled plan from the approved CAMARA tool catalog.",
      bullets: ["Current SIM Swap", "Device Swap if required", "Fresh cached evidence if allowed"],
      visual: "api-plan",
      status: "2 checks selected",
    },
    threat: {
      eyebrow: "Agent explanation",
      title: "Evidence becomes an auditable narrative",
      summary:
        "Key mismatch, out-of-scope beneficiary, and recent mobile changes make the recommendation clear.",
      bullets: ["Explain each reason", "Reference evidence", "Recommend deny + revoke"],
      visual: "explain",
      status: "DENY recommended",
    },
  },
  {
    number: 6,
    label: "Evidence",
    happy: {
      eyebrow: "Network evidence",
      title: "Current signals support continuity",
      summary:
        "The approved checks return a consistent, reachable mobile context without recent swaps.",
      bullets: ["No recent SIM swap", "No suspicious device change", "Device reachable"],
      visual: "signals-good",
      status: "Evidence passed",
    },
    threat: {
      eyebrow: "Deterministic policy",
      title: "Fixed rules reject the request",
      summary:
        "The same verified violations always produce the same result—without model improvisation.",
      bullets: ["Key mismatch → DENY", "Outside scope → DENY", "Over limit → DENY"],
      visual: "policy-deny",
      status: "Policy: DENY",
    },
  },
  {
    number: 7,
    label: "Policy",
    happy: {
      eyebrow: "Deterministic policy",
      title: "Every mandatory rule passes",
      summary:
        "A versioned policy engine—not the AI agent—authorizes the relying party to proceed.",
      bullets: ["Signature valid", "Scope and amount valid", "Evidence complete"],
      visual: "policy-allow",
      status: "Policy: ALLOW",
    },
    threat: {
      eyebrow: "Revocation response",
      title: "The mandate is contained",
      summary:
        "The transfer is blocked, the mandate is suspended, and re-verification is required.",
      bullets: ["Transaction blocked", "Mandate suspended", "Principal notification initiated"],
      visual: "revoke",
      status: "Mandate revoked",
    },
  },
  {
    number: 8,
    label: "Outcome",
    happy: {
      eyebrow: "Authorized outcome",
      title: "The transfer completes inside scope",
      summary:
        "The bank receives the ALLOW verdict and evidence reference. The mandate remains active.",
      bullets: ["Transfer accepted", "Audit event created", "Evidence reference recorded"],
      visual: "success",
      status: "Authorized within scope",
    },
    threat: {
      eyebrow: "Contained outcome",
      title: "The attack stops at the trust layer",
      summary:
        "The red transaction path ends before the relying party and a complete audit event is retained.",
      bullets: ["No money moved", "Audit event recorded", "Re-verification required"],
      visual: "blocked",
      status: "Attack stopped",
    },
  },
];

export type NetworkApi = {
  name: string;
  category: "Identity" | "Hijack protection" | "Continuity" | "Context";
  priority: "Core MVP" | "Risk-triggered" | "Context signal";
  stage: string;
  description: string;
  use: string;
  icon: string;
};

export const networkApis: NetworkApi[] = [
  {
    name: "Number Verification",
    category: "Identity",
    priority: "Core MVP",
    stage: "Mandate creation",
    description: "Confirms through the mobile network that the application phone context matches the number being verified.",
    use: "Establish network-confirmed phone context during creation or re-verification.",
    icon: "phone",
  },
  {
    name: "KYC Match",
    category: "Identity",
    priority: "Core MVP",
    stage: "Mandate creation",
    description: "Compares supplied identity attributes with customer information held by the operator.",
    use: "Check consistency between the claimed principal and operator-held KYC records.",
    icon: "badge",
  },
  {
    name: "SIM Swap",
    category: "Hijack protection",
    priority: "Core MVP",
    stage: "Transaction verification",
    description: "Checks whether a SIM change occurred during a specified recent period.",
    use: "Raise risk, require step-up, block a sensitive action, or support revocation.",
    icon: "sim",
  },
  {
    name: "Device Swap",
    category: "Hijack protection",
    priority: "Core MVP",
    stage: "Transaction verification",
    description: "Checks whether a phone number recently moved to a different physical device.",
    use: "Detect suspicious handset changes while the phone number remains the same.",
    icon: "device",
  },
  {
    name: "Call Forwarding Signal",
    category: "Hijack protection",
    priority: "Risk-triggered",
    stage: "Sensitive action",
    description: "Returns active call-forwarding information associated with the phone number.",
    use: "Add interception-risk evidence where voice or OTP recovery paths matter.",
    icon: "forward",
  },
  {
    name: "KYC Tenure",
    category: "Continuity",
    priority: "Risk-triggered",
    stage: "Optional context",
    description: "Verifies how long the subscriber has been associated with the mobile subscription.",
    use: "Add a continuity signal without treating tenure as proof of legitimacy.",
    icon: "clock",
  },
  {
    name: "Number Recycling",
    category: "Continuity",
    priority: "Risk-triggered",
    stage: "Re-verification",
    description: "Checks whether the subscriber associated with a phone number changed after a date.",
    use: "Prevent an old mandate from following a recycled number to a new subscriber.",
    icon: "recycle",
  },
  {
    name: "Device Reachability",
    category: "Context",
    priority: "Context signal",
    stage: "Step-up",
    description: "Checks whether a device is reachable through supported network channels.",
    use: "Add communication context for step-up and sensitive transactions.",
    icon: "signal",
  },
  {
    name: "Roaming Status",
    category: "Context",
    priority: "Context signal",
    stage: "Optional context",
    description: "Checks whether the device is roaming and may return country context.",
    use: "Distinguish legitimate travel from unexpected context and reduce false declines.",
    icon: "globe",
  },
  {
    name: "Location Verification",
    category: "Context",
    priority: "Risk-triggered",
    stage: "High-risk verification",
    description: "Verifies whether a device is inside a requested geographic area, subject to consent and precision.",
    use: "Add geographic consistency evidence for selected high-risk transactions.",
    icon: "location",
  },
];


import type {
  EvidenceSource,
  EvaluateResponse,
  NetworkCheckPresentation,
  WsEvent,
} from "@/lib/types";

type UnknownRecord = Record<string, unknown>;

const sourceLabels: Record<EvidenceSource, string> = {
  live: "Live network",
  cached: "Recent network data",
  replay: "Recorded demo",
  simulated: "Demo simulation",
  unavailable: "Unavailable",
};

const traceTitles: Record<string, string> = {
  classify_risk: "Assessing transfer risk",
  build_plan: "Building the verification plan",
  enforce_floor: "Applying required safeguards",
  gather_evidence: "Collecting security evidence",
  interpret: "Reviewing the evidence",
  decide: "Applying security policy",
};

function asRecord(value: unknown): UnknownRecord {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as UnknownRecord)
    : {};
}

function getNestedResult(payload: UnknownRecord) {
  const response = asRecord(payload.response);
  const result = asRecord(payload.result);

  if (Object.keys(result).length) return result;

  const nested = [response.result, response.data, response.body]
    .map(asRecord)
    .find((candidate) => Object.keys(candidate).length);

  return nested ?? response;
}

function getBoolean(record: UnknownRecord, keys: string[]) {
  for (const key of keys) {
    if (typeof record[key] === "boolean") return record[key] as boolean;
  }
  return undefined;
}

function getNumber(value: unknown) {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() && Number.isFinite(Number(value))) {
    return Number(value);
  }
  return undefined;
}

function getSource(payload: UnknownRecord): EvidenceSource {
  const source = String(payload.source ?? "unavailable").toLowerCase();
  return source in sourceLabels ? (source as EvidenceSource) : "unavailable";
}

function getSignal(payload: UnknownRecord) {
  return String(payload.signal ?? payload.checkName ?? payload.check_name ?? "")
    .toLowerCase()
    .replace(/[\s.-]+/g, "_");
}

function getMaxAge(payload: UnknownRecord) {
  const request = asRecord(payload.request);
  return (
    getNumber(payload.maxAgeHours) ??
    getNumber(payload.maxAge) ??
    getNumber(request.maxAge) ??
    24
  );
}

function isFailed(payload: UnknownRecord, result: UnknownRecord) {
  const status = getNumber(payload.status);
  return Boolean(
    payload.error ||
      result.error ||
      (status !== undefined && status >= 400) ||
      getSource(payload) === "unavailable",
  );
}

function wordsFromKey(key: string) {
  return key
    .replace(/Match$/, "")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/^./, (letter) => letter.toUpperCase());
}

function makePresentation(
  payload: UnknownRecord,
  presentation: Omit<NetworkCheckPresentation, "sourceLabel" | "latencyMs">,
): NetworkCheckPresentation {
  const source = getSource(payload);
  return {
    ...presentation,
    sourceLabel: sourceLabels[source],
    latencyMs: getNumber(payload.latencyMs) ?? null,
  };
}

function numberVerification(payload: UnknownRecord) {
  const result = getNestedResult(payload);
  const title = "Phone ownership (Number Verification)";

  if (isFailed(payload, result)) {
    const code = String(result.code ?? payload.errorCode ?? "");
    const mobileAuthRequired = code.includes(
      "USER_NOT_AUTHENTICATED_BY_MOBILE_NETWORK",
    );
    return makePresentation(payload, {
      title,
      message: mobileAuthRequired
        ? "Phone ownership verification requires mobile-network authentication."
        : "The mobile network could not confirm phone ownership.",
      tone: "warning",
      details: [],
    });
  }

  const verified = getBoolean(result, [
    "devicePhoneNumberVerified",
    "verified",
    "matches",
  ]);

  if (verified === true) {
    return makePresentation(payload, {
      title,
      message: "This number matches the SIM in the current device.",
      tone: "success",
      details: [],
    });
  }

  if (verified === false) {
    return makePresentation(payload, {
      title,
      message: "This number does not match the SIM in the current device.",
      tone: "danger",
      details: [],
    });
  }

  return makePresentation(payload, {
    title,
    message: "The mobile network could not confirm phone ownership.",
    tone: "warning",
    details: [],
  });
}

function numberRecycling(payload: UnknownRecord) {
  const result = getNestedResult(payload);
  const title = "Number ownership history (Number Recycling)";

  if (isFailed(payload, result)) {
    return makePresentation(payload, {
      title,
      message:
        "The mobile network could not confirm whether this phone number changed owners.",
      tone: "warning",
      details: [],
    });
  }

  const recycled = getBoolean(result, [
    "phoneNumberRecycled",
    "recycled",
  ]);

  if (recycled === true) {
    return makePresentation(payload, {
      title,
      message:
        "The mobile network detected that this phone number changed owners after the recorded date.",
      tone: "danger",
      details: [],
    });
  }

  if (recycled === false) {
    return makePresentation(payload, {
      title,
      message:
        "The mobile network confirmed that this phone number has remained with the same owner since the recorded date.",
      tone: "success",
      details: [],
    });
  }

  return makePresentation(payload, {
    title,
    message:
      "The mobile network could not confirm whether this phone number changed owners.",
    tone: "warning",
    details: [],
  });
}

function callForwarding(payload: UnknownRecord) {
  const result = getNestedResult(payload);
  const title = "Call routing security (Call Forwarding Signal)";

  if (isFailed(payload, result)) {
    return makePresentation(payload, {
      title,
      message:
        "The mobile network could not confirm whether unconditional call forwarding is active.",
      tone: "warning",
      details: [],
    });
  }

  const active = getBoolean(result, ["active"]);

  if (active === true) {
    return makePresentation(payload, {
      title,
      message:
        "Unconditional call forwarding is active. Incoming calls may be automatically redirected to another destination.",
      tone: "danger",
      details: [],
    });
  }

  if (active === false) {
    return makePresentation(payload, {
      title,
      message:
        "No unconditional call forwarding was detected. Incoming calls are not being automatically redirected.",
      tone: "success",
      details: [],
    });
  }

  return makePresentation(payload, {
    title,
    message:
      "The mobile network could not confirm whether unconditional call forwarding is active.",
    tone: "warning",
    details: [],
  });
}

function tenure(payload: UnknownRecord) {
  const result = getNestedResult(payload);
  const request = asRecord(payload.request);
  const title = "Customer tenure (KYC Tenure)";

  if (isFailed(payload, result)) {
    return makePresentation(payload, {
      title,
      message:
        "The mobile network could not determine how long this subscription has been active.",
      tone: "warning",
      details: [],
    });
  }

  const confirmed = getBoolean(result, ["tenureDateCheck"]);
  const tenureDate =
    typeof request.tenureDate === "string" ? request.tenureDate : undefined;
  const contractType =
    typeof result.contractType === "string" ? result.contractType : undefined;

  const contractLabels: Record<string, string> = {
    PAYG: "prepaid",
    PAYM: "contract",
    Business: "business",
  };

  const contractMessage = contractType
    ? ` This is a ${contractLabels[contractType] ?? contractType} subscription.`
    : "";
  const period = tenureDate
    ? ` since ${tenureDate}`
    : " for the requested period";

  if (confirmed === true) {
    return makePresentation(payload, {
      title,
      message:
        `The mobile network confirmed that this subscription has been continuously active${period}.` +
        contractMessage,
      tone: "success",
      details: [],
    });
  }

  if (confirmed === false) {
    return makePresentation(payload, {
      title,
      message:
        `The mobile network could not confirm continuous subscription history${period}.` +
        contractMessage,
      tone: "warning",
      details: [],
    });
  }

  return makePresentation(payload, {
    title,
    message:
      "The mobile network could not determine how long this subscription has been active.",
    tone: "warning",
    details: [],
  });
}

function swapPresentation(
  payload: UnknownRecord,
  kind: "sim" | "device",
) {
  const result = getNestedResult(payload);
  const maxAge = getMaxAge(payload);
  const title =
    kind === "sim" ? "SIM security (SIM Swap)" : "Trusted device (Device Swap)";

  if (isFailed(payload, result)) {
    return makePresentation(payload, {
      title,
      message:
        kind === "sim"
          ? "Recent SIM-change history could not be confirmed."
          : "Recent device-change history could not be confirmed.",
      tone: "warning",
      details: [],
    });
  }

  const swapped = getBoolean(result, ["swapped"]);

  if (swapped === true) {
    return makePresentation(payload, {
      title,
      message:
        kind === "sim"
          ? `A SIM replacement was detected within the last ${maxAge} hours.`
          : `This number was used in a different device within the last ${maxAge} hours.`,
      tone: "danger",
      details: [],
    });
  }

  if (swapped === false) {
    return makePresentation(payload, {
      title,
      message:
        kind === "sim"
          ? `No SIM replacement was detected in the last ${maxAge} hours.`
          : `This number has not moved to another device in the last ${maxAge} hours.`,
      tone: "success",
      details: [],
    });
  }

  const dateKey = kind === "sim" ? "latestSimChange" : "latestDeviceChange";
  const latestChange = result[dateKey];
  const monitoredPeriod = getNumber(result.monitoredPeriod);

  if (typeof latestChange === "string" && latestChange) {
    return makePresentation(payload, {
      title,
      message: `${kind === "sim" ? "Last SIM replacement" : "Last device change"} recorded ${new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(latestChange))}.`,
      tone: "warning",
      details: [],
    });
  }

  if (latestChange === null && monitoredPeriod !== undefined) {
    return makePresentation(payload, {
      title,
      message: `No ${kind === "sim" ? "SIM replacement" : "device change"} was recorded during the operator's ${monitoredPeriod}-day observation period.`,
      tone: "success",
      details: [],
    });
  }

  return makePresentation(payload, {
    title,
    message:
      kind === "sim"
        ? "Recent SIM-change history could not be confirmed."
        : "Recent device-change history could not be confirmed.",
    tone: "warning",
    details: [],
  });
}

function kycMatch(payload: UnknownRecord) {
  const result = getNestedResult(payload);
  const title = "Identity match (KYC Match)";

  if (isFailed(payload, result)) {
    return makePresentation(payload, {
      title,
      message: "Identity details could not be checked with the mobile operator.",
      tone: "warning",
      details: [],
    });
  }

  const matches = Object.entries(result).filter(
    ([key, value]) =>
      key.endsWith("Match") &&
      (value === "true" || value === "false" || value === "not_available"),
  ) as Array<[string, "true" | "false" | "not_available"]>;

  if (!matches.length) {
    return makePresentation(payload, {
      title,
      message: "Identity details could not be checked with the mobile operator.",
      tone: "warning",
      details: [],
    });
  }

  const details = matches.map(([key, value]) => {
    const label = wordsFromKey(key);
    if (value === "true") return `${label} matched`;
    if (value === "false") return `${label} did not match`;
    return `${label} could not be checked`;
  });

  if (matches.some(([, value]) => value === "false")) {
    return makePresentation(payload, {
      title,
      message: "Some identity details do not match the mobile operator's records.",
      tone: "danger",
      details,
    });
  }

  if (matches.some(([, value]) => value === "not_available")) {
    return makePresentation(payload, {
      title,
      message: "The mobile operator could not compare all requested identity details.",
      tone: "warning",
      details,
    });
  }

  return makePresentation(payload, {
    title,
    message: "The customer's identity details match the mobile operator's records.",
    tone: "success",
    details,
  });
}

export function getNetworkCheckPresentation(
  event: WsEvent,
): NetworkCheckPresentation {
  const payload = asRecord(event.payload);
  const signal = getSignal(payload);

  if (signal === "number_recycling") {
    return numberRecycling(payload);
  }
  if (signal === "call_forwarding") {
    return callForwarding(payload);
  }
  if (signal === "tenure") {
    return tenure(payload);
  }
  if (signal.includes("number") && signal.includes("verification")) {
    return numberVerification(payload);
  }
  if (signal.includes("device") && signal.includes("swap")) {
    return swapPresentation(payload, "device");
  }
  if (signal.includes("sim") && signal.includes("swap")) {
    return swapPresentation(payload, "sim");
  }
  if (signal.includes("kyc") || signal.includes("identity")) {
    return kycMatch(payload);
  }

  return makePresentation(payload, {
    title: "Network evidence (Nokia Network as Code)",
    message: "The mobile network returned additional security evidence.",
    tone: "warning",
    details: [],
  });
}

export function getTracePresentation(event: WsEvent) {
  const payload = asRecord(event.payload);
  const step = String(payload.step ?? "");
  return {
    title: traceTitles[step] ?? "Reviewing transaction security",
    summary:
      typeof payload.summary === "string"
        ? payload.summary
        : "WAKALAH is reviewing the transfer.",
    brain: typeof payload.brain === "string" ? payload.brain : null,
    degraded: payload.degraded === true,
  };
}

export function getEventTransactionId(event: WsEvent) {
  const payload = asRecord(event.payload);
  const value = payload.transactionId ?? payload.transaction_id;
  return typeof value === "string" ? value : null;
}

export function isEvaluateResponse(value: unknown): value is EvaluateResponse {
  const record = asRecord(value);
  return (
    typeof record.transactionId === "string" &&
    typeof record.decision === "string"
  );
}

export function normalizeDecision(value: string) {
  const decision = value.toLowerCase();
  if (decision === "allow") return "allow" as const;
  if (decision === "deny") return "deny" as const;
  return "challenge" as const;
}

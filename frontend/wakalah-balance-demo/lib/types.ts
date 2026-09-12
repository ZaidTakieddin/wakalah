export type Decision = "allow" | "challenge" | "deny";
export type RiskTier = "low" | "medium" | "high";

export type EvidenceSource =
  | "live"
  | "cached"
  | "replay"
  | "simulated"
  | "unavailable";

export type SignalEvidence = {
  dimension: string;
  result: Record<string, unknown>;
  source: EvidenceSource;
  available: boolean;
  errorCode: string | null;
};

export type MandateStatus = "idle" | "loading" | "error" | "success";
export type ConnectionStatus = "connecting" | "connected" | "disconnected";

export type TransferStatus =
  | "completed"
  | "challenge"
  | "denied"
  | "failed";

export type TransferRecord = {
  id: string;
  transactionId: string;
  beneficiaryId: string;
  beneficiaryName: string;
  amount: number;
  currency: "USD";
  status: TransferStatus;
  isNewRecipient: boolean;
  requestedAt: string;
};

export type MandateResponse = {
  mandateId: string;
  principalId: string;
  agentId: string;
  status: "active" | "revoked";
  amountLimit: number;
  currency: string;
  beneficiaryIds: string[];
  createdAt: string;
};

export type EvaluateTransactionInput = {
  transactionId: string;
  mandateId: string;
  amount: number;
  currency: "USD";
  beneficiaryId: string;
  beneficiaryIsNew: boolean;
};

export type EvaluateResponse = {
  transactionId: string;
  decision: Decision;
  riskTier: RiskTier;
  reasonCodes: string[];
  rationale: string;
  evidenceSummary: Record<string, SignalEvidence>;
  challenge: { challengeId: string; method: string } | null;
  policyVersion: string;
  agentProposal: Decision | null;
  policyOverrodeAgent: boolean;
  decidedAt: string;
  latencyMs: number | null;
  beatId: string | null;
};

export type WsEvent<T = Record<string, unknown>> = {
  type: string;
  ts: string;
  payload: T;
};

export type EvaluationRun = {
  transactionId: string;
  action: string;
  phoneNumber: string;
  beneficiaryId: string;
  beneficiaryName: string;
  amount: number;
  isNewRecipient: boolean;
  startedAt: string;
  status: "running" | "completed" | "failed";
  events: WsEvent[];
  decision: EvaluateResponse | null;
  error: string | null;
};

export type NetworkCheckPresentation = {
  title: string;
  message: string;
  tone: "success" | "danger" | "warning" | "progress";
  sourceLabel: string;
  details: string[];
  latencyMs: number | null;
};

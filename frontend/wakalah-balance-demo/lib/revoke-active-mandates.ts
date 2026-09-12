import { listMandates, revokeMandate } from "@/actions/wakalah";

/**
 * Demo hygiene: clears out any mandate left active from a previous run so
 * the next session/beat starts clean. Silently no-ops on failure — this is
 * best-effort cleanup, not a user-facing action.
 */
export async function revokeActiveMandates(reason: string) {
  const result = await listMandates();
  if (!result.ok) return;

  const active = result.data.filter((m) => m.status === "active");
  await Promise.all(active.map((m) => revokeMandate(m.mandateId, reason)));
}
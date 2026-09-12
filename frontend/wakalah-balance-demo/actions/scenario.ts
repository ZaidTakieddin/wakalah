"use server";

const API_URL = process.env.WAKALAH_API_BASE;

if (!API_URL) {
  throw new Error("WAKALAH_API_BASE is not configured");
}

export type ScenarioBeat = {
  id: string;
  title: string;
  narration: string;
  expect: string;
  labels: string[];
  kind: "mandate" | "transaction" | "operator_event";
  done: boolean;
};

export type Scenario = {
  beats: ScenarioBeat[];
  mandateId: string | null;
  results: unknown[];
};

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const error = await response.json();

      if (error?.detail) {
        message = error.detail;
      }
    } catch {
      // Ignore invalid/non-JSON error responses.
    }

    throw new Error(message);
  }

  return response.json();
}

export async function getScenario(): Promise<Scenario> {
  return request<Scenario>("/v1/scenario");
}

export async function runScenarioBeat(
  beatId: string,
): Promise<Scenario> {
  return request<Scenario>(`/v1/scenario/beats/${beatId}`, {
    method: "POST",
  });
}

export async function resetScenario(): Promise<Scenario> {
  return request<Scenario>("/v1/scenario/reset", {
    method: "POST",
  });
}

export async function runAllScenarioBeats(): Promise<Scenario> {
  return request<Scenario>("/v1/scenario/run-all", {
    method: "POST",
  });
}
const apiBase = "";

async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  if (!text) {
    return undefined as T;
  }
  return JSON.parse(text) as T;
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${apiBase}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || res.statusText);
  }
  return parseJson<T>(res);
}

export type User = {
  id: number;
  telegram_id: number;
  locale: string;
  created_at: string;
};

export type Cat = {
  id: number;
  user_id: number;
  name: string;
  weight_kg: string | null;
  notes: string | null;
  created_at: string;
};

export type ScenarioRun = {
  id: number;
  cat_id: number;
  scenario_type: string;
  status: string;
  started_at: string;
  context: Record<string, unknown> | null;
};

export type Reminder = {
  id: number;
  cat_id: number;
  scenario_run_id: number | null;
  kind: string;
  message_key: string;
  run_at: string;
  sent_at: string | null;
  cancelled: boolean;
  payload: Record<string, unknown> | null;
};

export async function authTelegram(initData: string): Promise<User> {
  return apiFetch<User>("/api/auth/telegram", {
    method: "POST",
    body: JSON.stringify({ init_data: initData }),
  });
}

export async function loadMe(): Promise<User> {
  return apiFetch<User>("/api/me");
}

export async function patchLocale(locale: string): Promise<User> {
  return apiFetch<User>("/api/me/locale", {
    method: "PATCH",
    body: JSON.stringify({ locale }),
  });
}

export async function listCats(): Promise<Cat[]> {
  return apiFetch<Cat[]>("/api/cats");
}

export async function createCat(body: {
  name: string;
  weight_kg?: string | null;
  notes?: string | null;
}): Promise<Cat> {
  return apiFetch<Cat>("/api/cats", { method: "POST", body: JSON.stringify(body) });
}

export async function updateCat(
  id: number,
  body: { name?: string; weight_kg?: string | null; notes?: string | null },
): Promise<Cat> {
  return apiFetch<Cat>(`/api/cats/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function deleteCat(id: number): Promise<void> {
  const res = await fetch(`${apiBase}/api/cats/${id}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
}

export async function listScenarios(catId: number): Promise<ScenarioRun[]> {
  return apiFetch<ScenarioRun[]>(`/api/cats/${catId}/scenarios`);
}

export async function startScenario(
  catId: number,
  body: {
    scenario_type: string;
    anchor_at?: string | null;
    context?: Record<string, unknown> | null;
  },
): Promise<ScenarioRun> {
  return apiFetch<ScenarioRun>(`/api/cats/${catId}/scenarios`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function cancelScenario(catId: number, runId: number): Promise<ScenarioRun> {
  return apiFetch<ScenarioRun>(`/api/cats/${catId}/scenarios/${runId}/cancel`, {
    method: "POST",
  });
}

export async function listReminders(catId: number): Promise<Reminder[]> {
  return apiFetch<Reminder[]>(`/api/cats/${catId}/reminders`);
}

export async function listUpcomingReminders(): Promise<Reminder[]> {
  return apiFetch<Reminder[]>("/api/reminders/upcoming");
}

export async function listDrugs(): Promise<{ drugs: string[] }> {
  return apiFetch("/api/dosage/drugs");
}

export async function calcDosage(body: {
  drug_slug: string;
  weight_kg: string;
  use: string;
}): Promise<{ mg: string }> {
  return apiFetch("/api/dosage/calculate", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function templateSterilization(): Promise<{ text: string }> {
  return apiFetch("/api/templates/sterilization_clinic");
}

export async function templateAdopter(): Promise<{ text: string }> {
  return apiFetch("/api/templates/potential_adopter_questions");
}

export async function templatePost(): Promise<{ text: string }> {
  return apiFetch("/api/templates/post_structure");
}

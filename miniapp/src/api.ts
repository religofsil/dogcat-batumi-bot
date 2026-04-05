import { agentDebugLog } from "./agentDebugLog";
import { compressImageForUpload } from "./compressImageForUpload";

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
  /** ISO-like time from API, e.g. "09:00:00" */
  daily_reminder_time: string;
  created_at: string;
};

export type CatOrganization = "catebi" | "dogcat_batumi" | "dogcat_tbilisi" | "none";

export type Cat = {
  id: number;
  user_id: number;
  name: string;
  weight_kg: string | null;
  notes: string | null;
  photo_url: string | null;
  organization: CatOrganization;
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

/** `hm` from `<input type="time">` is usually "HH:MM"; API accepts "HH:MM:00". */
export async function patchDailyReminderTime(hm: string): Promise<User> {
  const daily_reminder_time = hm.length === 5 ? `${hm}:00` : hm;
  return apiFetch<User>("/api/me/daily-reminder-time", {
    method: "PATCH",
    body: JSON.stringify({ daily_reminder_time }),
  });
}

export async function listCats(): Promise<Cat[]> {
  return apiFetch<Cat[]>("/api/cats");
}

export async function createCat(body: {
  name: string;
  weight_kg?: string | null;
  notes?: string | null;
  organization?: CatOrganization;
}): Promise<Cat> {
  return apiFetch<Cat>("/api/cats", { method: "POST", body: JSON.stringify(body) });
}

export async function updateCat(
  id: number,
  body: {
    name?: string;
    weight_kg?: string | null;
    notes?: string | null;
    organization?: CatOrganization;
  },
): Promise<Cat> {
  return apiFetch<Cat>(`/api/cats/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function uploadCatPhoto(catId: number, file: File): Promise<Cat> {
  const prepared = await compressImageForUpload(file);
  // #region agent log
  agentDebugLog({
    location: "api.ts:uploadCatPhoto",
    message: "after compress, before fetch",
    data: {
      catId,
      originalSize: file.size,
      preparedSize: prepared.size,
      preparedType: prepared.type,
    },
    hypothesisId: "H1-H2",
  });
  // #endregion
  const fd = new FormData();
  fd.append("file", prepared);
  const res = await fetch(`${apiBase}/api/cats/${catId}/photo`, {
    method: "POST",
    credentials: "include",
    body: fd,
  });
  // #region agent log
  agentDebugLog({
    location: "api.ts:uploadCatPhoto",
    message: "fetch response",
    data: { catId, status: res.status, ok: res.ok },
    hypothesisId: "H1-H3",
  });
  // #endregion
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return parseJson<Cat>(res);
}

export async function deleteCatPhoto(catId: number): Promise<Cat> {
  return apiFetch<Cat>(`/api/cats/${catId}/photo`, { method: "DELETE" });
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

import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  authTelegram,
  calcDosage,
  cancelScenario,
  createCat,
  deleteCat,
  listCats,
  listDrugs,
  listReminders,
  listScenarios,
  listUpcomingReminders,
  loadMe,
  patchLocale,
  startScenario,
  templateAdopter,
  templatePost,
  templateSterilization,
  updateCat,
  type Cat,
  type Reminder,
  type ScenarioRun,
  type User,
} from "./api";
import i18n from "./i18n";

type ScenarioChoice =
  | "new_capture"
  | "adopted_home"
  | "post_prep"
  | "potential_adopter"
  | "sterilization";

export default function App() {
  const { t } = useTranslation();
  const [status, setStatus] = useState<string>(() => i18n.t("auth"));
  const [user, setUser] = useState<User | null>(null);
  const [cats, setCats] = useState<Cat[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [runs, setRuns] = useState<ScenarioRun[]>([]);
  const [rems, setRems] = useState<Reminder[]>([]);
  const [upcoming, setUpcoming] = useState<Reminder[]>([]);
  const [drugs, setDrugs] = useState<string[]>([]);
  const [drug, setDrug] = useState<string>("");
  const [doseWeight, setDoseWeight] = useState<string>("");
  const [doseMg, setDoseMg] = useState<string>("");
  const [newName, setNewName] = useState("");
  const [newWeight, setNewWeight] = useState("");
  const [newNotes, setNewNotes] = useState("");
  const [scenarioPick, setScenarioPick] = useState<ScenarioChoice | "">("");
  const [opLocal, setOpLocal] = useState("");
  const [delayDays, setDelayDays] = useState("2");
  const [tpl, setTpl] = useState<Record<string, string>>({});

  const selected = useMemo(
    () => cats.find((c) => c.id === selectedId) || null,
    [cats, selectedId],
  );

  async function refreshCats() {
    setCats(await listCats());
  }

  async function refreshCatDetails(catId: number) {
    const [r, m] = await Promise.all([listScenarios(catId), listReminders(catId)]);
    setRuns(r);
    setRems(m);
  }

  useEffect(() => {
    const tw = window.Telegram?.WebApp;
    tw?.ready();
    tw?.expand();
    const init = tw?.initData || "";
    (async () => {
      try {
        if (!init) {
          setStatus(i18n.t("authFail"));
          return;
        }
        await authTelegram(init);
        const me = await loadMe();
        setUser(me);
        await i18n.changeLanguage(me.locale);
        setStatus("");
        await refreshCats();
        setUpcoming(await listUpcomingReminders());
        const d = await listDrugs();
        setDrugs(d.drugs);
        setDrug(d.drugs[0] || "");
      } catch {
        setStatus(i18n.t("authFail"));
      }
    })();
  }, []);

  useEffect(() => {
    if (selectedId) {
      void refreshCatDetails(selectedId);
    } else {
      setRuns([]);
      setRems([]);
    }
  }, [selectedId]);

  async function onLocaleChange(code: string) {
    await i18n.changeLanguage(code);
    if (user) {
      const u = await patchLocale(code);
      setUser(u);
    }
  }

  async function onAddCat() {
    if (!newName.trim()) return;
    await createCat({
      name: newName.trim(),
      weight_kg: newWeight ? newWeight : null,
      notes: newNotes || null,
    });
    setNewName("");
    setNewWeight("");
    setNewNotes("");
    await refreshCats();
  }

  async function onSaveCat(cat: Cat) {
    await updateCat(cat.id, {
      name: cat.name,
      weight_kg: cat.weight_kg,
      notes: cat.notes,
    });
    await refreshCats();
  }

  async function onDeleteCat(id: number) {
    await deleteCat(id);
    if (selectedId === id) setSelectedId(null);
    await refreshCats();
  }

  async function onStartScenario() {
    if (!selected || !scenarioPick) return;
    const body: {
      scenario_type: string;
      anchor_at?: string | null;
      context?: Record<string, unknown> | null;
    } = { scenario_type: scenarioPick };
    if (scenarioPick === "sterilization") {
      if (!opLocal) {
        window.Telegram?.WebApp?.showAlert("Pick operation date/time");
        return;
      }
      body.context = { operation_at: opLocal };
    }
    if (scenarioPick === "post_prep") {
      body.context = { post_delay_days: Number(delayDays || 2) };
    }
    await startScenario(selected.id, body);
    setScenarioPick("");
    setOpLocal("");
    await refreshCatDetails(selected.id);
    setUpcoming(await listUpcomingReminders());
  }

  async function onCancelRun(run: ScenarioRun) {
    if (!selected) return;
    await cancelScenario(selected.id, run.id);
    await refreshCatDetails(selected.id);
    setUpcoming(await listUpcomingReminders());
  }

  async function onCalc() {
    if (!drug || !doseWeight) return;
    const out = await calcDosage({
      drug_slug: drug,
      weight_kg: doseWeight,
      use: "mid",
    });
    setDoseMg(out.mg);
  }

  async function loadTemplates() {
    const [a, b, c] = await Promise.all([
      templateSterilization(),
      templateAdopter(),
      templatePost(),
    ]);
    setTpl({
      sterilization: a.text,
      adopter: b.text,
      post: c.text,
    });
  }

  async function copyText(key: string) {
    const text = tpl[key];
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      window.Telegram?.WebApp?.showAlert(t("copied"));
    } catch {
      window.Telegram?.WebApp?.showAlert(text);
    }
  }

  return (
    <div className="app">
      <h1>{t("title")}</h1>
      {status ? <div className="card">{status}</div> : null}

      <div className="card stack">
        <label>{t("locale")}</label>
        <select
          value={user?.locale || "en"}
          onChange={(e) => void onLocaleChange(e.target.value)}
        >
          <option value="en">English</option>
          <option value="ru">Русский</option>
          <option value="ka">ქართული</option>
        </select>
      </div>

      <div className="card stack">
        <strong>{t("cats")}</strong>
        <div className="row">
          <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder={t("name")} />
        </div>
        <div className="row">
          <input
            value={newWeight}
            onChange={(e) => setNewWeight(e.target.value)}
            placeholder={t("weight")}
            inputMode="decimal"
          />
        </div>
        <div className="row">
          <textarea
            rows={2}
            value={newNotes}
            onChange={(e) => setNewNotes(e.target.value)}
            placeholder={t("notes")}
          />
        </div>
        <button type="button" onClick={() => void onAddCat()}>
          {t("addCat")}
        </button>
        <div className="stack" style={{ marginTop: 8 }}>
          {cats.map((c) => (
            <div key={c.id} className="row" style={{ justifyContent: "space-between" }}>
              <button type="button" className="secondary" onClick={() => setSelectedId(c.id)}>
                {c.name}
              </button>
              <button type="button" className="danger" onClick={() => void onDeleteCat(c.id)}>
                {t("delete")}
              </button>
            </div>
          ))}
        </div>
      </div>

      {selected ? (
        <div className="card stack">
          <strong>{selected.name}</strong>
          <label>{t("weight")}</label>
          <input
            value={selected.weight_kg ?? ""}
            onChange={(e) =>
              setCats(
                cats.map((x) =>
                  x.id === selected.id ? { ...x, weight_kg: e.target.value || null } : x,
                ),
              )
            }
          />
          <label>{t("notes")}</label>
          <textarea
            rows={3}
            value={selected.notes ?? ""}
            onChange={(e) =>
              setCats(
                cats.map((x) =>
                  x.id === selected.id ? { ...x, notes: e.target.value || null } : x,
                ),
              )
            }
          />
          <button type="button" onClick={() => void onSaveCat(selected)}>
            {t("save")}
          </button>

          <hr style={{ border: 0, borderTop: "1px solid rgba(255,255,255,0.08)" }} />

          <strong>{t("scenarios")}</strong>
          <div className="small muted">
            {runs
              .filter((r) => r.status === "active")
              .map((r) => (
                <div key={r.id} className="row" style={{ justifyContent: "space-between" }}>
                  <span>
                    {t(`scenario_${r.scenario_type}` as never)} · #{r.id}
                  </span>
                  <button type="button" className="secondary" onClick={() => void onCancelRun(r)}>
                    {t("cancelScenario")}
                  </button>
                </div>
              ))}
          </div>
          <label>{t("startScenario")}</label>
          <select
            value={scenarioPick}
            onChange={(e) => setScenarioPick(e.target.value as ScenarioChoice | "")}
          >
            <option value="">—</option>
            <option value="new_capture">{t("scenario_new_capture")}</option>
            <option value="adopted_home">{t("scenario_adopted_home")}</option>
            <option value="post_prep">{t("scenario_post_prep")}</option>
            <option value="potential_adopter">{t("scenario_potential_adopter")}</option>
            <option value="sterilization">{t("scenario_sterilization")}</option>
          </select>
          {scenarioPick === "sterilization" ? (
            <div className="stack">
              <label>{t("opTime")}</label>
              <input type="datetime-local" value={opLocal} onChange={(e) => setOpLocal(e.target.value)} />
            </div>
          ) : null}
          {scenarioPick === "post_prep" ? (
            <div className="stack">
              <label>{t("delayDays")}</label>
              <input value={delayDays} onChange={(e) => setDelayDays(e.target.value)} inputMode="numeric" />
            </div>
          ) : null}
          <button type="button" onClick={() => void onStartScenario()}>
            {t("startScenario")}
          </button>

          <hr style={{ border: 0, borderTop: "1px solid rgba(255,255,255,0.08)" }} />

          <strong>{t("reminders")}</strong>
          <div className="small stack">
            {rems.map((r) => (
              <div key={r.id} className="muted">
                {new Date(r.run_at).toLocaleString()} — {r.kind}{" "}
                {r.sent_at ? "✓" : ""}
                {r.cancelled ? " (cancelled)" : ""}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="card stack">
        <strong>{t("upcoming")}</strong>
        <div className="small stack">
          {upcoming.map((r) => (
            <div key={r.id} className="muted">
              cat #{r.cat_id} · {new Date(r.run_at).toLocaleString()} · {r.kind}
            </div>
          ))}
        </div>
      </div>

      <div className="card stack">
        <strong>{t("dosage")}</strong>
        <p className="small muted">{t("disclaimer")}</p>
        <label>{t("drug")}</label>
        <select value={drug} onChange={(e) => setDrug(e.target.value)}>
          {drugs.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
        <label>{t("weight")}</label>
        <input value={doseWeight} onChange={(e) => setDoseWeight(e.target.value)} inputMode="decimal" />
        <button type="button" onClick={() => void onCalc()}>
          {t("calc")}
        </button>
        {doseMg ? (
          <div>
            {t("resultMg")}: <strong>{doseMg}</strong>
          </div>
        ) : null}
      </div>

      <div className="card stack">
        <strong>{t("templates")}</strong>
        <button type="button" className="secondary" onClick={() => void loadTemplates()}>
          {t("templates")}
        </button>
        {tpl.sterilization ? (
          <div className="stack">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span>{t("sterilizationMsg")}</span>
              <button type="button" onClick={() => void copyText("sterilization")}>
                {t("copy")}
              </button>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span>{t("adopterQs")}</span>
              <button type="button" onClick={() => void copyText("adopter")}>
                {t("copy")}
              </button>
            </div>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span>{t("postStruct")}</span>
              <button type="button" onClick={() => void copyText("post")}>
                {t("copy")}
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

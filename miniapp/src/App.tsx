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
  const [boot, setBoot] = useState<"loading" | "ready" | "error">("loading");
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
          setBoot("error");
          return;
        }
        await authTelegram(init);
        const me = await loadMe();
        setUser(me);
        await i18n.changeLanguage(me.locale);
        await refreshCats();
        setUpcoming(await listUpcomingReminders());
        const d = await listDrugs();
        setDrugs(d.drugs);
        setDrug(d.drugs[0] || "");
        setBoot("ready");
      } catch {
        setBoot("error");
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
      <header className="app__header">
        <p className="brand-mark">Catebi</p>
        <p className="brand-tagline">{t("brandSubtitle")}</p>
        <h1 className="app__title">{t("title")}</h1>
      </header>

      <main className="app__main">
        {boot === "loading" ? (
          <div className="card card--status" role="status" aria-busy="true">
            <span className="text-muted">{t("auth")}</span>
          </div>
        ) : null}

        {boot === "error" ? (
          <div className="card card--status">
            <span className="text-error">{t("authFail")}</span>
          </div>
        ) : null}

        {boot === "ready" ? (
          <>
            <section className="card stack">
              <span className="card__title">{t("locale")}</span>
              <select
                className="select"
                value={user?.locale || "en"}
                onChange={(e) => void onLocaleChange(e.target.value)}
              >
                <option value="en">English</option>
                <option value="ru">Русский</option>
                <option value="ka">ქართული</option>
              </select>
            </section>

            <section className="card stack">
              <span className="card__title">{t("cats")}</span>
              <div>
                <label className="field__label" htmlFor="new-cat-name">
                  {t("name")}
                </label>
                <input
                  id="new-cat-name"
                  className="input"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder={t("name")}
                />
              </div>
              <div>
                <label className="field__label" htmlFor="new-cat-weight">
                  {t("weight")}
                </label>
                <input
                  id="new-cat-weight"
                  className="input"
                  value={newWeight}
                  onChange={(e) => setNewWeight(e.target.value)}
                  placeholder={t("weight")}
                  inputMode="decimal"
                />
              </div>
              <div>
                <label className="field__label" htmlFor="new-cat-notes">
                  {t("notes")}
                </label>
                <textarea
                  id="new-cat-notes"
                  className="textarea"
                  rows={2}
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                  placeholder={t("notes")}
                />
              </div>
              <button type="button" className="btn btn--primary btn--block" onClick={() => void onAddCat()}>
                {t("addCat")}
              </button>
              <div className="stack stack--sm" style={{ marginTop: "var(--space-2)" }}>
                {cats.map((c) => (
                  <div key={c.id} className="cat-row">
                    <button
                      type="button"
                      className="btn btn--ghost btn--block"
                      onClick={() => setSelectedId(c.id)}
                    >
                      {c.name}
                    </button>
                    <button
                      type="button"
                      className="btn btn--danger"
                      onClick={() => void onDeleteCat(c.id)}
                    >
                      {t("delete")}
                    </button>
                  </div>
                ))}
              </div>
            </section>

            {selected ? (
              <section className="card stack">
                <span className="card__title">{selected.name}</span>
                <div>
                  <label className="field__label" htmlFor="cat-weight">
                    {t("weight")}
                  </label>
                  <input
                    id="cat-weight"
                    className="input"
                    value={selected.weight_kg ?? ""}
                    onChange={(e) =>
                      setCats(
                        cats.map((x) =>
                          x.id === selected.id ? { ...x, weight_kg: e.target.value || null } : x,
                        ),
                      )
                    }
                  />
                </div>
                <div>
                  <label className="field__label" htmlFor="cat-notes">
                    {t("notes")}
                  </label>
                  <textarea
                    id="cat-notes"
                    className="textarea"
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
                </div>
                <button type="button" className="btn btn--primary btn--block" onClick={() => void onSaveCat(selected)}>
                  {t("save")}
                </button>

                <hr className="divider" />

                <span className="card__title">{t("scenarios")}</span>
                <div className="stack stack--sm">
                  {runs
                    .filter((r) => r.status === "active")
                    .map((r) => (
                      <div key={r.id} className="row row--between scenario-active">
                        <span>
                          {t(`scenario_${r.scenario_type}` as never)} · #{r.id}
                        </span>
                        <button type="button" className="btn btn--secondary" onClick={() => void onCancelRun(r)}>
                          {t("cancelScenario")}
                        </button>
                      </div>
                    ))}
                </div>
                <div>
                  <label className="field__label" htmlFor="scenario-type">
                    {t("startScenario")}
                  </label>
                  <select
                    id="scenario-type"
                    className="select"
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
                </div>
                {scenarioPick === "sterilization" ? (
                  <div>
                    <label className="field__label" htmlFor="op-time">
                      {t("opTime")}
                    </label>
                    <input
                      id="op-time"
                      className="input"
                      type="datetime-local"
                      value={opLocal}
                      onChange={(e) => setOpLocal(e.target.value)}
                    />
                  </div>
                ) : null}
                {scenarioPick === "post_prep" ? (
                  <div>
                    <label className="field__label" htmlFor="delay-days">
                      {t("delayDays")}
                    </label>
                    <input
                      id="delay-days"
                      className="input"
                      value={delayDays}
                      onChange={(e) => setDelayDays(e.target.value)}
                      inputMode="numeric"
                    />
                  </div>
                ) : null}
                <button type="button" className="btn btn--primary btn--block" onClick={() => void onStartScenario()}>
                  {t("startScenario")}
                </button>

                <hr className="divider" />

                <span className="card__title">{t("reminders")}</span>
                <div className="stack stack--sm">
                  {rems.map((r) => (
                    <div key={r.id} className="reminder-line">
                      {new Date(r.run_at).toLocaleString()} — {r.kind}
                      {r.sent_at ? <span className="text-success"> ✓</span> : null}
                      {r.cancelled ? <span className="text-muted"> (cancelled)</span> : null}
                    </div>
                  ))}
                </div>
              </section>
            ) : null}

            <section className="card stack">
              <span className="card__title">{t("upcoming")}</span>
              <div className="stack stack--sm">
                {upcoming.map((r) => (
                  <div key={r.id} className="reminder-line">
                    cat #{r.cat_id} · {new Date(r.run_at).toLocaleString()} · {r.kind}
                  </div>
                ))}
              </div>
            </section>

            <section className="card stack">
              <span className="card__title">{t("dosage")}</span>
              <p className="text-small text-muted">{t("disclaimer")}</p>
              <div>
                <label className="field__label" htmlFor="drug-select">
                  {t("drug")}
                </label>
                <select id="drug-select" className="select" value={drug} onChange={(e) => setDrug(e.target.value)}>
                  {drugs.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="field__label" htmlFor="dose-weight">
                  {t("weight")}
                </label>
                <input
                  id="dose-weight"
                  className="input"
                  value={doseWeight}
                  onChange={(e) => setDoseWeight(e.target.value)}
                  inputMode="decimal"
                />
              </div>
              <button type="button" className="btn btn--primary btn--block" onClick={() => void onCalc()}>
                {t("calc")}
              </button>
              {doseMg ? (
                <div className="dose-result">
                  {t("resultMg")}: <strong>{doseMg}</strong>
                </div>
              ) : null}
            </section>

            <section className="card stack">
              <span className="card__title">{t("templates")}</span>
              <button type="button" className="btn btn--secondary btn--block" onClick={() => void loadTemplates()}>
                {t("templates")}
              </button>
              {tpl.sterilization ? (
                <div className="stack stack--sm">
                  <div className="template-row">
                    <span>{t("sterilizationMsg")}</span>
                    <button type="button" className="btn btn--primary" onClick={() => void copyText("sterilization")}>
                      {t("copy")}
                    </button>
                  </div>
                  <div className="template-row">
                    <span>{t("adopterQs")}</span>
                    <button type="button" className="btn btn--primary" onClick={() => void copyText("adopter")}>
                      {t("copy")}
                    </button>
                  </div>
                  <div className="template-row">
                    <span>{t("postStruct")}</span>
                    <button type="button" className="btn btn--primary" onClick={() => void copyText("post")}>
                      {t("copy")}
                    </button>
                  </div>
                </div>
              ) : null}
            </section>
          </>
        ) : null}
      </main>

      <footer className="app__footer">
        <p className="footer-credit">{t("footerCredit")}</p>
        <a
          className="footer-link"
          href="https://github.com/catebi"
          target="_blank"
          rel="noopener noreferrer"
        >
          {t("footerGithub")}
        </a>
      </footer>
    </div>
  );
}

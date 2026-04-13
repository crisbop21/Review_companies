// Earnings Podcast Agent — Claude Artifact (single-file React).
//
// Drop this into a Claude Artifact. It talks to a backend that exposes two
// endpoints:
//   POST /api/pipeline/run        -> runs Steps 1-7 (+9 if prior run exists)
//   POST /api/decisions           -> append-only decision log
//
// The backend is expected to proxy to the Python orchestrator + Supabase.
// If PIPELINE_ENDPOINT is unset, the artifact runs in UI-only "demo mode".

import React, { useMemo, useState } from "react";

const PIPELINE_ENDPOINT =
  (typeof window !== "undefined" && window.PIPELINE_ENDPOINT) || "";

const ACTIONS = ["buy", "add", "trim", "exit", "pass", "hold"];

function Tabs({ tabs, active, onChange }) {
  return (
    <div className="flex gap-2 border-b border-gray-200 mb-4">
      {tabs.map((t) => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={`px-3 py-2 text-sm font-medium border-b-2 ${
            active === t.id
              ? "border-indigo-600 text-indigo-700"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

function MemoCard({ memo }) {
  if (!memo) return <div className="text-gray-500">No memo yet.</div>;
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Thesis</h3>
        <p>{memo.thesis_summary}</p>
      </div>
      <div className="grid grid-cols-4 gap-4">
        <Stat label="Bull" value={memo.bull_score} />
        <Stat label="Bear" value={memo.bear_score} />
        <Stat label="Size %" value={memo.suggested_size_pct ?? "—"} />
        <Stat label="Horizon" value={memo.time_horizon ?? "—"} />
      </div>
      <div>
        <h3 className="text-lg font-semibold">Assumptions</h3>
        {(memo.key_assumptions || []).map((a, i) => (
          <div key={i} className="border rounded p-3 my-2">
            <div className="font-medium">{a.text}</div>
            <div className="text-xs text-gray-500">
              Confidence {a.confidence} / 10
            </div>
            {a.rationale && <div className="text-sm mt-1">{a.rationale}</div>}
          </div>
        ))}
      </div>
      <div>
        <h3 className="text-lg font-semibold">Kill conditions</h3>
        {(memo.kill_conditions || []).map((k, i) => (
          <div key={i} className="border rounded p-3 my-2">
            <div className="font-medium">{k.condition_text}</div>
            <div className="text-xs text-gray-500">
              {k.metric_name} {k.threshold_direction} {k.threshold_value}
            </div>
          </div>
        ))}
      </div>
      <div>
        <h3 className="text-lg font-semibold">Memo</h3>
        <p className="whitespace-pre-wrap">{memo.memo_text}</p>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="border rounded p-3">
      <div className="text-xs uppercase tracking-wide text-gray-500">
        {label}
      </div>
      <div className="text-2xl font-semibold">{value}</div>
    </div>
  );
}

function DecisionForm({ memo, companyId, memoId, onSubmitted }) {
  const [action, setAction] = useState("buy");
  const [conviction, setConviction] = useState(5);
  const [sizePct, setSizePct] = useState(memo?.suggested_size_pct ?? 0);
  const [price, setPrice] = useState(0);
  const [rationale, setRationale] = useState("");
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  async function submit(e) {
    e.preventDefault();
    setErr("");
    setOk("");
    if (!rationale.trim()) return setErr("Rationale is required.");
    if (!companyId) return setErr("No companyId available.");
    const payload = {
      company_id: companyId,
      memo_id: memoId,
      action,
      conviction: Number(conviction),
      rationale: rationale.trim(),
      size_pct: Number(sizePct),
      price_at_decision: Number(price),
    };
    if (!PIPELINE_ENDPOINT) {
      setOk("Demo mode — decision would be recorded: " + JSON.stringify(payload));
      if (onSubmitted) onSubmitted(payload);
      return;
    }
    const res = await fetch(`${PIPELINE_ENDPOINT}/api/decisions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      setErr(`Save failed: ${res.status}`);
      return;
    }
    const data = await res.json();
    setOk(`Decision recorded: ${data.id ?? ""}`);
    if (onSubmitted) onSubmitted(data);
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <label className="block">
        <span className="block text-sm">Action</span>
        <select
          value={action}
          onChange={(e) => setAction(e.target.value)}
          className="border rounded px-2 py-1"
        >
          {ACTIONS.map((a) => (
            <option key={a}>{a}</option>
          ))}
        </select>
      </label>
      <label className="block">
        <span className="block text-sm">Conviction ({conviction} / 10)</span>
        <input
          type="range"
          min={1}
          max={10}
          value={conviction}
          onChange={(e) => setConviction(e.target.value)}
          className="w-full"
        />
      </label>
      <div className="grid grid-cols-2 gap-3">
        <label className="block">
          <span className="block text-sm">Size %</span>
          <input
            type="number"
            step="0.1"
            value={sizePct}
            onChange={(e) => setSizePct(e.target.value)}
            className="border rounded px-2 py-1 w-full"
          />
        </label>
        <label className="block">
          <span className="block text-sm">Price at decision</span>
          <input
            type="number"
            step="0.01"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            className="border rounded px-2 py-1 w-full"
          />
        </label>
      </div>
      <label className="block">
        <span className="block text-sm">Rationale</span>
        <textarea
          value={rationale}
          onChange={(e) => setRationale(e.target.value)}
          rows={3}
          className="border rounded px-2 py-1 w-full"
          placeholder="Why this action, in your own words."
        />
      </label>
      {err && <div className="text-red-600 text-sm">{err}</div>}
      {ok && <div className="text-green-700 text-sm">{ok}</div>}
      <button
        type="submit"
        className="bg-indigo-600 text-white rounded px-4 py-2"
      >
        Record decision
      </button>
    </form>
  );
}

function ProgressBar({ steps, currentStep }) {
  return (
    <div className="flex flex-wrap gap-2">
      {steps.map((s, i) => {
        const done = i < currentStep;
        const active = i === currentStep;
        return (
          <div
            key={s}
            className={`text-xs px-2 py-1 rounded ${
              done
                ? "bg-green-100 text-green-800"
                : active
                ? "bg-indigo-100 text-indigo-800 animate-pulse"
                : "bg-gray-100 text-gray-500"
            }`}
          >
            {s}
          </div>
        );
      })}
    </div>
  );
}

export default function EarningsPodcastAgent() {
  const [mode, setMode] = useState("paste");
  const [ticker, setTicker] = useState("MSFT");
  const [quarter, setQuarter] = useState("Q1_2026");
  const [transcript, setTranscript] = useState("");
  const [running, setRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [tab, setTab] = useState("podcast");

  const steps = useMemo(
    () => [
      "1. Ingest",
      "2. Decode",
      "3. Critique",
      "4. Sector",
      "5. Script",
      "6. Audio",
      "7. Memo",
      "9. Tracker",
    ],
    []
  );

  async function runPipeline() {
    setError("");
    setResult(null);
    setRunning(true);
    setCurrentStep(0);
    try {
      if (!PIPELINE_ENDPOINT) {
        // Demo mode: fake a result so the UI can be eyeballed without a backend.
        for (let i = 0; i < steps.length; i++) {
          setCurrentStep(i);
          // eslint-disable-next-line no-await-in-loop
          await new Promise((r) => setTimeout(r, 200));
        }
        setResult({
          script_en: "HOST: Welcome to the show...",
          memo: {
            thesis_summary:
              "Demo thesis: the company compounds at ~15% for 3 years if Azure AI contribution holds.",
            bull_score: 7,
            bear_score: 5,
            suggested_size_pct: 3.0,
            time_horizon: "12_months",
            key_assumptions: [
              { text: "AI contribution holds above 6pp", confidence: 7 },
            ],
            kill_conditions: [
              {
                condition_text: "Azure YoY below 24% two quarters",
                metric_name: "azure_yoy_growth",
                threshold_value: 24,
                threshold_direction: "below",
              },
            ],
            memo_text: "Demo memo text.",
          },
        });
        setRunning(false);
        return;
      }
      const res = await fetch(`${PIPELINE_ENDPOINT}/api/pipeline/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker,
          quarter,
          source_type: mode === "paste" ? "text" : mode,
          source: transcript,
        }),
      });
      if (!res.ok) throw new Error(`Pipeline failed: ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Earnings Podcast Agent</h1>
        <p className="text-sm text-gray-500">
          Transcript → three-voice script → IC memo → decision log.
        </p>
      </header>

      <section className="border rounded p-4 space-y-3">
        <div className="flex gap-3">
          <label className="block">
            <span className="block text-sm">Ticker</span>
            <input
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              className="border rounded px-2 py-1"
            />
          </label>
          <label className="block">
            <span className="block text-sm">Quarter</span>
            <input
              value={quarter}
              onChange={(e) => setQuarter(e.target.value)}
              className="border rounded px-2 py-1"
            />
          </label>
          <label className="block">
            <span className="block text-sm">Input</span>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="border rounded px-2 py-1"
            >
              <option value="paste">Paste transcript</option>
              <option value="ticker">Ticker (web search)</option>
            </select>
          </label>
        </div>
        {mode === "paste" && (
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            rows={6}
            placeholder="Paste the full earnings transcript…"
            className="border rounded w-full px-2 py-1"
          />
        )}
        <button
          disabled={running || (mode === "paste" && !transcript.trim())}
          onClick={runPipeline}
          className="bg-indigo-600 disabled:bg-gray-300 text-white rounded px-4 py-2"
        >
          {running ? "Running…" : "Run pipeline"}
        </button>
        {running && (
          <ProgressBar steps={steps} currentStep={currentStep} />
        )}
        {error && <div className="text-red-600 text-sm">{error}</div>}
      </section>

      {result && (
        <section className="border rounded p-4">
          <Tabs
            active={tab}
            onChange={setTab}
            tabs={[
              { id: "podcast", label: "Podcast" },
              { id: "memo", label: "IC memo" },
              { id: "decision", label: "Decision" },
            ]}
          />
          {tab === "podcast" && (
            <div>
              {result.audio_en_url && (
                <audio controls src={result.audio_en_url} className="w-full mb-3" />
              )}
              <pre className="whitespace-pre-wrap text-sm">
                {result.script_en?.slice(0, 6000)}
              </pre>
            </div>
          )}
          {tab === "memo" && <MemoCard memo={result.memo} />}
          {tab === "decision" && (
            <DecisionForm
              memo={result.memo}
              companyId={result.company_id}
              memoId={result.memo_id}
            />
          )}
        </section>
      )}
    </div>
  );
}

import { useEffect, useEffectEvent, useState } from "react";
import "./Dashboard.css";

const API_URL = "http://127.0.0.1:8000";
const todayLabel = new Intl.DateTimeFormat("en-GB", {
  day: "2-digit",
  month: "short",
  year: "numeric",
}).format(new Date());
function RiskBadge({ level }) {
  return (
    <span className={`risk-badge risk-${level.toLowerCase()}`}>{level}</span>
  );
}

function Dashboard() {
  const [data, setData] = useState(null);
  const [riskEstimates, setRiskEstimates] = useState(null);
  const [backtest, setBacktest] = useState(null);
  const [outcomePerformance, setOutcomePerformance] = useState(null);
  const [hedgeCostRate, setHedgeCostRate] = useState("2");
  const [overhedgePenaltyRate, setOverhedgePenaltyRate] = useState("1");
  const [riskAppetite, setRiskAppetite] = useState("75");
  const [calibrating, setCalibrating] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importMessage, setImportMessage] = useState(null);
  const [refreshingHistory, setRefreshingHistory] = useState(false);
  const [historyMessage, setHistoryMessage] = useState(null);
  const [concentration, setConcentration] = useState(null);
  const [sensitivity, setSensitivity] = useState(null);
  const [loadingEstimates, setLoadingEstimates] = useState(false);
  const [companies, setCompanies] = useState([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState("1");
  const [showCompanyForm, setShowCompanyForm] = useState(false);
  const [companyName, setCompanyName] = useState("");
  const [companyCountry, setCompanyCountry] = useState("");
  const [companyCurrency, setCompanyCurrency] = useState("GBP");
  const [companySubmitting, setCompanySubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [currency, setCurrency] = useState("USD");
  const [foreignAmount, setForeignAmount] = useState("500000");
  const [fxRate, setFxRate] = useState(null);
  const [rateDate, setRateDate] = useState(null);
  const [loadingRate, setLoadingRate] = useState(false);
  const [paymentDate, setPaymentDate] = useState("2026-11-30");
  const [hedgePercentage, setHedgePercentage] = useState("75");

  async function loadDashboard(companyId = selectedCompanyId) {
    try {
      const response = await fetch(`${API_URL}/exposures/summary/${companyId}`);
      if (!response.ok) throw new Error("Failed to load TreasuryPilot data");
      setData(await response.json());
      setError(null);
    } catch (err) {
      console.error(err);
      setError(err.message);
    }
  }

  async function loadCompanies() {
    try {
      const response = await fetch(`${API_URL}/companies/`);
      if (!response.ok) throw new Error("Failed to load companies");
      const result = await response.json();
      setCompanies(result);
      if (result.length && !result.some((company) => String(company.id) === selectedCompanyId)) {
        setSelectedCompanyId(String(result[0].id));
      }
    } catch (err) {
      console.error(err);
      setError(err.message);
    }
  }

  async function loadRiskEstimates(exposureId) {
    setLoadingEstimates(true);
    try {
      const response = await fetch(`${API_URL}/exposures/${exposureId}/risk-estimates`);
      if (!response.ok) throw new Error("Failed to load parallel risk estimates");
      setRiskEstimates(await response.json());
    } catch (err) {
      console.error(err);
      setRiskEstimates(null);
    } finally {
      setLoadingEstimates(false);
    }
  }

  async function loadConcentration(companyId) {
    try {
      const response = await fetch(`${API_URL}/exposures/concentration/${companyId}`);
      if (!response.ok) throw new Error("Failed to load concentration risk");
      setConcentration(await response.json());
    } catch (err) {
      console.error(err);
      setConcentration(null);
    }
  }

  async function loadSensitivity(exposureId) {
    try {
      const response = await fetch(`${API_URL}/exposures/${exposureId}/sensitivity`);
      if (!response.ok) throw new Error("Failed to load sensitivity analysis");
      setSensitivity(await response.json());
    } catch (err) {
      console.error(err);
      setSensitivity(null);
    }
  }

  async function loadBacktest(exposureId, calibration = {}) {
    try {
      const params = new URLSearchParams({
        hedge_cost_annual_rate: String(calibration.hedgeCost ?? Number(hedgeCostRate) / 100),
        overhedge_penalty_annual_rate: String(calibration.overhedgePenalty ?? Number(overhedgePenaltyRate) / 100),
        risk_appetite_percentage: String(calibration.riskAppetite ?? riskAppetite),
      });
      const response = await fetch(`${API_URL}/exposures/${exposureId}/backtest?${params}`);
      if (!response.ok) throw new Error("Failed to load backtest");
      setBacktest(await response.json());
    } catch (err) {
      console.error(err);
      setBacktest(null);
    }
  }

  async function loadOutcomePerformance(companyId) {
    try {
      const response = await fetch(`${API_URL}/exposures/outcomes/company/${companyId}/performance`);
      if (!response.ok) throw new Error("Failed to load realized performance");
      setOutcomePerformance(await response.json());
    } catch (err) {
      console.error(err);
      setOutcomePerformance(null);
    }
  }

  async function runCalibration() {
    const exposureId = data?.portfolio_recommendation?.priority_exposure?.exposure_id;
    if (!exposureId) return;
    setCalibrating(true);
    await loadBacktest(exposureId);
    setCalibrating(false);
  }

  async function handleImport(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setImporting(true);
    setImportMessage(null);
    try {
      const text = await file.text();
      const [header, ...rows] = text.trim().split(/\r?\n/);
      const columns = header.split(",").map((column) => column.trim());
      const required = ["company_id", "currency", "foreign_amount", "current_fx_rate", "payment_date", "hedge_percentage"];
      if (!required.every((column) => columns.includes(column))) throw new Error(`CSV must contain: ${required.join(", ")}`);
      const records = rows.filter(Boolean).map((row) => {
        const values = row.split(",");
        return Object.fromEntries(columns.map((column, index) => [column, values[index]?.trim()]));
      }).map((record) => ({ ...record, company_id: Number(record.company_id), foreign_amount: Number(record.foreign_amount), current_fx_rate: Number(record.current_fx_rate), hedge_percentage: Number(record.hedge_percentage) }));
      const response = await fetch(`${API_URL}/exposures/import`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(records) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Import failed");
      setImportMessage(`Imported ${result.imported_count} exposure${result.imported_count === 1 ? "" : "s"}.`);
      await loadDashboard();
    } catch (err) {
      setImportMessage(err.message);
    } finally {
      setImporting(false);
      event.target.value = "";
    }
  }

  async function refreshHistory() {
    setRefreshingHistory(true);
    setHistoryMessage(null);
    try {
      const response = await fetch(`${API_URL}/rates/history/refresh/${selectedCompanyId}`, { method: "POST" });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Failed to refresh historical data");
      setHistoryMessage(`Refreshed ${result.observation_count} observations across ${result.currency_count} currencies.`);
      const exposureId = data?.portfolio_recommendation?.priority_exposure?.exposure_id;
      if (exposureId) {
        loadRiskEstimates(exposureId);
        loadBacktest(exposureId);
      }
    } catch (err) {
      console.error(err);
      setHistoryMessage(err.message);
    } finally {
      setRefreshingHistory(false);
    }
  }

  async function handleCreateCompany(event) {
    event.preventDefault();
    setCompanySubmitting(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/companies/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: companyName,
          country: companyCountry,
          base_currency: companyCurrency.toUpperCase(),
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Failed to create company");
      setCompanies((current) => [...current, result]);
      setSelectedCompanyId(String(result.id));
      setCompanyName("");
      setCompanyCountry("");
      setShowCompanyForm(false);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setCompanySubmitting(false);
    }
  }

  const loadDashboardEvent = useEffectEvent(loadDashboard);
  const loadCompaniesEvent = useEffectEvent(loadCompanies);
  const loadFxRateEvent = useEffectEvent(loadFxRate);
  const loadRiskEstimatesEvent = useEffectEvent(loadRiskEstimates);
  const loadConcentrationEvent = useEffectEvent(loadConcentration);
  const loadSensitivityEvent = useEffectEvent(loadSensitivity);
  const loadBacktestEvent = useEffectEvent(loadBacktest);
  const loadOutcomePerformanceEvent = useEffectEvent(loadOutcomePerformance);

  async function loadFxRate(value) {
    const code = value.trim().toUpperCase();
    if (code.length !== 3) {
      setFxRate(null);
      setRateDate(null);
      return;
    }
    setLoadingRate(true);
    setError(null);
    try {
      const baseCurrency = data?.base_currency || companies.find((company) => String(company.id) === selectedCompanyId)?.base_currency || "GBP";
      const response = await fetch(`${API_URL}/rates/${code}/${baseCurrency}`);
      const result = await response.json();
      if (!response.ok)
        throw new Error(result.detail || "Failed to retrieve FX rate");
      setFxRate(result.rate);
      setRateDate(result.date);
    } catch (err) {
      console.error(err);
      setFxRate(null);
      setRateDate(null);
      setError(err.message);
    } finally {
      setLoadingRate(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadCompaniesEvent();
      loadFxRateEvent("USD");
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadDashboardEvent();
      loadConcentrationEvent(selectedCompanyId);
      loadFxRateEvent(currency);
      loadOutcomePerformanceEvent(selectedCompanyId);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [selectedCompanyId, currency]);

  useEffect(() => {
    const exposureId = data?.portfolio_recommendation?.priority_exposure?.exposure_id;
    const timer = window.setTimeout(() => {
      if (exposureId) {
        loadRiskEstimatesEvent(exposureId);
        loadSensitivityEvent(exposureId);
        loadBacktestEvent(exposureId);
      } else {
        setRiskEstimates(null);
        setSensitivity(null);
        setBacktest(null);
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, [data]);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!fxRate) {
      setError("A valid FX rate is required before adding the exposure.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const url = editingId
        ? `${API_URL}/exposures/${editingId}`
        : `${API_URL}/exposures/`;
      const body = editingId
        ? {
            currency: currency.toUpperCase(),
            foreign_amount: Number(foreignAmount),
            payment_date: paymentDate,
            hedge_percentage: Number(hedgePercentage),
          }
        : {
            company_id: Number(selectedCompanyId),
            currency: currency.toUpperCase(),
            foreign_amount: Number(foreignAmount),
            current_fx_rate: Number(fxRate),
            payment_date: paymentDate,
            hedge_percentage: Number(hedgePercentage),
          };
      const response = await fetch(url, {
        method: editingId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const result = await response.json();
      if (!response.ok)
        throw new Error(result.detail || "Failed to create exposure");
      await loadDashboard();
      setForeignAmount("");
      setEditingId(null);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(exposureId) {
    if (!window.confirm("Remove this exposure from the portfolio?")) return;
    try {
      const response = await fetch(`${API_URL}/exposures/${exposureId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        const result = await response.json();
        throw new Error(result.detail || "Failed to remove exposure");
      }
      await loadDashboard();
    } catch (err) {
      console.error(err);
      setError(err.message);
    }
  }

  function beginEdit(exposure) {
    setEditingId(exposure.exposure_id);
    setCurrency(exposure.currency);
    setForeignAmount(String(exposure.foreign_amount));
    setPaymentDate(exposure.payment_date);
    setHedgePercentage(
      String(
        exposure.current_hedge_percentage ??
          exposure.recommended_hedge_percentage,
      ),
    );
    loadFxRate(exposure.currency);
    window.scrollTo({
      top: document.body.scrollHeight / 2,
      behavior: "smooth",
    });
  }

  function cancelEdit() {
    setEditingId(null);
    setForeignAmount("");
    setCurrency("USD");
    loadFxRate("USD");
  }

  if (error && !data)
    return (
      <main className="state-page">
        <p className="eyebrow">TreasuryPilot</p>
        <h1>Risk data unavailable</h1>
        <p>{error}</p>
      </main>
    );
  if (!data)
    return (
      <main className="state-page">
        <p className="eyebrow">TreasuryPilot</p>
        <h1>Loading risk data</h1>
        <div className="loader" />
      </main>
    );

  const portfolio = data.portfolio;
  const risk = data.risk;
  const recommendation = data.portfolio_recommendation;
  const baseCurrency = data.base_currency || companies.find((company) => String(company.id) === selectedCompanyId)?.base_currency || "GBP";
  const currencyMoney = (value, digits = 0) => `${baseCurrency} ${Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })}`;
  const gbpExposure =
    fxRate && foreignAmount ? Number(foreignAmount) * fxRate : null;

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">TP</span>
          <span>TreasuryPilot</span>
        </div>
        <div className="topbar-meta">
          <label className="company-picker">
            Company
            <select
              value={selectedCompanyId}
              onChange={(event) => {
                setSelectedCompanyId(event.target.value);
                setEditingId(null);
              }}
              disabled={!companies.length}
            >
              {companies.length ? (
                companies.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.name}
                  </option>
                ))
              ) : (
                <option value="1">Company 1</option>
              )}
            </select>
          </label>
          <button
            className="company-add-button"
            type="button"
            onClick={() => setShowCompanyForm((visible) => !visible)}
            title="Add company"
          >
            + Company
          </button>
          <span className="status-dot" /> Live portfolio view{" "}
          <span className="date-stamp">{todayLabel}</span>
        </div>
      </header>
      {showCompanyForm && (
        <form className="company-form" onSubmit={handleCreateCompany}>
          <div>
            <p className="eyebrow">Company setup</p>
            <h2>Add a company</h2>
          </div>
          <label>
            Company name
            <input value={companyName} onChange={(event) => setCompanyName(event.target.value)} required />
          </label>
          <label>
            Country
            <input value={companyCountry} onChange={(event) => setCompanyCountry(event.target.value)} required />
          </label>
          <label>
            Base currency
            <input value={companyCurrency} onChange={(event) => setCompanyCurrency(event.target.value.toUpperCase())} maxLength="3" required />
          </label>
          <button type="submit" disabled={companySubmitting}>
            {companySubmitting ? "Creating..." : "Create company"}
            <span>→</span>
          </button>
        </form>
      )}
      <section className="intro">
        <div>
          <p className="eyebrow">Treasury control room</p>
          <h1>Know what needs hedging next.</h1>
          <p className="intro-copy">
            A clear view of your currency exposure, stress loss, and the actions
            that matter today.
          </p>
        </div>
        <div className="intro-note">
          <span className="note-label">Priority currency</span>
          <strong>
            {recommendation.priority_exposure?.currency || "None"}
          </strong>
          <span>
            {recommendation.priority_exposure
              ? `${recommendation.priority_exposure.days_to_payment} days to payment`
              : "Portfolio is clear"}
          </span>
        </div>
      </section>
      <section className="metric-grid">
        <article className="metric-card metric-featured">
          <span className="metric-label">Total exposure</span>
          <strong>{currencyMoney(portfolio.total_base_currency_exposure)}</strong>
          <span className="metric-foot">
            Across {data.exposures.length} active exposure
            {data.exposures.length === 1 ? "" : "s"}
          </span>
        </article>
        <article className="metric-card">
          <span className="metric-label">Risk posture</span>
          <strong>{risk.overall_level}</strong>
          <RiskBadge level={risk.overall_level} />
          <span className="metric-foot">
            Portfolio score {risk.overall_score}/100
          </span>
        </article>
        <article className="metric-card">
          <span className="metric-label">Current hedge</span>
          <strong>{portfolio.hedge_coverage_percentage.toFixed(1)}%</strong>
          <div className="progress">
            <span
              style={{
                width: `${Math.min(portfolio.hedge_coverage_percentage, 100)}%`,
              }}
            />
          </div>
          <span className="metric-foot">
            Target {portfolio.recommended_hedge_coverage_percentage.toFixed(1)}%
          </span>
        </article>
        <article className="metric-card metric-warning">
          <span className="metric-label">10% stress loss</span>
          <strong>{currencyMoney(risk["10_percent_adverse_move"])}</strong>
          <span className="metric-foot">Unhedged adverse movement</span>
        </article>
      </section>
      {concentration && (
        <section className="panel concentration-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Portfolio structure</p>
              <h2>Currency concentration</h2>
            </div>
            <RiskBadge level={concentration.level} />
          </div>
          <div className="concentration-summary">
            <div><span>Largest currency</span><strong>{concentration.top_currency || "None"}</strong></div>
            <div><span>Portfolio share</span><strong>{concentration.top_currency_share.toFixed(1)}%</strong></div>
            <div><span>Currency count</span><strong>{concentration.currency_count}</strong></div>
            <div><span>HHI index</span><strong>{concentration.hhi.toFixed(2)}</strong></div>
          </div>
          <div className="concentration-list">
            {concentration.currencies.map((item) => (
              <div className="concentration-row" key={item.currency}>
                <span>{item.currency}</span>
                <div className="currency-bar"><span style={{ width: `${item.share_percentage}%` }} /></div>
                <strong>{item.share_percentage.toFixed(1)}%</strong>
              </div>
            ))}
          </div>
        </section>
      )}
      <section className="dashboard-grid">
        <article className="panel recommendation-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Decision brief</p>
              <h2>Portfolio recommendation</h2>
            </div>
            <RiskBadge level={risk.overall_level} />
          </div>
          <p className="recommendation-action">{recommendation.action}</p>
          <p className="muted">{recommendation.summary}</p>
          <div className="recommendation-stats">
            <div>
              <span>Additional hedge</span>
              <strong>{currencyMoney(portfolio.additional_hedge_required)}</strong>
            </div>
            <div>
              <span>Recommended coverage</span>
              <strong>
                {portfolio.recommended_hedge_coverage_percentage.toFixed(1)}%
              </strong>
            </div>
          </div>
        </article>
        <article className="panel stress-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Scenario analysis</p>
              <h2>Adverse FX movement</h2>
            </div>
            <span className="scenario-icon">%</span>
          </div>
          <div className="stress-row">
            <span>5% movement</span>
            <strong>{currencyMoney(risk["5_percent_adverse_move"])}</strong>
          </div>
          <div className="stress-row stress-row-critical">
            <span>10% movement</span>
            <strong>{currencyMoney(risk["10_percent_adverse_move"])}</strong>
          </div>
          <p className="muted">
            Potential impact translated into GBP across the portfolio.
          </p>
        </article>
      </section>
      <section className="panel model-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Parallel risk view</p>
            <h2>How the estimates compare</h2>
          </div>
          <span className="scenario-icon">2x</span>
        </div>
          <button className="refresh-button" type="button" onClick={refreshHistory} disabled={refreshingHistory}>
            {refreshingHistory ? "Refreshing historical data..." : "Refresh historical data"}
          </button>
        {loadingEstimates ? (
          <p className="muted">Loading historical observations...</p>
        ) : riskEstimates ? (
          <div className="estimate-grid">
            <div className="estimate-card">
              <span>Deterministic · 5%</span>
              <strong>{currencyMoney(riskEstimates.deterministic_stress["5_percent_loss"])}</strong>
            </div>
            <div className="estimate-card">
              <span>Deterministic · 10%</span>
              <strong>{currencyMoney(riskEstimates.deterministic_stress["10_percent_loss"])}</strong>
            </div>
            {riskEstimates.monte_carlo?.available && (
              <>
                <div className="estimate-card estimate-card-model">
                  <span>Monte Carlo median</span>
                  <strong>{currencyMoney(riskEstimates.monte_carlo.median_loss)}</strong>
                </div>
                <div className="estimate-card estimate-card-model">
                  <span>Monte Carlo P95</span>
                  <strong>{currencyMoney(riskEstimates.monte_carlo.p95_loss)}</strong>
                </div>
                <div className="estimate-card estimate-card-model">
                  <span>Monte Carlo P99</span>
                  <strong>{currencyMoney(riskEstimates.monte_carlo.p99_loss)}</strong>
                </div>
              </>
            )}
            {riskEstimates.historical_simulation.available ? (
              <>
                <div className="estimate-card">
                  <span>Historical median</span>
                  <strong>{currencyMoney(riskEstimates.historical_simulation.median_loss)}</strong>
                </div>
                <div className="estimate-card">
                  <span>Historical P95</span>
                  <strong>{currencyMoney(riskEstimates.historical_simulation.p95_loss)}</strong>
                </div>
                <div className="estimate-card">
                  <span>Historical P99</span>
                  <strong>{currencyMoney(riskEstimates.historical_simulation.p99_loss)}</strong>
                </div>
                <div className="estimate-card">
                  <span>Historical maximum</span>
                  <strong>{currencyMoney(riskEstimates.historical_simulation.maximum_loss)}</strong>
                </div>
              </>
            ) : (
              <p className="muted estimate-empty">Historical simulation needs more stored observations.</p>
            )}
          </div>
        ) : (
          <p className="muted">Parallel estimates are unavailable for this exposure.</p>
        )}
        {riskEstimates && (
          <p className="model-meta">
            Generated {new Date(riskEstimates.generated_at).toLocaleString()} · {riskEstimates.monte_carlo?.simulation_count || 0} Monte Carlo paths
          </p>
        )}
        {historyMessage && <p className="model-meta">{historyMessage}</p>}
      </section>
      {sensitivity && (
        <section className="panel sensitivity-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Sensitivity analysis</p>
              <h2>What changes the downside?</h2>
            </div>
            <span className="scenario-icon">↗</span>
          </div>
          <div className="sensitivity-grid">
            {sensitivity.hedge_scenarios.map((scenario) => (
              <div className="sensitivity-row" key={scenario.hedge_percentage}>
                <span>{scenario.hedge_percentage}% hedge</span>
                <strong>{currencyMoney(scenario.net_loss_at_10_percent_shock)}</strong>
              </div>
            ))}
          </div>
          <p className="muted">Net loss under a 10% adverse move at different hedge levels.</p>
        </section>
      )}
      {backtest && (
        <section className="panel backtest-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Reality check</p>
              <h2>Historical hedge-policy backtest</h2>
            </div>
            <span className="scenario-icon">↺</span>
          </div>
          <div className="calibration-controls">
            <label>
              Hedge cost (% p.a.)
              <input type="number" min="0" step="0.1" value={hedgeCostRate} onChange={(event) => setHedgeCostRate(event.target.value)} />
            </label>
            <label>
              Over-hedge penalty (% p.a.)
              <input type="number" min="0" step="0.1" value={overhedgePenaltyRate} onChange={(event) => setOverhedgePenaltyRate(event.target.value)} />
            </label>
            <label>
              Risk appetite (% hedge)
              <input type="number" min="0" max="100" step="1" value={riskAppetite} onChange={(event) => setRiskAppetite(event.target.value)} />
            </label>
            <button className="refresh-button" type="button" onClick={runCalibration} disabled={calibrating}>
              {calibrating ? "Running benchmark..." : "Run calibrated benchmark"}
            </button>
          </div>
          {backtest.available ? (
            <>
              <div className="backtest-decision"><span>Decision under current assumptions</span><strong>{backtest.policies.reduce((best, policy) => policy.average_total_cost < best.average_total_cost ? policy : best).strategy}</strong></div>
              <p className="muted">{backtest.scenario_count} decision-to-settlement scenarios from {backtest.observation_count} stored observations.</p>
              <div className="backtest-table-wrap">
                <table className="backtest-table">
                  <thead><tr><th>Policy</th><th>Average loss</th><th>Average total cost</th><th>P95 total cost</th><th>Reduction</th></tr></thead>
                  <tbody>{backtest.policies.map((policy) => <tr key={policy.strategy}><td><strong>{policy.strategy}</strong></td><td>{currencyMoney(policy.average_loss)}</td><td>{currencyMoney(policy.average_total_cost)}</td><td>{currencyMoney(policy.p95_total_cost)}</td><td className="reduction">{(policy.loss_reduction_vs_no_hedge * 100).toFixed(0)}%</td></tr>)}</tbody>
                </table>
              </div>
            </>
          ) : (
            <p className="muted">{backtest.reason}</p>
          )}
          {backtest.summary && <p className="model-meta">Best strategy by average total cost: {backtest.summary.best_strategy}</p>}
          {backtest.available && <p className="model-meta">Assumptions: {(Number(hedgeCostRate) * 100).toFixed(1)}% annual hedge cost · {(Number(overhedgePenaltyRate) * 100).toFixed(1)}% over-hedge penalty · {riskAppetite}% risk appetite.</p>}
        </section>
      )}
      {outcomePerformance && (
        <section className="panel outcome-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Observed outcomes</p>
              <h2>Realized performance</h2>
            </div>
            <span className="scenario-icon">✓</span>
          </div>
          {outcomePerformance.performance.available ? (
            <>
              <p className="muted">Based on {outcomePerformance.performance.outcome_count} imported or generated settlement outcomes.</p>
              <div className="outcome-highlight"><span>Lowest observed total cost</span><strong>{outcomePerformance.performance.best_strategy}</strong></div>
              <div className="backtest-table-wrap">
                <table className="backtest-table">
                  <thead><tr><th>Strategy</th><th>Average total cost</th><th>Maximum cost</th><th>Reduction</th></tr></thead>
                  <tbody>{outcomePerformance.performance.strategies.map((strategy) => <tr key={strategy.strategy}><td><strong>{strategy.strategy}</strong></td><td>{currencyMoney(strategy.average_total_cost)}</td><td>{currencyMoney(strategy.maximum_total_cost)}</td><td className="reduction">{(strategy.cost_reduction_vs_no_hedge * 100).toFixed(0)}%</td></tr>)}</tbody>
                </table>
              </div>
            </>
          ) : <p className="muted">{outcomePerformance.performance.reason}</p>}
        </section>
      )}
      <section className="workspace-grid">
        <article className="panel add-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">
                {editingId ? "Update exposure" : "Capture exposure"}
              </p>
              <h2>{editingId ? "Edit FX exposure" : "Add FX exposure"}</h2>
            </div>
            <span className="plus-icon">+</span>
          </div>
          <form onSubmit={handleSubmit} className="exposure-form">
            <label>
              Currency
              <input
                type="text"
                value={currency}
                onChange={(event) => {
                  const value = event.target.value.toUpperCase();
                  setCurrency(value);
                  if (value.length === 3) loadFxRate(value);
                }}
                maxLength="3"
                required
              />
            </label>
            <label>
              Foreign amount
              <input
                type="number"
                value={foreignAmount}
                onChange={(event) => setForeignAmount(event.target.value)}
                min="0"
                step="0.01"
                required
              />
            </label>
            <label>
              Payment date
              <input
                type="date"
                value={paymentDate}
                onChange={(event) => setPaymentDate(event.target.value)}
                required
              />
            </label>
            <label>
              Current hedge
              <input
                type="number"
                value={hedgePercentage}
                onChange={(event) => setHedgePercentage(event.target.value)}
                min="0"
                max="100"
                required
              />
            </label>
            <div className="rate-readout">
              <span>Live rate</span>
              <strong>
                {loadingRate
                  ? "Loading..."
                  : fxRate
                    ? `${fxRate} GBP / ${currency}`
                    : "Unavailable"}
              </strong>
              {rateDate && <small>As of {rateDate}</small>}
            </div>
            <div className="rate-readout">
              <span>GBP exposure</span>
              <strong>
                {gbpExposure !== null
                  ? currencyMoney(gbpExposure, 2)
                  : "Enter an amount"}
              </strong>
            </div>
            <button type="submit" disabled={submitting || !fxRate || loadingRate}>
              {submitting
                ? editingId
                  ? "Updating exposure..."
                  : "Adding exposure..."
                : editingId
                  ? "Save changes"
                  : "Add exposure"}
              <span>→</span>
            </button>
            {editingId && (
              <button className="cancel-button" type="button" onClick={cancelEdit}>
                Cancel edit
              </button>
            )}
          </form>
          {error && <p className="form-error">{error}</p>}
        </article>
        <article className="panel currency-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Book composition</p>
              <h2>By currency</h2>
            </div>
            <span className="panel-count">
              {Object.keys(data.currencies).length}
            </span>
          </div>
          {Object.entries(data.currencies).map(([code, exposure]) => (
            <div className="currency-row" key={code}>
              <div className="currency-code">{code}</div>
              <div className="currency-bar">
                <span
                  style={{
                    width: `${Math.min((exposure.base_currency_value / portfolio.total_base_currency_exposure) * 100, 100)}%`,
                  }}
                />
              </div>
                <strong>{currencyMoney(exposure.base_currency_value)}</strong>
              <small>
                {exposure.foreign_amount.toLocaleString()} {code}
              </small>
            </div>
          ))}
        </article>
      </section>
      <section className="panel import-panel">
        <div className="panel-heading">
          <div><p className="eyebrow">Bring your data</p><h2>Import exposure records</h2></div>
          <span className="scenario-icon">↓</span>
        </div>
        <p className="muted">Add validated CSV records without changing existing exposures. Rates must be quoted in the company base currency.</p>
        <label className="file-picker">
          Choose CSV file
          <input type="file" accept=".csv,text/csv" onChange={handleImport} disabled={importing} />
        </label>
        <p className="model-meta">Columns: company_id, currency, foreign_amount, current_fx_rate, payment_date, hedge_percentage</p>
        {importMessage && <p className="model-meta">{importMessage}</p>}
      </section>
      <section className="recommendations">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Action queue</p>
            <h2>Treasury recommendations</h2>
          </div>
          <span className="muted">Sorted by risk priority</span>
        </div>
        <div className="recommendation-list">
          {data.exposures.length === 0 ? (
            <div className="empty-queue">
              <strong>Your action queue is clear.</strong>
              <span>Add your first foreign-currency exposure above to begin tracking risk.</span>
            </div>
          ) : (
            data.exposures.map((exposure) => (
            <article className="exposure-row" key={exposure.exposure_id}>
              <div className="exposure-main">
                <div className="currency-code">{exposure.currency}</div>
                <div>
                  <h3>{currencyMoney(exposure.base_currency_value)} exposure</h3>
                  <p className="muted">
                    Due {exposure.payment_date} · {exposure.days_to_payment}{" "}
                    days remaining
                  </p>
                </div>
              </div>
              <div className="exposure-risk">
                <RiskBadge level={exposure.risk_level} />
                <span>Score {exposure.risk_score}/100</span>
              </div>
              <div className="exposure-action">
                <strong>{exposure.recommended_action}</strong>
                <span>
                  {exposure.instrument} · target{" "}
                  {exposure.recommended_hedge_percentage}%
                </span>
              </div>
              <button
                className="edit-button"
                type="button"
                onClick={() => beginEdit(exposure)}
                title="Edit exposure"
                aria-label={`Edit ${exposure.currency} exposure`}
              >
                Edit
              </button>
              <button
                className="delete-button"
                type="button"
                onClick={() => handleDelete(exposure.exposure_id)}
                title="Remove exposure"
                aria-label={`Remove ${exposure.currency} exposure`}
              >
                Remove
              </button>
            </article>
            ))
          )}
        </div>
      </section>
    </main>
  );
}

export default Dashboard;

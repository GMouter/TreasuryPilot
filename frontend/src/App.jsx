import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000";
const COMPANY_ID = 1;

function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [currency, setCurrency] = useState("USD");
  const [foreignAmount, setForeignAmount] = useState("500000");
  const [fxRate, setFxRate] = useState(null);
  const [rateDate, setRateDate] = useState(null);
  const [loadingRate, setLoadingRate] = useState(false);
  const [paymentDate, setPaymentDate] = useState("2026-11-30");
  const [hedgePercentage, setHedgePercentage] = useState("75");

  async function loadDashboard() {
    try {
      const response = await fetch(
        `${API_URL}/exposures/summary/${COMPANY_ID}`
      );

      if (!response.ok) {
        throw new Error("Failed to load TreasuryPilot data");
      }

      const result = await response.json();

      setData(result);
      setError(null);
    } catch (err) {
      console.error(err);
      setError(err.message);
    }
  }

  async function loadFxRate(selectedCurrency) {
    const cleanCurrency = selectedCurrency.trim().toUpperCase();

    if (cleanCurrency.length !== 3) {
      setFxRate(null);
      setRateDate(null);
      return;
    }

    setLoadingRate(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/rates/${cleanCurrency}/GBP`
      );

      if (!response.ok) {
        const result = await response.json();

        throw new Error(
          result.detail || "Failed to retrieve FX rate"
        );
      }

      const result = await response.json();

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
    loadDashboard();
    loadFxRate("USD");
  }, []);

  function handleCurrencyChange(event) {
    const value = event.target.value.toUpperCase();

    setCurrency(value);

    if (value.length === 3) {
      loadFxRate(value);
    } else {
      setFxRate(null);
      setRateDate(null);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!fxRate) {
      setError("A valid FX rate is required before adding the exposure.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/exposures/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          company_id: COMPANY_ID,
          currency: currency.toUpperCase(),
          foreign_amount: Number(foreignAmount),
          current_fx_rate: Number(fxRate),
          payment_date: paymentDate,
          hedge_percentage: Number(hedgePercentage),
        }),
      });

      if (!response.ok) {
        const result = await response.json();

        throw new Error(
          result.detail || "Failed to create exposure"
        );
      }

      await response.json();

      await loadDashboard();

      alert("Exposure added successfully.");
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  const gbpExposure =
    fxRate && foreignAmount
      ? Number(foreignAmount) * fxRate
      : null;

  if (error && !data) {
    return (
      <div>
        <h1>TreasuryPilot</h1>
        <p>Error: {error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div>
        <h1>TreasuryPilot</h1>
        <p>Loading risk data...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: "30px", fontFamily: "Arial" }}>
      <h1>TreasuryPilot</h1>

      <h2>FX Risk Dashboard</h2>

      <hr />

      <h2>Add FX Exposure</h2>

      <form onSubmit={handleSubmit}>
        <div>
          <label>Currency: </label>

          <input
            type="text"
            value={currency}
            onChange={handleCurrencyChange}
            maxLength="3"
            required
          />
        </div>

        <br />

        <div>
          <label>Foreign Amount: </label>

          <input
            type="number"
            value={foreignAmount}
            onChange={(e) =>
              setForeignAmount(e.target.value)
            }
            min="0"
            step="0.01"
            required
          />
        </div>

        <br />

        <div>
          <strong>Current FX Rate: </strong>

          {loadingRate ? (
            <span> Loading...</span>
          ) : fxRate ? (
            <span>
              {" "}
              {fxRate} GBP per {currency}
            </span>
          ) : (
            <span> Not available</span>
          )}

          {rateDate && (
            <span>
              {" "}
              (Rate date: {rateDate})
            </span>
          )}
        </div>

        <br />

        <div>
          <strong>GBP Exposure: </strong>

          {gbpExposure !== null
            ? `£${gbpExposure.toLocaleString(undefined, {
                maximumFractionDigits: 2,
              })}`
            : "Unable to calculate"}
        </div>

        <br />

        <div>
          <label>Payment Date: </label>

          <input
            type="date"
            value={paymentDate}
            onChange={(e) =>
              setPaymentDate(e.target.value)
            }
            required
          />
        </div>

        <br />

        <div>
          <label>Hedge Percentage: </label>

          <input
            type="number"
            value={hedgePercentage}
            onChange={(e) =>
              setHedgePercentage(e.target.value)
            }
            min="0"
            max="100"
            required
          />
        </div>

        <br />

        <button
          type="submit"
          disabled={submitting || !fxRate || loadingRate}
        >
          {submitting ? "Adding..." : "Add Exposure"}
        </button>
      </form>

      {error && (
        <p>
          <strong>Error:</strong> {error}
        </p>
      )}

      <hr />

        <hr />

<h2>Portfolio Recommendation</h2>

<div
  style={{
    border: "2px solid #333",
    padding: "20px",
    marginBottom: "20px",
    borderRadius: "8px",
  }}
>
  <h3>Recommended Action</h3>

  <p>
    <strong>
      {data.portfolio_recommendation.action}
    </strong>
  </p>

  <p>
    {data.portfolio_recommendation.summary}
  </p>

  <hr />

  <h3>Portfolio Position</h3>

  <p>
    <strong>Total FX Exposure:</strong>{" "}
    £
    {data.portfolio.total_base_currency_exposure.toLocaleString(
      undefined,
      {
        maximumFractionDigits: 0,
      }
    )}
  </p>

  <p>
    <strong>Current Hedge Coverage:</strong>{" "}
    {data.portfolio.hedge_coverage_percentage.toFixed(1)}%
  </p>

  <p>
    <strong>Recommended Coverage:</strong>{" "}
    {data.portfolio.recommended_hedge_coverage_percentage.toFixed(
      1
    )}
    %
  </p>

  <p>
    <strong>Additional Hedge Required:</strong>{" "}
    £
    {data.portfolio.additional_hedge_required.toLocaleString(
      undefined,
      {
        maximumFractionDigits: 0,
      }
    )}
  </p>

  <hr />

  <h3>Priority Exposure</h3>

  {data.portfolio_recommendation.priority_exposure && (
    <>
      <p>
        <strong>Currency:</strong>{" "}
        {data.portfolio_recommendation.priority_exposure.currency}
      </p>

      <p>
        <strong>Exposure:</strong>{" "}
        £
        {data.portfolio_recommendation.priority_exposure.base_currency_value.toLocaleString(
          undefined,
          {
            maximumFractionDigits: 0,
          }
        )}
      </p>

      <p>
        <strong>Risk:</strong>{" "}
        {data.portfolio_recommendation.priority_exposure.risk_level}
      </p>

      <p>
        <strong>Risk Score:</strong>{" "}
        {data.portfolio_recommendation.priority_exposure.risk_score}
        /100
      </p>

      <p>
        <strong>Payment Date:</strong>{" "}
        {data.portfolio_recommendation.priority_exposure.payment_date}
      </p>

      <p>
        <strong>Days to Payment:</strong>{" "}
        {data.portfolio_recommendation.priority_exposure.days_to_payment}
      </p>
    </>
  )}
</div>

      <h2>Portfolio Overview</h2>

      <h3>Total Exposure</h3>

      <p>
        £
        {data.portfolio.total_base_currency_exposure.toLocaleString(
          undefined,
          {
            maximumFractionDigits: 0,
          }
        )}
      </p>

      <h3>Hedge Coverage</h3>

      <p>
        {data.portfolio.hedge_coverage_percentage.toFixed(1)}%
      </p>

      <h3>Risk Level</h3>

      <p>{data.risk.overall_level}</p>

      <h3>Risk Score</h3>

      <p>{data.risk.overall_score}/100</p>

      <hr />

      <h2>Stress Testing</h2>

      <p>
        5% adverse FX move: £
        {data.risk["5_percent_adverse_move"].toLocaleString(
          undefined,
          {
            maximumFractionDigits: 0,
          }
        )}
      </p>

      <p>
        10% adverse FX move: £
        {data.risk["10_percent_adverse_move"].toLocaleString(
          undefined,
          {
            maximumFractionDigits: 0,
          }
        )}
      </p>

      <hr />

      <h2>Currency Exposure</h2>

      {Object.entries(data.currencies).map(
        ([currency, exposure]) => (
          <div key={currency}>
            <h3>{currency}</h3>

            <p>
              Foreign exposure:{" "}
              {exposure.foreign_amount.toLocaleString()}
            </p>

            <p>
              GBP exposure: £
              {exposure.base_currency_value.toLocaleString(
                undefined,
                {
                  maximumFractionDigits: 0,
                }
              )}
            </p>
          </div>
        )
      )}

    <hr />

    <h2>Treasury Recommendations</h2>

    {data.exposures.map((exposure) => (
      <div
        key={exposure.exposure_id}
        style={{

          border: "1px solid #ccc",
          padding: "20px",
          marginBottom: "20px",
          borderRadius: "8px",
        }}
      >
        <h3>
          {exposure.currency} Exposure
        </h3>

        <p>
          <strong>Risk Level:</strong>{" "}
          {exposure.risk_level}
        </p>

        <p>
          <strong>Risk Score:</strong>{" "}
          {exposure.risk_score}/100
        </p>

        <hr />

        <h3>Recommended Action</h3>

        <p>
          <strong>
            {exposure.recommended_action}
          </strong>
        </p>

        <p>
          {exposure.recommendation_summary}
        </p>

        <hr />

        <h3>Hedge Recommendation</h3>

        <p>
          <strong>Recommended hedge:</strong>{" "}
          {exposure.recommended_hedge_percentage}%
        </p>

        <p>
          <strong>Recommended hedge amount:</strong>{" "}
          £
          {exposure.recommended_hedge_amount.toLocaleString(
            undefined,
            {
              maximumFractionDigits: 0,
            }
          )}
        </p>

        <p>
          <strong>Remaining unhedged:</strong>{" "}
          £
          {exposure.unhedged_amount.toLocaleString(
            undefined,
            {
              maximumFractionDigits: 0,
            }
          )}
        </p>

        <p>
          <strong>Suggested instrument:</strong>{" "}
          {exposure.instrument}
        </p>

        <hr />

        <h3>Stress Scenario</h3>

        <p>
          Potential impact of a 10% adverse FX movement:
          {" "}
          <strong>
            £
            {exposure.potential_10_percent_loss.toLocaleString(
              undefined,
              {
                maximumFractionDigits: 0,
              }
            )}
          </strong>
        </p>

        <p>
          <strong>Payment date:</strong>{" "}
          {exposure.payment_date}
        </p>

        <p>
          <strong>Days to payment:</strong>{" "}
          {exposure.days_to_payment}
        </p>

        <h3>Why?</h3>

        <ul>
          {exposure.reasons.map(
            (reason, index) => (
              <li key={index}>
                {reason}
              </li>
            )
          )}
        </ul>
      </div>
    ))}
</div>
  );
}

export default App;
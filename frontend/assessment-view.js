(function exposeAssessmentView(globalObject) {
  "use strict";

  const assessmentResults = document.querySelector("#assessment-results");
  const previewPanel = document.querySelector("#preview-panel");
  const previewIdentifier = document.querySelector("#preview-identifier");
  const previewGroups = document.querySelector("#preview-groups");
  const missingData = document.querySelector("#missing-data");
  const missingList = document.querySelector("#missing-list");
  const completenessPanel = document.querySelector("#completeness-panel");
  const completenessStatus = document.querySelector("#completeness-status");
  const completenessMeter = document.querySelector("#completeness-meter");
  const completenessBar = document.querySelector("#completeness-bar");
  const completenessValue = document.querySelector("#completeness-value");
  const featureCaveat = document.querySelector("#feature-caveat");
  const featureCaveatText = document.querySelector("#feature-caveat-text");
  const missingFeatureList = document.querySelector("#missing-feature-list");
  const riskPanel = document.querySelector("#risk-panel");
  const riskBand = document.querySelector("#risk-band");
  const riskScore = document.querySelector("#risk-score");
  const modelVersion = document.querySelector("#model-version");
  const thresholdVersion = document.querySelector("#threshold-version");
  const assessmentTime = document.querySelector("#assessment-time");
  const reviewRecommendation = document.querySelector("#review-recommendation");
  const riskWarning = document.querySelector("#risk-warning");
  const factorList = document.querySelector("#factor-list");
  const uncertaintyText = document.querySelector("#uncertainty-text");
  const decisionPanel = document.querySelector("#decision-panel");
  const followUpPanel = document.querySelector("#follow-up-panel");

  const previewDefinitions = [
    ["Profile", [["Username", "username"], ["Description", "description"], ["Location", "location"]]],
    ["Activity", [["Account age", "account_age_days"], ["Post count", "post_count"], ["Posts per day", "posts_per_day"]]],
    ["Network", [["Followers", "followers_count"], ["Following", "following_count"]]],
  ];

  const recommendationLabels = Object.freeze({
    no_concern: "No immediate concern — retain normal human review.",
    monitor: "Continue monitoring — review again if evidence changes.",
    prioritise: "Prioritise this account for human review.",
  });
  const booleanFactorFeatures = new Set([
    "verified",
    "uses_default_profile_image",
    "has_description",
  ]);

  /** Convert missing source values to the visible, non-imputed placeholder. */
  function displayValue(value) {
    return value === null || value === undefined || value === ""
      ? "Not available"
      : String(value);
  }

  /** Translate encoded binary model inputs into values a reviewer can read. */
  function displayFactorValue(factor) {
    const value = factor.observed_value;
    if (value === null || value === undefined || value === "") {
      return "Not available";
    }
    if (booleanFactorFeatures.has(factor.feature)) {
      if (["1", "1.0", "true"].includes(String(value).toLowerCase())) return "Yes";
      if (["0", "0.0", "false"].includes(String(value).toLowerCase())) return "No";
    }
    return String(value);
  }

  /** Hide all single-assessment result panels before a new request. */
  function clear() {
    previewPanel.hidden = true;
    completenessPanel.hidden = true;
    riskPanel.hidden = true;
    decisionPanel.hidden = true;
    followUpPanel.hidden = true;
  }

  /** Render approved public fields while preserving explicit missing values. */
  function renderPreview(preview) {
    previewIdentifier.textContent = preview.display_identifier;
    previewGroups.replaceChildren();
    const sections = {
      Profile: preview.profile,
      Activity: preview.activity,
      Network: preview.network,
    };
    for (const [title, fields] of previewDefinitions) {
      const group = document.createElement("section");
      group.className = "preview-group";
      const heading = document.createElement("h3");
      heading.textContent = title;
      const list = document.createElement("dl");
      for (const [label, key] of fields) {
        const term = document.createElement("dt");
        term.textContent = label;
        const detail = document.createElement("dd");
        const value = sections[title][key];
        detail.textContent = displayValue(value);
        if (value === null || value === undefined || value === "") {
          detail.className = "missing-value";
        }
        list.append(term, detail);
      }
      group.append(heading, list);
      previewGroups.append(group);
    }
    missingList.replaceChildren();
    for (const label of preview.missing_fields) {
      const item = document.createElement("li");
      item.textContent = label;
      missingList.append(item);
    }
    missingData.hidden = preview.missing_fields.length === 0;
    previewPanel.hidden = false;
  }

  /** Present evidence completeness before any risk output is shown. */
  function renderCompleteness(result) {
    const percentage = result.completeness_percentage;
    completenessStatus.textContent = result.status;
    completenessStatus.classList.toggle("insufficient", !result.eligible_for_scoring);
    completenessMeter.setAttribute("aria-valuenow", String(percentage));
    completenessBar.style.width = `${percentage}%`;
    completenessValue.textContent = `${percentage}% of required features are available.`;
    missingFeatureList.replaceChildren();
    for (const label of result.missing_features) {
      const item = document.createElement("li");
      item.textContent = label;
      missingFeatureList.append(item);
    }
    featureCaveatText.textContent = result.missing_data_caveat || "";
    featureCaveat.hidden = result.missing_features.length === 0;
    completenessPanel.hidden = false;
  }

  /** Render a scored result, its factors, and available human-review panels. */
  function renderRiskResult(result) {
    riskBand.textContent = `${result.risk_band_label} risk`;
    riskBand.className = `risk-band ${result.risk_band}`;
    riskScore.textContent = `${result.risk_score} / 100`;
    modelVersion.textContent = result.model_version;
    thresholdVersion.textContent = result.threshold_version;
    assessmentTime.textContent = new Date(result.assessment_time).toLocaleString();
    reviewRecommendation.textContent =
      recommendationLabels[result.recommendation] || "Human review is required.";
    riskWarning.textContent = result.warning;
    factorList.replaceChildren();
    for (const factor of result.top_factors) {
      const item = document.createElement("li");
      const label = document.createElement("strong");
      label.textContent = factor.label || factor.feature || "Contributing factor";
      const detail = document.createElement("span");
      detail.className = "factor-direction";
      const direction =
        factor.direction === "increases_risk" ? "Increases risk" : "Decreases risk";
      detail.textContent =
        `${direction} · Observed value: ${displayFactorValue(factor)}`;
      item.append(label, detail);
      factorList.append(item);
    }
    uncertaintyText.textContent = result.uncertainty;
    riskPanel.hidden = false;
    decisionPanel.hidden = false;
    followUpPanel.hidden = false;
  }

  /** Render the valid no-score path while keeping human follow-up available. */
  function renderInsufficientResult() {
    riskPanel.hidden = true;
    decisionPanel.hidden = true;
    followUpPanel.hidden = false;
  }

  const view = Object.freeze({
    assessmentResults,
    clear,
    renderCompleteness,
    renderInsufficientResult,
    renderPreview,
    renderRiskResult,
  });
  globalObject.SignalReviewAssessmentView = view;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = view;
  }
})(typeof window === "undefined" ? globalThis : window);

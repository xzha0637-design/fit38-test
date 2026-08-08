/** Browser controller for the single-account and CSV assessment workflows. */

const form = document.querySelector("#intake-form");
const identifierInput = document.querySelector("#account-identifier");
const demoSelect = document.querySelector("#demo-account");
const errorMessage = document.querySelector("#identifier-error");
const statusPanel = document.querySelector("#intake-status");
const submitButton = document.querySelector("#assess-button");
const buttonLabel = submitButton.querySelector(".button-label");
const buttonLoading = submitButton.querySelector(".button-loading");
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
const riskWarning = document.querySelector("#risk-warning");
const factorList = document.querySelector("#factor-list");
const uncertaintyText = document.querySelector("#uncertainty-text");
const decisionPanel = document.querySelector("#decision-panel");
const decisionForm = document.querySelector("#decision-form");
const decisionReason = document.querySelector("#decision-reason");
const decisionSubmit = document.querySelector("#decision-submit");
const decisionAcknowledgement = document.querySelector("#decision-acknowledgement");
let currentAssessmentId = null;
const recoveryActions = document.querySelector("#recovery-actions");
const retryButton = document.querySelector("#retry-button");
const newAssessmentButton = document.querySelector("#new-assessment-button");
const followUpPanel = document.querySelector("#follow-up-panel");
const followUpForm = document.querySelector("#follow-up-form");
const followUpReason = document.querySelector("#follow-up-reason");
const followUpStatus = document.querySelector("#follow-up-status");
const clearFollowUp = document.querySelector("#clear-follow-up");
const batchForm = document.querySelector("#batch-form");
const batchFile = document.querySelector("#batch-file");
const batchFileName = document.querySelector("#batch-file-name");
const batchSubmit = document.querySelector("#batch-submit");
const batchProgress = document.querySelector("#batch-progress");
const batchProgressLabel = document.querySelector("#batch-progress-label");
const batchCompletedCount = document.querySelector("#batch-completed-count");
const batchFailedCount = document.querySelector("#batch-failed-count");
const batchResultsPanel = document.querySelector("#batch-results-panel");
const batchResults = document.querySelector("#batch-results");
const batchRiskSort = document.querySelector("#batch-risk-sort");
const batchRiskFilter = document.querySelector("#batch-risk-filter");
const batchCompletenessFilter = document.querySelector("#batch-completeness-filter");
const batchReviewFilter = document.querySelector("#batch-review-filter");
const batchClearFilters = document.querySelector("#batch-clear-filters");
const batchFilterSummary = document.querySelector("#batch-filter-summary");
let batchSourceResults = [];

const previewDefinitions = [
  ["Profile", [["Username", "username"], ["Description", "description"], ["Location", "location"]]],
  ["Activity", [["Account age", "account_age_days"], ["Post count", "post_count"], ["Posts per day", "posts_per_day"]]],
  ["Network", [["Followers", "followers_count"], ["Following", "following_count"]]],
];

/** Toggle the intake form's visual and accessible busy state. */
function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  buttonLabel.hidden = isLoading;
  buttonLoading.hidden = !isLoading;
  form.setAttribute("aria-busy", String(isLoading));
}

/** Show an adjacent intake error and mark the identifier as invalid. */
function showError(message) {
  errorMessage.textContent = message;
  identifierInput.setAttribute("aria-invalid", "true");
  statusPanel.hidden = true;
}

/** Reveal recovery actions and optionally offer the same-request retry. */
function showRecovery(canRetry = true) {
  retryButton.hidden = !canRetry;
  recoveryActions.hidden = false;
}

/** Clear all single-assessment state and return focus to the first input. */
function startNewAssessment() {
  form.reset();
  decisionForm.reset();
  followUpForm.reset();
  currentAssessmentId = null;
  errorMessage.textContent = "";
  statusPanel.hidden = true;
  decisionAcknowledgement.textContent = "";
  decisionAcknowledgement.hidden = true;
  followUpStatus.textContent = "";
  followUpStatus.hidden = true;
  previewPanel.hidden = true;
  completenessPanel.hidden = true;
  riskPanel.hidden = true;
  decisionPanel.hidden = true;
  followUpPanel.hidden = true;
  recoveryActions.hidden = true;
  identifierInput.removeAttribute("aria-invalid");
  identifierInput.focus();
}

/** Remove the current validation message after the user corrects input. */
function clearError() {
  errorMessage.textContent = "";
  identifierInput.removeAttribute("aria-invalid");
}

/** Convert missing source values to the visible, non-imputed placeholder. */
function displayValue(value) {
  return value === null || value === undefined || value === ""
    ? "Not available"
    : String(value);
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

/** Render a scored result, its context, factors, and human-review controls. */
function renderRiskResult(result) {
  currentAssessmentId = result.assessment_id;
  riskBand.textContent = `${result.risk_band_label} risk`;
  riskBand.className = `risk-band ${result.risk_band}`;
  riskScore.textContent = `${result.risk_score}%`;
  modelVersion.textContent = result.model_version;
  thresholdVersion.textContent = result.threshold_version;
  assessmentTime.textContent = new Date(result.assessment_time).toLocaleString();
  riskWarning.textContent = result.warning;
  factorList.replaceChildren();
  for (const factor of result.top_factors) {
    const item = document.createElement("li");
    const label = document.createElement("strong");
    label.textContent = factor.label;
    const detail = document.createElement("span");
    detail.className = "factor-direction";
    const direction =
      factor.direction === "increases_risk" ? "Increases risk" : "Decreases risk";
    detail.textContent = `${direction} · Observed value: ${factor.observed_value ?? "Not available"}`;
    item.append(label, detail);
    factorList.append(item);
  }
  uncertaintyText.textContent = result.uncertainty;
  riskPanel.hidden = false;
  decisionPanel.hidden = false;
  followUpPanel.hidden = false;
  decisionForm.hidden = false;
  decisionAcknowledgement.hidden = true;
}

/** Request one score and handle the valid Insufficient-data response path. */
async function scoreAccount(accountId) {
  const response = await fetch("/api/v1/assessments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ platform: "x", account_id: accountId }),
  });
  const payload = await response.json();
  if (response.status === 422 && payload.status === "insufficient_data") {
    currentAssessmentId = payload.assessment_id;
    decisionPanel.hidden = true;
    followUpPanel.hidden = false;
    return;
  }
  if (!response.ok) {
    throw new Error(payload.error?.message || "Risk scoring is unavailable.");
  }
  renderRiskResult(payload);
}

/** Return a user-facing validation message, or an empty string when valid. */
function validateIdentifier(value) {
  const trimmed = value.trim();
  if (!trimmed) {
    return "Enter an offline account identifier or choose a demonstration scenario.";
  }
  if (!/^@?[A-Za-z0-9_]{1,32}$/.test(trimmed)) {
    return "Use only letters, numbers, or underscores after an optional @.";
  }
  return "";
}

/** Populate deterministic demonstration scenarios from the offline API. */
async function loadDemoAccounts() {
  try {
    const response = await fetch("/api/v1/demo/accounts?limit=3");
    if (!response.ok) {
      throw new Error("Demo accounts are unavailable.");
    }
    const payload = await response.json();
    for (const account of payload.accounts) {
      const option = document.createElement("option");
      option.value = account.username || account.account_id;
      option.textContent = account.display_label;
      option.dataset.scenario = account.scenario;
      demoSelect.append(option);
    }
  } catch {
    demoSelect.options[0].textContent = "Demonstration scenarios unavailable";
    demoSelect.disabled = true;
  }
}

demoSelect.addEventListener("change", () => {
  if (demoSelect.value) {
    identifierInput.value = `@${demoSelect.value}`;
    clearError();
  }
});

identifierInput.addEventListener("input", clearError);

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  const validationMessage = validateIdentifier(identifierInput.value);
  if (validationMessage) {
    showError(validationMessage);
    identifierInput.focus();
    return;
  }

  setLoading(true);
  try {
    const response = await fetch("/api/v1/intake", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier: identifierInput.value }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error?.message || "The assessment could not start.");
    }
    statusPanel.textContent =
      `${payload.display_identifier} is ready. One offline assessment has started; ` +
      "no live platform connection was made.";
    statusPanel.hidden = false;
    const previewResponse = await fetch(
      `/api/v1/accounts/${encodeURIComponent(payload.account_id)}/preview`,
    );
    if (!previewResponse.ok) {
      throw new Error("The public account preview could not be loaded.");
    }
    renderPreview(await previewResponse.json());
    const completenessResponse = await fetch(
      `/api/v1/accounts/${encodeURIComponent(payload.account_id)}/completeness`,
    );
    if (!completenessResponse.ok) {
      throw new Error("Feature completeness could not be calculated.");
    }
    const completeness = await completenessResponse.json();
    renderCompleteness(completeness);
    riskPanel.hidden = true;
    await scoreAccount(payload.account_id);
    showRecovery(false);
  } catch (error) {
    showError(error.message);
    showRecovery(true);
  } finally {
    setLoading(false);
  }
});

loadDemoAccounts();

retryButton.addEventListener("click", () => form.requestSubmit());
newAssessmentButton.addEventListener("click", startNewAssessment);

decisionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const decision = new FormData(decisionForm).get("decision");
  if (!decision || !currentAssessmentId) {
    return;
  }
  const reason = decisionReason.value.trim();
  if (decision === "override" && !reason) {
    decisionReason.setCustomValidity("Enter a reason before recording an override.");
    decisionReason.reportValidity();
    return;
  }
  decisionReason.setCustomValidity("");
  decisionSubmit.disabled = true;
  try {
    const response = await fetch(
      `/api/v1/assessments/${encodeURIComponent(currentAssessmentId)}/decision`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision, reason }),
      },
    );
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error?.message || "The decision could not be recorded.");
    }
    decisionAcknowledgement.textContent = payload.acknowledgement;
    decisionAcknowledgement.hidden = false;
    decisionForm.hidden = true;
  } catch (error) {
    decisionAcknowledgement.textContent = error.message;
    decisionAcknowledgement.hidden = false;
    decisionSubmit.disabled = false;
  }
});

/** Persist or clear the current assessment's authorised follow-up state. */
async function updateFollowUp(status) {
  if (!currentAssessmentId) return;
  const reason = followUpReason.value.trim();
  if (status === "flagged" && !reason) {
    followUpReason.reportValidity();
    return;
  }
  const response = await fetch(
    `/api/v1/assessments/${encodeURIComponent(currentAssessmentId)}/follow-up`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-Project-Role": "analyst",
      },
      body: JSON.stringify({ status, reason }),
    },
  );
  const payload = await response.json();
  followUpStatus.textContent = response.ok
    ? `${payload.status === "flagged" ? "Flagged" : "Cleared"}. ${payload.acknowledgement}`
    : payload.error?.message;
  followUpStatus.hidden = false;
}

followUpForm.addEventListener("submit", (event) => {
  event.preventDefault();
  updateFollowUp("flagged");
});
clearFollowUp.addEventListener("click", () => updateFollowUp("cleared"));

/** Snapshot the non-mutating sort and filter control values. */
function currentBatchControls() {
  return {
    sort: batchRiskSort.value,
    riskBand: batchRiskFilter.value,
    completeness: batchCompletenessFilter.value,
    reviewStatus: batchReviewFilter.value,
  };
}

/** Restore batch controls to the documented unfiltered source order. */
function resetBatchControls() {
  batchRiskSort.value = "none";
  batchRiskFilter.value = "all";
  batchCompletenessFilter.value = "all";
  batchReviewFilter.value = "all";
}

/** Render a derived batch view without mutating the API source results. */
function renderBatchResults() {
  const controls = currentBatchControls();
  const visibleResults = window.BatchResultTools.filterAndSort(
    batchSourceResults,
    controls,
  );
  batchResults.replaceChildren();
  for (const result of visibleResults) {
    const row = document.createElement("tr");
    const values = [
      result.row_number,
      result.account_id || "Not provided",
      result.processing_status,
      result.assessment_status || "Not assessed",
      result.risk_score === null ? "—" : `${result.risk_score}% ${result.risk_band}`,
      result.completeness_state || "—",
      result.error || "—",
    ];
    for (const value of values) {
      const cell = document.createElement("td");
      cell.textContent = String(value);
      row.append(cell);
    }
    batchResults.append(row);
  }
  batchFilterSummary.textContent = window.BatchResultTools.describeFilters(
    controls,
    visibleResults.length,
  );
  batchResultsPanel.hidden = false;
}

batchFile.addEventListener("change", () => {
  batchFileName.textContent = batchFile.files[0]?.name || "No file selected";
});

batchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = batchFile.files[0];
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".csv")) {
    batchProgressLabel.textContent = "Upload a .csv file using the template.";
    return;
  }
  resetBatchControls();
  batchSourceResults = [];
  batchSubmit.disabled = true;
  batchProgress.setAttribute("aria-busy", "true");
  batchProgressLabel.textContent = "Processing valid rows offline…";
  batchCompletedCount.textContent = "0";
  batchFailedCount.textContent = "0";
  batchResultsPanel.hidden = true;
  try {
    const response = await fetch("/api/v1/batch-assessments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: file.name, content: await file.text() }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error?.message || "The batch could not be assessed.");
    }
    batchCompletedCount.textContent = String(payload.completed_count);
    batchFailedCount.textContent = String(payload.failed_count);
    batchProgressLabel.textContent =
      `${payload.total_rows} rows processed. ${payload.acknowledgement}`;
    batchSourceResults = payload.results.map((result) => ({ ...result }));
    renderBatchResults();
  } catch (error) {
    batchProgressLabel.textContent = error.message;
  } finally {
    batchProgress.removeAttribute("aria-busy");
    batchSubmit.disabled = false;
  }
});

for (const control of [
  batchRiskSort,
  batchRiskFilter,
  batchCompletenessFilter,
  batchReviewFilter,
]) {
  control.addEventListener("change", renderBatchResults);
}

batchClearFilters.addEventListener("click", () => {
  resetBatchControls();
  renderBatchResults();
});

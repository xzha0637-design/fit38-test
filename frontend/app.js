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

const previewDefinitions = [
  ["Profile", [["Username", "username"], ["Description", "description"], ["Location", "location"]]],
  ["Activity", [["Account age", "account_age_days"], ["Post count", "post_count"], ["Posts per day", "posts_per_day"]]],
  ["Network", [["Followers", "followers_count"], ["Following", "following_count"]]],
];

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  buttonLabel.hidden = isLoading;
  buttonLoading.hidden = !isLoading;
  form.setAttribute("aria-busy", String(isLoading));
}

function showError(message) {
  errorMessage.textContent = message;
  identifierInput.setAttribute("aria-invalid", "true");
  statusPanel.hidden = true;
}

function clearError() {
  errorMessage.textContent = "";
  identifierInput.removeAttribute("aria-invalid");
}

function displayValue(value) {
  return value === null || value === undefined || value === ""
    ? "Not available"
    : String(value);
}

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

function renderRiskResult(result) {
  riskBand.textContent = `${result.risk_band_label} risk`;
  riskBand.className = `risk-band ${result.risk_band}`;
  riskScore.textContent = `${result.risk_score}%`;
  modelVersion.textContent = result.model_version;
  thresholdVersion.textContent = result.threshold_version;
  assessmentTime.textContent = new Date(result.assessment_time).toLocaleString();
  riskWarning.textContent = result.warning;
  riskPanel.hidden = false;
}

async function scoreAccount(accountId) {
  const response = await fetch("/api/v1/assessments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ platform: "x", account_id: accountId }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error?.message || "Risk scoring is unavailable.");
  }
  renderRiskResult(payload);
}

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
    if (completeness.eligible_for_scoring) {
      await scoreAccount(payload.account_id);
    }
  } catch (error) {
    showError(error.message);
  } finally {
    setLoading(false);
  }
});

loadDemoAccounts();

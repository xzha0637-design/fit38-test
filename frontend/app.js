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
  } catch (error) {
    showError(error.message);
  } finally {
    setLoading(false);
  }
});

loadDemoAccounts();

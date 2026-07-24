const form = document.querySelector("#intake-form");
const identifierInput = document.querySelector("#account-identifier");
const demoSelect = document.querySelector("#demo-account");
const errorMessage = document.querySelector("#identifier-error");
const statusPanel = document.querySelector("#intake-status");
const submitButton = document.querySelector("#assess-button");
const buttonLabel = submitButton.querySelector(".button-label");
const buttonLoading = submitButton.querySelector(".button-loading");

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
  } catch (error) {
    showError(error.message);
  } finally {
    setLoading(false);
  }
});

loadDemoAccounts();

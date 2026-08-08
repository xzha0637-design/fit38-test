/** Coordinate intake, API workflow, restoration, and focused UI modules. */

const form = document.querySelector("#intake-form");
const identifierInput = document.querySelector("#account-identifier");
const demoSelect = document.querySelector("#demo-account");
const errorMessage = document.querySelector("#identifier-error");
const statusPanel = document.querySelector("#intake-status");
const submitButton = document.querySelector("#assess-button");
const buttonLabel = submitButton.querySelector(".button-label");
const buttonLoading = submitButton.querySelector(".button-loading");
const recoveryActions = document.querySelector("#recovery-actions");
const retryButton = document.querySelector("#retry-button");
const newAssessmentButton = document.querySelector("#new-assessment-button");

const { requestJson } = window.SignalReviewApi;
const assessmentState = window.SignalReviewAssessmentState;
const assessmentView = window.SignalReviewAssessmentView;
const reviewController = window.SignalReviewReviewController;
const batchController = window.SignalReviewBatchController;
let currentAssessmentSnapshot = null;

/** Return a stable message even if a non-Error value is unexpectedly thrown. */
function safeErrorMessage(error, fallback) {
  return error instanceof Error && error.message ? error.message : fallback;
}

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

/** Clear all rendered single-assessment and review-action output. */
function clearRenderedAssessment() {
  reviewController.reset();
  assessmentView.clear();
  recoveryActions.hidden = true;
}

/** Persist only the validated preview, result, and review UI for this tab. */
function persistAssessmentState(snapshot) {
  currentAssessmentSnapshot = assessmentState.saveSnapshot(snapshot);
}

/** Remove the transient assessment snapshot when it is no longer current. */
function clearPersistedAssessmentState() {
  currentAssessmentSnapshot = null;
  assessmentState.clearSnapshot();
}

/** Merge one review-action update into the current validated session snapshot. */
function persistReviewState(update) {
  if (!currentAssessmentSnapshot) return;
  persistAssessmentState({
    ...currentAssessmentSnapshot,
    review: {
      ...(currentAssessmentSnapshot.review || {}),
      ...update,
    },
  });
}

/** Remove a result-only return target when no restorable result exists. */
function clearUnusedResultHash() {
  if (window.location.hash !== "#assessment-results") return;
  history.replaceState(null, "", window.location.pathname);
  requestAnimationFrame(() => window.scrollTo({ top: 0, left: 0 }));
}

/** Clear all single-assessment state and return focus to the first input. */
function startNewAssessment() {
  form.reset();
  clearRenderedAssessment();
  clearPersistedAssessmentState();
  errorMessage.textContent = "";
  statusPanel.textContent = "";
  statusPanel.hidden = true;
  identifierInput.removeAttribute("aria-invalid");
  if (window.location.hash === "#assessment-results") {
    history.replaceState(null, "", window.location.pathname);
  }
  identifierInput.focus();
}

/** Remove the current validation message after the user corrects input. */
function clearError() {
  errorMessage.textContent = "";
  identifierInput.removeAttribute("aria-invalid");
}

/** Restore one validated assessment after returning from model information. */
function restoreAssessmentState() {
  const saved = assessmentState.loadSnapshot();
  if (!saved) {
    clearUnusedResultHash();
    return;
  }

  currentAssessmentSnapshot = saved;
  identifierInput.value = saved.identifier;
  statusPanel.textContent = saved.status;
  statusPanel.hidden = false;
  assessmentView.renderPreview(saved.preview);
  assessmentView.renderCompleteness(saved.completeness);
  reviewController.setAssessment(saved.assessment.payload.assessment_id);
  if (saved.assessment.kind === "scored") {
    assessmentView.renderRiskResult(saved.assessment.payload);
  } else {
    assessmentView.renderInsufficientResult();
  }
  reviewController.restore(saved.review);
  showRecovery(false);

  if (window.location.hash === "#assessment-results") {
    requestAnimationFrame(() => {
      assessmentView.assessmentResults.scrollIntoView({ block: "start" });
      assessmentView.assessmentResults.focus({ preventScroll: true });
    });
  }
}

/** Request one score and handle the valid Insufficient-data response path. */
async function scoreAccount(accountId) {
  const { response, payload } = await requestJson(
    "/api/v1/assessments",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ platform: "x", account_id: accountId }),
    },
    {
      acceptedStatuses: [422],
      fallbackMessage: "Risk scoring is unavailable.",
    },
  );
  reviewController.setAssessment(payload.assessment_id);
  if (response.status === 422 && payload.status === "insufficient_data") {
    assessmentView.renderInsufficientResult();
    return { kind: "insufficient", payload };
  }
  assessmentView.renderRiskResult(payload);
  return { kind: "scored", payload };
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
    const { payload } = await requestJson(
      "/api/v1/demo/accounts?limit=3",
      {},
      { fallbackMessage: "Demo accounts are unavailable." },
    );
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

/** Run intake, preview, completeness, and scoring as one recoverable workflow. */
async function submitAssessment(event) {
  event.preventDefault();
  clearError();
  const validationMessage = validateIdentifier(identifierInput.value);
  if (validationMessage) {
    showError(validationMessage);
    identifierInput.focus();
    return;
  }

  clearRenderedAssessment();
  clearPersistedAssessmentState();
  statusPanel.hidden = true;
  setLoading(true);
  try {
    const { payload } = await requestJson(
      "/api/v1/intake",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier: identifierInput.value }),
      },
      { fallbackMessage: "The assessment could not start." },
    );
    statusPanel.textContent =
      `${payload.display_identifier} is ready. One offline assessment has started; ` +
      "no live platform connection was made.";
    statusPanel.hidden = false;
    const { payload: preview } = await requestJson(
      `/api/v1/accounts/${encodeURIComponent(payload.account_id)}/preview`,
      {},
      { fallbackMessage: "The public account preview could not be loaded." },
    );
    assessmentView.renderPreview(preview);
    const { payload: completeness } = await requestJson(
      `/api/v1/accounts/${encodeURIComponent(payload.account_id)}/completeness`,
      {},
      { fallbackMessage: "Feature completeness could not be calculated." },
    );
    assessmentView.renderCompleteness(completeness);
    const assessment = await scoreAccount(payload.account_id);
    persistAssessmentState({
      identifier: payload.display_identifier,
      status: statusPanel.textContent,
      preview,
      completeness,
      assessment,
      review: { decision: null, followUp: null },
    });
    showRecovery(false);
  } catch (error) {
    clearRenderedAssessment();
    showError(safeErrorMessage(error, "The assessment could not be completed."));
    showRecovery(true);
  } finally {
    setLoading(false);
  }
}

reviewController.initialise(persistReviewState);
batchController.initialise();
demoSelect.addEventListener("change", () => {
  if (demoSelect.value) {
    identifierInput.value = `@${demoSelect.value}`;
    clearError();
  }
});
identifierInput.addEventListener("input", clearError);
form.addEventListener("submit", submitAssessment);
retryButton.addEventListener("click", () => form.requestSubmit());
newAssessmentButton.addEventListener("click", startNewAssessment);
restoreAssessmentState();
loadDemoAccounts();

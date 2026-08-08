(function exposeReviewController(globalObject) {
  "use strict";

  const decisionForm = document.querySelector("#decision-form");
  const decisionReason = document.querySelector("#decision-reason");
  const decisionSubmit = document.querySelector("#decision-submit");
  const decisionAcknowledgement = document.querySelector("#decision-acknowledgement");
  const followUpForm = document.querySelector("#follow-up-form");
  const followUpReason = document.querySelector("#follow-up-reason");
  const followUpStatus = document.querySelector("#follow-up-status");
  const clearFollowUp = document.querySelector("#clear-follow-up");
  const followUpSubmit = followUpForm.querySelector('button[type="submit"]');
  const { requestJson } = globalObject.SignalReviewApi;

  let currentAssessmentId = null;
  let decisionRequestPending = false;
  let followUpRequestPending = false;
  let onReviewStateChange = () => {};
  let initialised = false;

  /** Return a stable message even if a non-Error value is unexpectedly thrown. */
  function errorMessage(error, fallback) {
    return error instanceof Error && error.message ? error.message : fallback;
  }

  /** Bind subsequent review actions to the assessment currently on screen. */
  function setAssessment(assessmentId) {
    currentAssessmentId = assessmentId;
  }

  /** Restore review forms to their untouched state for a new assessment. */
  function reset() {
    decisionForm.reset();
    followUpForm.reset();
    currentAssessmentId = null;
    decisionRequestPending = false;
    decisionAcknowledgement.textContent = "";
    decisionAcknowledgement.hidden = true;
    decisionSubmit.disabled = false;
    decisionForm.hidden = false;
    followUpStatus.textContent = "";
    followUpStatus.hidden = true;
    setFollowUpLoading(false);
  }

  /** Restore submitted decision and follow-up controls without repeating a request. */
  function restore(review = {}) {
    if (review.decision) {
      decisionAcknowledgement.textContent = review.decision.acknowledgement;
      decisionAcknowledgement.hidden = false;
      decisionSubmit.disabled = true;
      decisionForm.hidden = true;
    }
    if (review.followUp) {
      followUpReason.value = review.followUp.status === "flagged"
        ? review.followUp.reason
        : "";
      followUpStatus.textContent = review.followUp.message;
      followUpStatus.hidden = false;
    }
  }

  /** Toggle both follow-up actions while one update is in flight. */
  function setFollowUpLoading(isLoading) {
    followUpRequestPending = isLoading;
    followUpReason.disabled = isLoading;
    clearFollowUp.disabled = isLoading;
    followUpSubmit.disabled = isLoading;
    followUpForm.setAttribute("aria-busy", String(isLoading));
  }

  /** Persist or clear the current assessment's authorised follow-up state. */
  async function updateFollowUp(status) {
    if (!currentAssessmentId || followUpRequestPending) return;
    const reason = followUpReason.value.trim();
    if (status === "flagged" && !reason) {
      followUpReason.setCustomValidity("Enter a reason before saving a follow-up flag.");
      followUpReason.reportValidity();
      return;
    }
    followUpReason.setCustomValidity("");
    setFollowUpLoading(true);
    followUpStatus.textContent = status === "flagged" ? "Saving flag…" : "Clearing flag…";
    followUpStatus.hidden = false;
    try {
      const { payload } = await requestJson(
        `/api/v1/assessments/${encodeURIComponent(currentAssessmentId)}/follow-up`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "X-Project-Role": "analyst",
          },
          body: JSON.stringify({ status, reason }),
        },
        { fallbackMessage: "The follow-up status could not be updated." },
      );
      const message =
        `${payload.status === "flagged" ? "Flagged" : "Cleared"}. ${payload.acknowledgement}`;
      followUpStatus.textContent = message;
      if (payload.status === "cleared") followUpReason.value = "";
      onReviewStateChange({
        followUp: {
          status: payload.status,
          reason: payload.status === "flagged" ? reason : "",
          message,
        },
      });
    } catch (error) {
      followUpStatus.textContent = errorMessage(
        error,
        "The follow-up status could not be updated.",
      );
    } finally {
      setFollowUpLoading(false);
    }
  }

  /** Record the single final analyst decision while preventing double submit. */
  async function submitDecision(event) {
    event.preventDefault();
    if (decisionRequestPending) return;
    const decision = new FormData(decisionForm).get("decision");
    if (!decision || !currentAssessmentId) return;
    const reason = decisionReason.value.trim();
    if (decision === "override" && !reason) {
      decisionReason.setCustomValidity("Enter a reason before recording an override.");
      decisionReason.reportValidity();
      return;
    }
    decisionReason.setCustomValidity("");
    decisionRequestPending = true;
    decisionSubmit.disabled = true;
    try {
      const { payload } = await requestJson(
        `/api/v1/assessments/${encodeURIComponent(currentAssessmentId)}/decision`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ decision, reason }),
        },
        { fallbackMessage: "The decision could not be recorded." },
      );
      decisionAcknowledgement.textContent = payload.acknowledgement;
      decisionAcknowledgement.hidden = false;
      decisionForm.hidden = true;
      onReviewStateChange({
        decision: { value: decision, acknowledgement: payload.acknowledgement },
      });
    } catch (error) {
      decisionAcknowledgement.textContent = errorMessage(
        error,
        "The decision could not be recorded.",
      );
      decisionAcknowledgement.hidden = false;
      decisionSubmit.disabled = false;
    } finally {
      decisionRequestPending = false;
    }
  }

  /** Attach review listeners once and provide the session-persistence callback. */
  function initialise(reviewStateCallback) {
    onReviewStateChange = reviewStateCallback;
    if (initialised) return;
    decisionForm.addEventListener("submit", submitDecision);
    followUpForm.addEventListener("submit", (event) => {
      event.preventDefault();
      updateFollowUp("flagged");
    });
    clearFollowUp.addEventListener("click", () => updateFollowUp("cleared"));
    initialised = true;
  }

  const controller = Object.freeze({ initialise, reset, restore, setAssessment });
  globalObject.SignalReviewReviewController = controller;
})(typeof window === "undefined" ? globalThis : window);

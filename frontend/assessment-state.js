(function exposeAssessmentState(globalObject) {
  "use strict";

  const STORAGE_KEY = "signal-review.current-assessment.v2";
  const LEGACY_STORAGE_KEYS = ["signal-review.current-assessment.v1"];
  const SCHEMA_VERSION = 2;
  const ASSESSMENT_ID_PATTERN = /^asmt_(?:[0-9a-f]{8}|[0-9a-f]{32})$/;

  /** Return true only for a plain JSON object. */
  function isObject(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  }

  /** Validate a bounded user-visible string. */
  function isText(value, maximum = 1000) {
    return typeof value === "string" && value.length > 0 && value.length <= maximum;
  }

  /** Validate a short list of display labels. */
  function isTextList(value) {
    return Array.isArray(value) && value.length <= 20 && value.every((item) => isText(item, 120));
  }

  /** Validate a source field that may be explicitly unavailable. */
  function isNullableText(value, maximum = 1000) {
    return value === null || isText(value, maximum);
  }

  /** Validate a public numeric field that may be explicitly unavailable. */
  function isNullableNumber(value) {
    return value === null || (typeof value === "number" && Number.isFinite(value));
  }

  /** Check the whitelisted public preview structure used by the renderer. */
  function isPreview(value) {
    return (
      isObject(value) &&
      isText(value.account_id, 64) &&
      isText(value.display_identifier, 64) &&
      isObject(value.profile) &&
      isNullableText(value.profile.username, 64) &&
      isNullableText(value.profile.description, 1000) &&
      isNullableText(value.profile.location, 240) &&
      isObject(value.activity) &&
      isNullableNumber(value.activity.account_age_days) &&
      isNullableNumber(value.activity.post_count) &&
      isNullableNumber(value.activity.posts_per_day) &&
      isObject(value.network) &&
      isNullableNumber(value.network.followers_count) &&
      isNullableNumber(value.network.following_count) &&
      isTextList(value.missing_fields)
    );
  }

  /** Check the bounded completeness contract used by the progress meter. */
  function isCompleteness(value) {
    return (
      isObject(value) &&
      Number.isInteger(value.completeness_percentage) &&
      value.completeness_percentage >= 0 &&
      value.completeness_percentage <= 100 &&
      typeof value.eligible_for_scoring === "boolean" &&
      ["Eligible for scoring", "Insufficient data"].includes(value.status) &&
      value.eligible_for_scoring === (value.status === "Eligible for scoring") &&
      isTextList(value.missing_features) &&
      (value.missing_data_caveat === null ||
        value.missing_data_caveat === undefined ||
        isText(value.missing_data_caveat, 500))
    );
  }

  /** Check the common identity fields of a scored or insufficient assessment. */
  function hasAssessmentIdentity(value) {
    return (
      isObject(value) &&
      typeof value.assessment_id === "string" &&
      ASSESSMENT_ID_PATTERN.test(value.assessment_id) &&
      isText(value.account_id, 64)
    );
  }

  /** Validate the displayed assessment payload for its declared result kind. */
  function isAssessment(value) {
    if (!isObject(value) || !["scored", "insufficient"].includes(value.kind)) return false;
    const payload = value.payload;
    if (!hasAssessmentIdentity(payload)) return false;
    if (value.kind === "insufficient") {
      return payload.status === "insufficient_data" && isText(payload.warning, 500);
    }
    const factorsValid =
      Array.isArray(payload.top_factors) &&
      payload.top_factors.length <= 3 &&
      payload.top_factors.every(
        (factor) =>
          isObject(factor) &&
          isText(factor.feature, 120) &&
          (factor.label === null ||
            factor.label === undefined ||
            isText(factor.label, 120)) &&
          ["increases_risk", "decreases_risk"].includes(factor.direction) &&
          (factor.observed_value === null || isText(factor.observed_value, 120)),
      );
    return (
      ["completed", "completed_with_warning"].includes(payload.status) &&
      Number.isInteger(payload.risk_score) &&
      payload.risk_score >= 0 &&
      payload.risk_score <= 100 &&
      ["low", "medium", "high"].includes(payload.risk_band) &&
      ["Low", "Medium", "High"].includes(payload.risk_band_label) &&
      isText(payload.model_version, 120) &&
      isText(payload.threshold_version, 120) &&
      isText(payload.assessment_time, 80) &&
      !Number.isNaN(Date.parse(payload.assessment_time)) &&
      ["no_concern", "monitor", "prioritise"].includes(payload.recommendation) &&
      isText(payload.warning, 500) &&
      isText(payload.uncertainty, 500) &&
      factorsValid
    );
  }

  /** Validate optional decision and follow-up state restored into the controls. */
  function isReviewState(value) {
    if (value === undefined) return true;
    if (!isObject(value)) return false;
    const decisionValid =
      value.decision === null ||
      value.decision === undefined ||
      (isObject(value.decision) &&
        ["confirm", "override"].includes(value.decision.value) &&
        isText(value.decision.acknowledgement, 500));
    const followUpValid =
      value.followUp === null ||
      value.followUp === undefined ||
      (isObject(value.followUp) &&
        ["flagged", "cleared"].includes(value.followUp.status) &&
        typeof value.followUp.reason === "string" &&
        value.followUp.reason.length <= 240 &&
        isText(value.followUp.message, 500));
    return decisionValid && followUpValid;
  }

  /** Validate the complete versioned session snapshot before rendering any field. */
  function validateSnapshot(value) {
    const structureValid = (
      isObject(value) &&
      value.schemaVersion === SCHEMA_VERSION &&
      isText(value.identifier, 64) &&
      isText(value.status, 500) &&
      isPreview(value.preview) &&
      isCompleteness(value.completeness) &&
      isAssessment(value.assessment) &&
      isReviewState(value.review)
    );
    if (!structureValid) return false;
    return value.assessment.kind === "scored" || !value.review?.decision;
  }

  /** Save a versioned snapshot and return the in-memory value used by the page. */
  function saveSnapshot(snapshot, storage = null) {
    const versioned = { ...snapshot, schemaVersion: SCHEMA_VERSION };
    try {
      (storage || globalObject.sessionStorage).setItem(
        STORAGE_KEY,
        JSON.stringify(versioned),
      );
    } catch {
      // Disabled or full storage must not break the current page workflow.
    }
    return versioned;
  }

  /** Load only a valid snapshot; remove malformed or stale data immediately. */
  function loadSnapshot(storage = null) {
    try {
      const raw = (storage || globalObject.sessionStorage).getItem(STORAGE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (validateSnapshot(parsed)) return parsed;
    } catch {
      // Invalid JSON and inaccessible storage both fall through to safe cleanup.
    }
    clearSnapshot(storage);
    return null;
  }

  /** Remove the current versioned snapshot without surfacing storage failures. */
  function clearSnapshot(storage = null) {
    try {
      const target = storage || globalObject.sessionStorage;
      target.removeItem(STORAGE_KEY);
      for (const legacyKey of LEGACY_STORAGE_KEYS) target.removeItem(legacyKey);
    } catch {
      // The page already has no reliable retained state to use.
    }
  }

  const assessmentState = Object.freeze({
    STORAGE_KEY,
    clearSnapshot,
    loadSnapshot,
    saveSnapshot,
    validateSnapshot,
  });
  globalObject.SignalReviewAssessmentState = assessmentState;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = assessmentState;
  }
})(typeof window === "undefined" ? globalThis : window);

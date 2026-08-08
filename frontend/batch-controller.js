(function exposeBatchController(globalObject) {
  "use strict";

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
  const { requestJson } = globalObject.SignalReviewApi;

  let batchSourceResults = [];
  let initialised = false;

  /** Snapshot the non-mutating sort and filter control values. */
  function currentControls() {
    return {
      sort: batchRiskSort.value,
      riskBand: batchRiskFilter.value,
      completeness: batchCompletenessFilter.value,
      reviewStatus: batchReviewFilter.value,
    };
  }

  /** Restore batch controls to the documented unfiltered source order. */
  function resetControls() {
    batchRiskSort.value = "none";
    batchRiskFilter.value = "all";
    batchCompletenessFilter.value = "all";
    batchReviewFilter.value = "all";
  }

  /** Render a derived batch view without mutating the API source results. */
  function renderResults() {
    const controls = currentControls();
    const visibleResults = globalObject.BatchResultTools.filterAndSort(
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
    batchFilterSummary.textContent = globalObject.BatchResultTools.describeFilters(
      controls,
      visibleResults.length,
    );
    batchResultsPanel.hidden = false;
  }

  /** Read, submit, and render one bounded offline CSV batch. */
  async function submitBatch(event) {
    event.preventDefault();
    const file = batchFile.files[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".csv")) {
      batchProgressLabel.textContent = "Upload a .csv file using the template.";
      return;
    }
    resetControls();
    batchSourceResults = [];
    batchSubmit.disabled = true;
    batchProgress.setAttribute("aria-busy", "true");
    batchProgressLabel.textContent = "Processing valid rows offline…";
    batchCompletedCount.textContent = "0";
    batchFailedCount.textContent = "0";
    batchResultsPanel.hidden = true;
    try {
      const { payload } = await requestJson(
        "/api/v1/batch-assessments",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ filename: file.name, content: await file.text() }),
        },
        { fallbackMessage: "The batch could not be assessed." },
      );
      batchCompletedCount.textContent = String(payload.completed_count);
      batchFailedCount.textContent = String(payload.failed_count);
      batchProgressLabel.textContent =
        `${payload.total_rows} rows processed. ${payload.acknowledgement}`;
      batchSourceResults = payload.results.map((result) => ({ ...result }));
      renderResults();
    } catch (error) {
      batchProgressLabel.textContent =
        error instanceof Error ? error.message : "The batch could not be assessed.";
    } finally {
      batchProgress.removeAttribute("aria-busy");
      batchSubmit.disabled = false;
    }
  }

  /** Attach batch upload and filter listeners once. */
  function initialise() {
    if (initialised) return;
    batchFile.addEventListener("change", () => {
      batchFileName.textContent = batchFile.files[0]?.name || "No file selected";
    });
    batchForm.addEventListener("submit", submitBatch);
    for (const control of [
      batchRiskSort,
      batchRiskFilter,
      batchCompletenessFilter,
      batchReviewFilter,
    ]) {
      control.addEventListener("change", renderResults);
    }
    batchClearFilters.addEventListener("click", () => {
      resetControls();
      renderResults();
    });
    initialised = true;
  }

  const controller = Object.freeze({ initialise });
  globalObject.SignalReviewBatchController = controller;
})(typeof window === "undefined" ? globalThis : window);

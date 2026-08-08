(function exposeBatchResultTools(globalObject) {
  /** Return cloned rows that match the controls, with unscored rows kept last. */
  function filterAndSort(results, controls) {
    const filtered = results.filter((result) => {
      const reviewStatus = result.review_status || "unavailable";
      return (
        (controls.riskBand === "all" || result.risk_band === controls.riskBand) &&
        (controls.completeness === "all" ||
          result.completeness_state === controls.completeness) &&
        (controls.reviewStatus === "all" ||
          reviewStatus === controls.reviewStatus)
      );
    });

    if (controls.sort === "none") {
      return filtered.map((result) => ({ ...result }));
    }
    const direction = controls.sort === "ascending" ? 1 : -1;
    return filtered
      .map((result) => ({ ...result }))
      .sort((left, right) => {
        if (left.risk_score === null && right.risk_score === null) {
          return left.row_number - right.row_number;
        }
        if (left.risk_score === null) return 1;
        if (right.risk_score === null) return -1;
        const leftScore = left.risk_score;
        const rightScore = right.risk_score;
        const scoreOrder = (leftScore - rightScore) * direction;
        return scoreOrder || left.row_number - right.row_number;
      });
  }

  /** Summarise active controls and the number of currently visible rows. */
  function describeFilters(controls, matchingCount) {
    const active = [];
    if (controls.sort !== "none") active.push(`risk ${controls.sort}`);
    if (controls.riskBand !== "all") active.push(`${controls.riskBand} risk`);
    if (controls.completeness !== "all") active.push(controls.completeness);
    if (controls.reviewStatus !== "all") active.push(controls.reviewStatus);
    const description = active.length
      ? `Active: ${active.join(", ")}`
      : "No active filters";
    return `${description} | ${matchingCount} matching records`;
  }

  const tools = { filterAndSort, describeFilters };
  globalObject.BatchResultTools = tools;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = tools;
  }
})(typeof window === "undefined" ? globalThis : window);

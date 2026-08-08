(function exposeApiClient(globalObject) {
  "use strict";

  const DEFAULT_TIMEOUT_MS = 10000;

  class ApiRequestError extends Error {
    /** Describe one controlled HTTP, network, timeout, or response-format failure. */
    constructor(message, status = 0, code = "request_failed") {
      super(message);
      this.name = "ApiRequestError";
      this.status = status;
      this.code = code;
    }
  }

  /** Parse JSON without exposing an HTML error page or parser exception to users. */
  async function parseJsonResponse(response, fallbackMessage) {
    const text = await response.text();
    if (!text) return {};
    try {
      return JSON.parse(text);
    } catch {
      throw new ApiRequestError(
        fallbackMessage || "The local service returned an unreadable response.",
        response.status,
        "invalid_response",
      );
    }
  }

  /** Fetch one JSON contract with a timeout and consistent safe error messages. */
  async function requestJson(url, options = {}, config = {}) {
    const controller = new globalObject.AbortController();
    const timeoutMs = config.timeoutMs ?? DEFAULT_TIMEOUT_MS;
    const acceptedStatuses = config.acceptedStatuses || [];
    const fallbackMessage = config.fallbackMessage || "The request could not be completed.";
    const timeoutId = globalObject.setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await globalObject.fetch(url, {
        ...options,
        signal: controller.signal,
      });
      const payload = await parseJsonResponse(response, fallbackMessage);
      if (!response.ok && !acceptedStatuses.includes(response.status)) {
        throw new ApiRequestError(
          payload?.error?.message || fallbackMessage,
          response.status,
          payload?.error?.code || "http_error",
        );
      }
      return { response, payload };
    } catch (error) {
      if (error?.name === "AbortError") {
        throw new ApiRequestError(
          "The local service did not respond in time. Check it is running and try again.",
          0,
          "request_timeout",
        );
      }
      if (error instanceof ApiRequestError) throw error;
      throw new ApiRequestError(
        "The local service could not be reached. Check it is running and try again.",
        0,
        "network_error",
      );
    } finally {
      globalObject.clearTimeout(timeoutId);
    }
  }

  const apiClient = Object.freeze({ ApiRequestError, requestJson });
  globalObject.SignalReviewApi = apiClient;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = apiClient;
  }
})(typeof window === "undefined" ? globalThis : window);

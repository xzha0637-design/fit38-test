class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable


class ModelUnavailableError(RuntimeError):
    """Raised when inference artifacts are not ready."""


class ExplanationUnavailableError(RuntimeError):
    """Raised after scoring succeeds but a SHAP explanation cannot be produced."""


class MalformedModelResponseError(RuntimeError):
    """Raised when a model response does not satisfy the scoring contract."""

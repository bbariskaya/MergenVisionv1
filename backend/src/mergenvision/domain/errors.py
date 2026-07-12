class DomainError(Exception):
    pass


class SecurityError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class NotFoundError(DomainError):
    pass


class ValidationError(DomainError):
    pass


class RepositoryError(DomainError):
    pass


class _RetryableDomainError(DomainError):
    def __init__(self, message: str = "", *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class ObjectStorageError(_RetryableDomainError):
    pass


class ObjectConflictError(ObjectStorageError):
    pass


class VectorIndexError(_RetryableDomainError):
    pass


class VectorContractError(VectorIndexError):
    pass


class CrossStoreConsistencyError(_RetryableDomainError):
    pass


class ReconciliationRequiredError(CrossStoreConsistencyError):
    pass

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

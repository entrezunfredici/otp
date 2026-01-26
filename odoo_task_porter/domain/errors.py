"""Custom errors for the domain."""


class PorterError(Exception):
    """Base error for the task porter."""


class ValidationError(PorterError):
    """Raised when markdown parsing or validation fails."""


class OdooError(PorterError):
    """Raised when Odoo operations fail."""

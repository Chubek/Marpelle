class MarpelleError(Exception):
    """Base error for all marpelle exceptions."""


class ManifestError(MarpelleError):
    """Raised when manifest loading or validation fails."""


class RegistryError(MarpelleError):
    """Raised when registry actions fail."""


class IPCError(MarpelleError):
    """Raised when IPC operations fail."""

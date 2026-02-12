"""Custom exceptions for Jenkins MCP Server."""


class JenkinsMCPError(Exception):
    """Base exception for Jenkins MCP Server."""
    pass


class JenkinsConnectionError(JenkinsMCPError):
    """Raised when Jenkins connection fails."""
    pass


class JenkinsAuthenticationError(JenkinsMCPError):
    """Raised when Jenkins authentication fails."""
    pass


class JenkinsNotFoundError(JenkinsMCPError):
    """Raised when Jenkins resource is not found."""
    pass


class JenkinsPermissionError(JenkinsMCPError):
    """Raised when Jenkins operation is not permitted."""
    pass


class JenkinsConfigurationError(JenkinsMCPError):
    """Raised when Jenkins configuration is invalid."""
    pass


class JenkinsBuildError(JenkinsMCPError):
    """Raised when Jenkins build operation fails."""
    pass


class JenkinsResourceError(JenkinsMCPError):
    """Raised when Jenkins resource access fails."""
    pass


class JenkinsValidationError(JenkinsMCPError):
    """Raised when input validation fails."""
    pass
class UIWError(Exception):
    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class ConfigError(UIWError):
    pass


class ValidationError(UIWError):
    pass


class CommandExecutionError(UIWError):
    pass


class WorkspaceNotFoundError(UIWError):
    pass


class WorkspaceConflictError(UIWError):
    pass


class DirtyWorkspaceError(UIWError):
    pass


class UnsafePathError(UIWError):
    pass


class RegistryError(UIWError):
    pass

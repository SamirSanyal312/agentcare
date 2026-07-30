class WorkflowError(Exception):
    """Base workflow exception."""


class PatientRequestNotFoundError(WorkflowError):
    pass


class PatientRequestAccessDeniedError(WorkflowError):
    pass


class WorkflowNotFoundError(WorkflowError):
    pass


class InvalidWorkflowTransitionError(WorkflowError):
    pass
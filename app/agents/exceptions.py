class AgentError(Exception):
    """Base error for AgentCare agents."""


class SafetyAgentError(AgentError):
    """Raised when the Safety Agent cannot produce a valid decision."""
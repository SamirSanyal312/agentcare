from enum import Enum


class UserRole(str, Enum):
    PATIENT = "patient"
    STAFF = "staff"
    ADMIN = "admin"


class RequestStatus(str, Enum):
    RECEIVED = "received"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_HUMAN = "waiting_for_human"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    WAITING_FOR_HUMAN = "waiting_for_human"
    COMPLETED = "completed"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED = "failed"


class SlotStatus(str, Enum):
    AVAILABLE = "available"
    HELD = "held"
    BOOKED = "booked"
    UNAVAILABLE = "unavailable"


class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    CLASSIFIED = "classified"
    REJECTED = "rejected"


class ReminderStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FollowUpStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"


class EscalationStatus(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"


class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
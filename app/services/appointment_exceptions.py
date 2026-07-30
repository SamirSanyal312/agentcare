class AppointmentError(Exception):
    """Base exception for appointment operations."""


class DepartmentNotFoundError(AppointmentError):
    pass


class DoctorNotFoundError(AppointmentError):
    pass


class SlotNotFoundError(AppointmentError):
    pass


class SlotUnavailableError(AppointmentError):
    pass


class AppointmentNotFoundError(AppointmentError):
    pass


class AppointmentAccessDeniedError(AppointmentError):
    pass


class InvalidAppointmentStateError(AppointmentError):
    pass


class InvalidDateRangeError(AppointmentError):
    pass
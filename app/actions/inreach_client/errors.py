

class InReachClientError(Exception):
    # Optional support for storing the api response
    def __init__(self, message=None, response=None):
        super().__init__(message)
        self.response = response


class InReachServiceUnreachable(InReachClientError):
    def __init__(self, message="The InReach service is currently unavailable.", response=None):
        super().__init__(message, response)


class InReachInternalError(InReachClientError):
    def __init__(self, message="An unexpected error occurred in InReach API.", response=None):
        super().__init__(message, response)


class InReachTooManyRequestsError(InReachClientError):
    def __init__(self, message="Too many concurrent requests are being processed.", response=None):
        super().__init__(message, response)


class InReachAuthenticationError(InReachClientError):
    def __init__(self, message="Invalid username or password.", response=None):
        super().__init__(message, response)


class InReachUnknownDeviceError(InReachClientError):
    def __init__(self, message="The specified IMEI does not belong to the tenant.", response=None):
        super().__init__(message, response)


class InReachInvalidMessageError(InReachClientError):
    def __init__(self, message="The message length is invalid (valid range: 1-160).", response=None):
        super().__init__(message, response)


class InReachInvalidTimestampError(InReachClientError):
    def __init__(self, message="The message timestamp is invalid (valid range: Jan 2011 - Current date).", response=None):
        super().__init__(message, response)


class InReachInvalidSenderError(InReachClientError):
    def __init__(self, message="The message sender is invalid (must be a valid phone number or email address).", response=None, ):
        super().__init__(message, response)


class InReachInvalidAltitudeError(InReachClientError):
    def __init__(self, message="The location's altitude is invalid (must be between -1,000 and +18,000 meters inclusive).", response=None):
        super().__init__(message, response)


class InReachInvalidSpeedError(InReachClientError):
    def __init__(self, message="The location's speed is invalid (must be between 0 and 1,854km/h inclusive).", response=None):
        super().__init__(message, response)


class InReachInvalidCourseError(InReachClientError):
    def __init__(self, message="The location's course is invalid (must be between -360° and + 360° inclusive).", response=None):
        super().__init__(message, response)


class InReachInvalidPositionError(InReachClientError):
    def __init__(self, message="The location's position is invalid (latitude must be between -90° and +90°, longitude must be between -180° and +180°).", response=None):
        super().__init__(message, response)


class InReachInvalidIntervalError(InReachClientError):
    def __init__(self, message="The tracking interval is invalid (must be between between 30 and 65535 seconds).", response=None):
        super().__init__(message, response)


class InReachInvalidLocationTypeError(InReachClientError):
    def __init__(self, message="The location’s type is invalid. It must be 0 (reference point) or 1 (GPSlocation).", response=None):
        super().__init__(message, response)


class InReachInvalidLabelError(InReachClientError):
    def __init__(self, message="The location’s label is invalid (max len = 160 - message len, for reference points only).", response=None):
        super().__init__(message, response)


class InReachIllegalEmergencyActionError(InReachClientError):
    def __init__(self, message="The account’s emergencies are not handled by the account owner.", response=None):
        super().__init__(message, response)


class InReachInvalidBinaryTypeError(InReachClientError):
    def __init__(self, message="The binary type is invalid. It  must be 0 (Encrypted Binary), 1 (Generic Binary), or 2 (Encrypted Pinpoint).", response=None):
        super().__init__(message, response)


class InReachInvalidPayloadError(InReachClientError):
    def __init__(self, message="The payload is invalid. It must be base64 encoded and no greater than 268 bytes", response=None):
        super().__init__(message, response)


exceptions_by_inreach_code = {
    1: InReachInternalError,
    2: InReachTooManyRequestsError,
    3: InReachAuthenticationError,
    4: InReachUnknownDeviceError,
    5: InReachInvalidMessageError,
    6: InReachInvalidTimestampError,
    7: InReachInvalidSenderError,
    8: InReachInvalidAltitudeError,
    9: InReachInvalidSpeedError,
    10: InReachInvalidCourseError,
    11: InReachInvalidPositionError,
    12: InReachInvalidIntervalError,
    13: InReachInvalidLocationTypeError,
    14: InReachInvalidLabelError,
    15: InReachIllegalEmergencyActionError,
    16: InReachInvalidBinaryTypeError,
    17: InReachInvalidPayloadError,
}

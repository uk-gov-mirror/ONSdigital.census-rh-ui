class InactiveCaseError(Exception):
    """Raised when a user enters a used IAC code"""


class InvalidEqPayLoad(Exception):

    def __init__(self, message):
        super().__init__()
        self.message = message


class InvalidIACError(Exception):
    """Raised when the IAC Service returns a 404"""

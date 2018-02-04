"""
Exceptions.
"""


class AuthFailed(Exception):
    """
    Thrown when authorization to create/update a session fails.
    """
    pass


class DoesNotExist(Exception):
    """
    It doesn't exist.
    """
    pass


class BadInput(Exception):
    """
    Input format is bad.
    """
    pass


class InvalidAction(Exception):
    """
    The requested action can not be performed.
    """
    pass


class AlreadyExists(Exception):
    pass

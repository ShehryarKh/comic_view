"""
response module.
"""

from flask import make_response
import json


def error_response(code, message, description):
    """
    Helper to create an API error response.

    Params:
        code (int): The response's HTTP status code. Defaults to 200.
        message (string): The error message.
        description (string): The error description.

    Returns:
        (response): A flask response object.
    """
    dict = {'debug': message,
            'message': description
            }
    return json_response(status=code, data=dict)


def json_response(status=200, data=None, headers=None):
    """
    Helper to create an API response.

    Params:
        status (int, optional): The response's HTTP status code.
                                Defaults to 200.
        dict (dictionary, optional): The response body. Defaults to empty body.
        session (string, optional): The session identifier.
                                    Sets or deletes cookie.
        temp_session (bool, optional): Whether session should have a
                                       limited length.

    Returns:
        (response): A flask response object.
    """
    if data is not None:
        json_string = json.dumps(data,
                                 indent=2,
                                 default=lambda o: o.json_serialize())
    else:
        json_string = ''

    final_headers = {'Content-Type': 'application/json'}

    if headers:
        final_headers.update(headers)

    response = make_response(json_string, status, final_headers)
    return response

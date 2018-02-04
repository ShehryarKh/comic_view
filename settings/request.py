"""
requests module.
"""

import app

from flask import request
from werkzeug.exceptions import BadRequest, Unauthorized

import jwt
import jsonschema
from functools import wraps
import urllib
import json
import requests as url_request  # To avoid confusion with Flask's 'request'


def call(path, jwt, method='GET', data=None):
    root = request.url_root

    components = urllib.parse.urlparse(root)
    scheme = components.scheme
    hostname = components.hostname
    port = components.port

    if hostname == 'localhost':
        if path.startswith('auth'):
            port = 5000
        elif path.startswith('locations'):
            port = 5001
        elif path.startswith('things'):
            port = 5002
        elif path.startswith('accounts'):
            port = 5003

    # TODO Do this right
    url = scheme + '://' + hostname + ':' + str(port) + '/' + path
    # url = urllib.parse.urlunparse((scheme, hostname, str(port), path))
    headers = {'Authorization': 'Bearer ' + jwt,
               'Content-Type': 'application/json'}

    if method == 'GET':
        req = url_request.get(url, headers=headers)
    elif method == 'POST':
        json_body = json.dumps(data)
        req = url_request.post(url, headers=headers, data=json_body)

    response = req.json()
    return response

    # try:
    #     auth_request = urllib2.Request(url)
    #     auth_request.add_header('Session', session)
    #     auth_response = urllib2.urlopen(auth_request)
    #     headers = auth_response.info()
    #     header = headers.get('Authentication')
    #     token_type, encoded_jwt = header.split(' ', 1)
    #     assert encoded_jwt is not None
    #     assert token_type == 'Bearer'
    # except:
    #     raise Unauthorized('Malformed Authentication header')


def _validate(dict, schema):
    try:
        jsonschema.validate(dict, schema)
    except jsonschema.ValidationError as e:
        raise BadRequest(e.message)
    except Exception as e:  # Perhaps some other exception is thrown?
        raise BadRequest(str(e))


def json_body(schema):
    def json_body_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                json_body = request.get_json()
            except Exception:
                raise BadRequest('JSON body required.')

            _validate(json_body, schema)

            return f(*args, json=json_body, **kwargs)
        return wrapper
    return json_body_decorator


def query_params(schema):
    def query_params_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            query_params = request.args.to_dict()

            for key, value in query_params.items():
                # Because URL query params are always strings, we need to
                # convert paramters that are integers from string to integer
                # so validation against schema will pass.
                if value.isnumeric():
                    query_params[key] = int(value)

            _validate(query_params, schema)

            return f(*args, query_params=query_params, **kwargs)
        return wrapper
    return query_params_decorator


def role_required(required_roles):
    """
    Wrapper to extract entity ids from JWT.
    Used for all authenticated endpoints.
    """
    def authorization_required_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):

            encoded_jwt, decoded_token = get_token()

            try:
                jwt_roles = decoded_token['rol']
                account_id = decoded_token.get('acc')
                provider_id = decoded_token.get('pvd')
            except KeyError as e:
                raise Unauthorized('Missing JWT parameters ' + str(e))
            except Exception:
                raise Unauthorized('Error')

# https://stackoverflow.com/questions/3170055/test-if-lists-share-any-items-in-python
            if set(jwt_roles).isdisjoint(required_roles):
                raise Unauthorized('ACL Fail')

            return f(*args,
                     account_id=account_id,
                     provider_id=provider_id,
                     ** kwargs)

        return wrapper
    return authorization_required_decorator


# def admin_required(f):
#     @wraps(f)
#     def wrapper(*args, **kwargs):

#         encoded_jwt, decoded_token = get_token()
#         admin = decoded_token['admin']

#         if admin is not True:
#             raise Unauthorized

#         return f(*args,
#                  jwt=encoded_jwt,
#                  **kwargs)

#     return wrapper


# def verify(required_scope, jwt_scope):
#     required_dict = dict_representation(required_scope)
#     required_service = required_dict['service']
#     required_action = required_dict['action']

#     authorized = False

#     for item in jwt_scope:
#         dict = dict_representation(item)
#         service = dict['service']
#         action = dict['action']

#         service_match = (required_service == service or
#                          required_service == '*')

#         action_match = (required_action == action or
#                         required_action == '*')

#         if service_match and action_match:
#             authorized = True
#             break

#     if not authorized:
#         raise Unauthorized('ACL Fail')


def get_token():
    authorization_header = request.headers.get('Authorization')

    if authorization_header is None:
        raise Unauthorized('Missing Header')

    try:
        token_type, encoded_jwt = authorization_header.split(' ', 1)
        assert encoded_jwt is not None
        assert token_type == 'Bearer'
    except Exception:
        raise Unauthorized('Malformed Authorization header')

    try:
        algo = app.config['JWT_SERVICE_ALGO']
        secret_file = app.config['JWT_SERVICE_KEY_FILE']
        file_name = secret_file + '.public'
        file = open(file_name, 'r')
        secret = file.read()
        file.close()
    except Exception:
        raise Unauthorized('Bad signing info')

    try:
        decoded_token = jwt.decode(
            encoded_jwt,
            secret,
            algorithms=[algo],
            audience='zapi-rs',
            issuer='zapi-id'
        )
    except Exception:
        raise Unauthorized('JWT Bad')

    return encoded_jwt, decoded_token


import json
import jwt
import io

from datetime import datetime
from datetime import timedelta

global_password_hash = '$2b$12$eCc5pM5y.eOhNPandfz8GuQry6cYz6vJW.QjqUAgw0C7YdaqrYyzS'
global_account_id = 'f4f29c4f508aa8053788d57148140fe5b049ed900d01315eb04242c69517e370'
global_provider_id = '7148140fe5b049ed900d01315eb04242c69517e370f4f29c4f508aa8053788d5'


def create_authorization_token(test, dict_params, roles=[]):
    algo = test.zapi_service_app.config['JWT_SERVICE_ALGO']
    secret_file = test.zapi_service_app.config['JWT_SERVICE_KEY_FILE']
    file_name = secret_file + '.private'
    # TODO Do we want to hit the disk for every auth query?
    file = io.open(file_name, 'r', encoding='utf8')
    secret = file.read()
    file.close()

    token_valid_period = test.zapi_service_app.config['JWT_SERVICE_TTL']
    current_time = datetime.utcnow()
    date_until_valid = current_time + timedelta(seconds=token_valid_period)
    date_before_valid = current_time - timedelta(seconds=60)

    jwt_dict = {
        'iss': 'zapi-id',
        'ttl': token_valid_period,
        'exp': date_until_valid,
        'nbf': date_before_valid,
        'iat': current_time,
        'aud': ['zapi-rs'],
        'acc': dict_params.get('account_id'),
        'pvd': dict_params.get('provider_id'),
        'rol': roles
    }

    encoded_jwt = jwt.encode(jwt_dict, secret, algorithm=algo)
    return encoded_jwt.decode('utf-8')


def post(test, url, body, jwt=None, force_content_type=False):
    if body:
        data = json.dumps(body, indent=2)
    else:
        data = None

    if body or force_content_type:  # When testing empty body - force header
        headers = {'Content-Type': 'application/json'}
    else:
        headers = {}

    if jwt:
        headers['Authorization'] = 'Bearer ' + jwt

    response = test.app.post(url, data=data, headers=headers)
    return response


def put(test, url, body, jwt=None, force_content_type=False):
    if body:
        data = json.dumps(body, indent=2)
    else:
        data = None

    if body or force_content_type:  # When testing empty body - force header
        headers = {'Content-Type': 'application/json'}
    else:
        headers = {}

    if jwt:
        headers['Authorization'] = 'Bearer ' + jwt

    response = test.app.put(url, data=data, headers=headers)
    return response


def patch(test, url, body, jwt=None, force_content_type=False):
    if body:
        data = json.dumps(body, indent=2)
    else:
        data = None

    if body or force_content_type:  # When testing empty body - force header
        headers = {'Content-Type': 'application/json'}
    else:
        headers = {}

    if jwt:
        headers['Authorization'] = 'Bearer ' + jwt

    response = test.app.patch(url, data=data, headers=headers)
    return response


def get(test, url, jwt=None):
    headers = {}
    if jwt:
        headers.update({'Authorization': 'Bearer ' + jwt})

    response = test.app.get(url, headers=headers)
    return response


def delete(test, url, jwt=None):
    headers = {}
    if jwt:
        headers['Authorization'] = 'Bearer ' + jwt

    response = test.app.delete(url, headers=headers)
    return response


def assert_404(test, response):
    test.assertEqual(response.status_code, 404)

    response_body = json.loads(response.data)
    test.assertEqual(
        response_body,
        {'debug': 'Not Found',
         'message': 'The requested URL was not found on the server.  ' +
         'If you entered the URL manually please check your spelling and try again.'
         })


def assert_200(test, response, payload):
    test.assertEqual(response.status_code, 200)

    if payload is not None:
        response_body = json.loads(response.data)
        test.assertEqual(response_body, payload)
    else:
        test.assertEqual(len(response.data), 0)


def assert_201(test, response, payload):
    test.assertEqual(response.status_code, 201)

    if payload is not None:
        response_body = json.loads(response.data)
        test.assertEqual(response_body, payload)
    else:
        test.assertEqual(response.data, '')


def assert_400(test, response, description):
    test.assertEqual(response.status_code, 400)

    response_body = json.loads(response.data)
    test.assertEqual(response_body, {'debug': 'Bad Request',
                                     'message': description
                                     })


def assert_401(test, response, description='The credentials supplied do not allow access.'):
    test.assertEqual(response.status_code, 401)

    response_body = json.loads(response.data)
    test.assertEqual(response_body, {'debug': 'Unauthorized',
                                     'message': description
                                     })


def assert_403(test, response):
    test.assertEqual(response.status_code, 403)

    response_body = json.loads(response.data)
    test.assertEqual(response_body, {'debug': 'Forbidden',
                                     'message': "You don't have the permission to access the requested resource. " +
                                     "It is either read-protected or not readable by the server."
                                     })


def assert_405(test, response):
    test.assertEqual(response.status_code, 405)

    response_body = json.loads(response.data)
    test.assertEqual(
        response_body,
        {'debug': 'Method Not Allowed',
         'message': 'The method is not allowed for the requested URL.'
         })


def assert_406(test, response, description):
    test.assertEqual(response.status_code, 406)

    response_body = json.loads(response.data)
    test.assertEqual(
        response_body,
        {'debug': 'Not Acceptable',
         'message': description
         })


def assert_415(test, response):
    test.assertEqual(response.status_code, 415)

    response_body = json.loads(response.data)
    test.assertEqual(response_body, {'debug': 'Unsupported Media Type',
                                     'message': "Content-Type must be 'application/json'"
                                     })


def assert_409(test, response):
    test.assertEqual(response.status_code, 409)

    response_body = json.loads(response.data)
    test.assertEqual(response_body, {'debug': 'Conflict',
                                     'message': 'An account for that username already exists.'
                                     })


def assert_503(test, response):
    test.assertEqual(response.status_code, 503)

    response_body = json.loads(response.data)
    test.assertEqual(response_body, {'debug': 'Service Unavailable',
                                     'message': 'The server is temporarily unable to service your ' +
                                     'request due to maintenance downtime or capacity problems.  ' +
                                     'Please try again later.'
                                     })


# def assert_session_cookie(test, response, session_id=None, max_age=0):
#     cookie_string = response.headers['Set-Cookie']
#     cookie = SimpleCookie(cookie_string)
#     cookie_morsel = cookie['session']

#     if session_id:
#         test.assertEqual(cookie_morsel.value, session_id)

#     test.assertEqual(cookie_morsel['secure'], True)
#     test.assertEqual(cookie_morsel['httponly'], True)
#     test.assertEqual(cookie_morsel['max-age'], str(max_age))
#     test.assertEqual(cookie_morsel['path'], '/')


def assert_jwt(test, response, account_id, username):
    response_body = json.loads(response.data)
    encoded_jwt = response_body.get('id_token')
    algo = test.zeel_auth_app.config['JWT_ALGO']
    secret_file = test.zeel_auth_app.config['JWT_SECRET_FILE']
    file_name = secret_file + '.public'
    file = open(file_name, 'r')
    secret = file.read()
    file.close()

    try:
        decoded_token = jwt.decode(
            encoded_jwt,
            secret,
            algorithms=[algo],
            audience='zapi-rs',
            issuer='zapi-id'
        )
    except Exception as e:
        test.assertTrue(False, e)

# TODO Figure out testing timestamps
    # token_valid_period = 30
    # current_time = datetime.utcnow()
    # date_until_valid = current_time + timedelta(seconds=token_valid_period)
    # date_before_valid = current_time - timedelta(seconds=token_valid_period)

    # test.assertEqual(decoded_token.get('exp'), date_until_valid)
    # test.assertEqual(decoded_token.get('nbf'), date_before_valid)
    # test.assertEqual(decoded_token.get('iat'), current_time)

    test.assertEqual(decoded_token.get('iss'), 'zapi-id')
    test.assertEqual(decoded_token.get('aud'), ['zapi-rs'])

    payload = decoded_token.get('sub')
    test.assertEqual(payload, account_id)

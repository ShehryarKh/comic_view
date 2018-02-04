# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from database import db as db
from settings.base import Base

# Define a base model for other database tables to inherit


# Define a User model


class User(Base):

    # New instance instantiation procedure
    def __init__(self, dict):
        self.identity_id = dict.get('identity_id')
        self.username = dict.get('username')
        self.first_name = dict.get('first_name')
        self.last_name = dict.get('last_name')
        self.email = dict.get('email')
        self.phone_number = dict.get('phone_number')
        self.birth_date = dict.get('birth_date')
        self.gender = dict.get('gender')
        self.invite_code = dict.get('invite_code')
        self.session_id = dict.get('session_id')
        self.admin = dict.get('admin') or False
        self.temp_session = dict.get('temp_session') or False
        self.totp_secret = dict.get('totp_secret')


def schema(required_args=None):
    schema = {
        "type": "object",
        "properties": {
            "identity_id": {"type": "string", "minLength": 64, "maxLength": 64},
            "username": {"type": "string", "minLength": 1, "maxLength": 50},
            "password": {"type": "string", "minLength": 8},
            "new_password": {"type": "string", "minLength": 8},
            "totp_code": {"type": "string", "minLength": 6, "maxLength": 6},
            "token": {"type": "string", "minLength": 64, "maxLength": 64},
            "first_name": {"type": "string", "minLength": 1, "maxLength": 50},
            "last_name": {"type": "string", "minLength": 1, "maxLength": 50},
            "email": {"type": "string", "minLength": 1, "maxLength": 50},
            "phone_number": {"type": "string", "minLength": 1, "maxLength": 50},
            "birth_date": {"type": "string", "minLength": 10, "maxLength": 10},
            "gender": {"type": "string", "minLength": 1, "maxLength": 1},
            "invite_code": {"type": "string", "minLength": 1, "maxLength": 50},
        }
    }

    if required_args:
        schema['required'] = required_args

    return schema


def create_password_hash(password):
    bcrypt = Bcrypt(app)
    password_hash = bcrypt.generate_password_hash(password)

    return password_hash


def check_password(password, password_hash):
    bcrypt = Bcrypt(app)
    password_correct = bcrypt.check_password_hash(password_hash, password)

    return password_correct


def create_identity(username, password):
    """
    Creates an identity.
    Params:
        username (string): The desired username of the newly created identity.
        password (string): The desired password of the newly created identity.
    Returns:
        (identity): A newly created identity object.
    Raises:
        AlreadyExists - The username is already assigned to an identity.
    """
    from app.controllers.models import role
    from zapi_service.controllers.request import create_jwt

    bcrypt = Bcrypt(app)
    password_hash = bcrypt.generate_password_hash(password)

    identity_id = db.identifier()

    try:
        connection = db.connection()
        db.call(connection,
                'create_identity',
                [identity_id, username, password_hash])
    except DBItemAlreadyExistsException:
        raise AlreadyExists

    # # DO NOT commit db query yet. Let's see if account gets
    # # created sucessfully first.
    # Turns out I have to commit here or db transaction times out.

    db.commit(connection)
###########################################################
# If we are testing, stop here. This is somewhat of a problem
# because we're not testing account creation, but we don't
# want to have to run the accounts service to test.
    if app.config['TESTING'] is True:
        # db.commit(connection)
        identity = session.create(identity_id)
        return identity
###########################################################

    jwt_dict = {
        'idt': identity_id,
        'adm': False,
        'acc': '',
        'pvd': '',
        'rol': ['id_create']
    }

    encoded_jwt, token_valid_period = create_jwt(jwt_dict)
    data = {'name': username}
    try:
        response = zapi.request.call('accounts',
                                     encoded_jwt,
                                     method='POST',
                                     data=data)

        account_id = response['account_id']

        connection = db.connection()

        user_role = db.call(connection, 'role_for_user', None)
        user_role_id = user_role.get('role_id')

        parameters = {'account_id': account_id, 'role_id': user_role_id}

        role.add_to_identity(identity_id, parameters)
    except Exception:
        # If anything goes wrong with account creation
        # fail here with DB error.
        raise DBException

    # Commit now that we know account was created sucessfully.
    db.commit(connection)

    identity = session.create(identity_id)

    return identity


def create_session(params):
    """
    Creates a session. This is used to implement a 'login'.
    Params:
        username (string): The username of the identity which
        session is created for.
        password (string): The password of the identity which
        session is created for.
        totp (string, optional): The one-time TOTP code.
        Needed if two-factor is enable for the identity.
    Returns:
        (identity): A newly created identity object.
    Raises:
        None
    """
    username = params['username']
    password = params.get('password')
    totp = params.get('totp')
    admin_requested = params.get('admin') or False

    params = authenticate(username, password, totp)

    admin = params.get('admin') or False
    if admin_requested and admin is False:
        raise AuthFailed

    identity_id = params['identity_id']
    temp_session = params.get('temp_session') or False
    identity = session.create(identity_id,
                              temp_session=temp_session,
                              admin=admin_requested)
    return identity


def authenticate(username, password, totp=None):
    """
    Authenticates an identity's credentials.
    Params:
        username (string): The username of the identity to authenticate.
        password (string): The password of the identity to authenticate.
        totp (string, optional): The one-time TOTP code. Needed if
                                 two-factor is enable for the identity.
    Returns:
        (dictionary): Representation of an identity.
    Raises:
        AuthFailed - The credentials were incorrect.
    """
    result = _verify_identity(username, password)
    _check_totp(result, totp)

    if result['locked']:
        raise AuthFailed

    did_pass = result['did_pass']
    if did_pass is False:
        # Now, and only now, is it safe to reject based on wrong password.
        # Doing so earlier would leak information concerning the correctness
        # of the password guess.
        raise AuthFailed

    # By now we know identity has authenticated correctly.
    # Reset auth_attempt_count to 0.
    identity_id = result['identity_id']
    try:
        connection = db.connection()
        db.call(connection,
                'update_identity_reset_auth_count',
                [identity_id])
        db.commit(connection)
    except Exception:
        pass  # Not too concerned about a db error here.

    return result


def _check_totp(params, totp_code):
    """
    Verifies the TOTP code.
    Params:
        params (dictionary): A Represention of an identity.
                             Pulled straight from database.
        totp (string): The one-time TOTP code to be verified.
    Returns:
        None
    Raises:
        TOTPRequired - The identity requires two-factor and
        a TOTP code was not provided.
    """
    totp_secret = params['totp_secret']

    if totp_secret is not None:
        if totp_code is not None:
            verify_totp(totp_secret, totp_code)
        else:
            raise TOTPRequired


def _verify_identity(username, password):
    """
    Verifies the identity's username/password credentials.
    Params:
        username (string): The username of the identity to authenticate.
        password (string): The password of the identity to authenticate.
    Returns:
        (dictionary): Representation of an identity.
    Raises:
        AuthFailed - No identity exists for that username.
    """
    # Get the current bcrypt cost from config.
    current_cost = app.config['BCRYPT_LOG_ROUNDS']

    try:
        connection = db.connection()
        result = db.call(connection, 'fetch_identity_credentials', [username])
        password_hash = result['password_hash']
        identity_exists = True

        db.close(connection)

    except DBKeyDoesNotExistException:  # The username does not exist.
        # We could bail here, but not running the bcrypt
        # function will leak the presence/non-presense of identity
        # via timing attack.

        # Use this sample hash so we have something to feed into
        # bcrypt function. Make sure our bogus attempt uses the
        # same cost as a stored hashes.
        password_hash = (
            '$2b$' + str(current_cost) +
            # Rymths with assword
            '$eCc5pM5y.eOhNPandfz8GuQry6cYz6vJW.QjqUAgw0C7YdaqrYyzS')
        identity_exists = False
        # We don't want to abort here.
        pass  # We want to run the hash function to avoid timing attack.

    bcrypt = Bcrypt(app)
    did_pass = bcrypt.check_password_hash(password_hash, password)

    if identity_exists:
        # If identity and password is correct,
        # let's see if we should update the bcrypt cost.
        if did_pass:
            hash_array = password_hash.split('$')
            hash_cost = int(hash_array[2])  # The hash cost

            # If we have changed the bcrypt cost since this password
            # was created, let's update it with the new cost.
            if hash_cost != current_cost:
                identity_id = result['identity_id']
                bcrypt = Bcrypt(app)
                password_hash = bcrypt.generate_password_hash(password)

                connection = db.connection()
                db.call(connection,
                        'update_identity_password_hash',
                        [identity_id, password_hash])
                db.commit(connection)
        else:
            did_pass = _check_temp_password(result, password)
            result['temp_session'] = True
    else:
        # Now we can bail if no identity exists.
        raise AuthFailed

    result['did_pass'] = did_pass
    return result


def _check_temp_password(dict, password):
    """
    Verifies a secondary (temp) password for the identity.
    Params:
        dict (dictionary): A Represention of an identity.
        Pulled straight from database.
        password (string): The temp password of the identity to authenticate.
    Returns:
        None
    Raises:
        AuthFailed - Temp password has expired.
    """
    temp_password_hash = dict['temp_password_hash']

    if temp_password_hash:
        bcrypt = Bcrypt(app)
        did_pass = bcrypt.check_password_hash(temp_password_hash, password)

        if did_pass:
            username = dict['username']
            try:
                connection = db.connection()
                db.call(connection,
                        'delete_identity_temp_password',
                        [username])
                db.commit(connection)
            except Exception:
                pass  # Let's not let a db issue stop us from continuing here.

        return did_pass

    return False


def verify_totp(totp_secret, totp_code):
    """
    Verifies a TOTP code. Used when adding two-factor TOTP to an identity
    to insure identity has set their authenticator app up correctly.
    Params:
        totp_secret (string): A base32 encoded string of the TOTP secret.
        totp_code (string): A six digit numeric code generated by
        Authentictor app.
    Returns:
        None
    Raises:
        AuthFailed - The TOTP code did not match the calculated value.
    """
    totp = pyotp.TOTP(totp_secret)

    if totp.verify(totp_code) is False:
        raise AuthFailed


def identity_from_session_id(session_id):
    """
    Calls function on 'session' module which creates a identity
    object from a session_id.
    Params:
        session_id (string): A unique session id as defined in the database.
    Returns:
        An identity object.
    Raises:
        None
    """
    identity = session.identity_from_session_id(session_id)
    return identity

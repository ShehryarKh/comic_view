# Import flask dependencies
from flask import Blueprint, request, render_template, \
    flash, g, session, redirect, url_for, jsonify

# Import password / encryption helper tools
from werkzeug import check_password_hash, generate_password_hash

# Import the database object from the main app module
from database import db


# Import module models (i.e. User)
from app.mod_auth.user_model import User

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_auth = Blueprint('auth', __name__)


# Set the route and accepted methods


@mod_auth.route('/signup', methods=['POST'])
def signup():
    """
    POST /auth/identities - Create an identity.
    """
    username = json['username']
    password = json['password']

    identity = User.create_identity(username, password)
    roles = Role.fetch_for_identity(identity.identity_id)

    return json_response(status=201,
                         data=roles,
                         headers={'X-Session': identity.session_id})


@mod_auth.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Hello, World!'})

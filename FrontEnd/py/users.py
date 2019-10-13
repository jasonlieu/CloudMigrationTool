import sys
import flask_api
import pugsql
from flask import request, jsonify, Response
from flask_api import status, exceptions
from werkzeug.security import generate_password_hash, check_password_hash

app = flask_api.FlaskAPI(__name__)
app.config.from_envvar('APP_CONFIG')

queries = pugsql.module('queries/user')
queries.connect(app.config['DATABASE_URL'])

def validContentType(request, type='application/json'):
    if request.headers.has_key('Content-Type'):
        if request.headers['Content-Type'] == type:
            return True
    return { 'Error':'Unsupported Media Type', 'Support-Content-Type':type}, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

@app.route('/', methods=['GET'])
def home():
    return '''<h1>Cloue-Works-SERVICE</h1>'''


@app.route('/api/v1/cloud/users/register', methods=['POST', 'GET'])
def register():
    if request.method=='GET':
        all_users=queries.all_users()
        data = list(all_users)
        return data, status.HTTP_200_OK
    elif request.method=='POST':
        valid = validContentType(request)
        if valid is not True:
            return valid
        return create_user()

def create_user():
    user = request.data
    required_fields = ['uName','uUsername','uEmail','uPassword']
    if not all([field in user for field in required_fields]):
        raise exceptions.ParseError()
    try:
        user['uPassword'] = generate_password_hash(user['uPassword'])
        user['uID'] = queries.create_user(**user)
    except Exception as e:
        return { 'Error': str(e) }, status.HTTP_409_CONFLICT
    return user, status.HTTP_201_CREATED


@app.route('/api/v1/cloud/users/id/<int:id>', methods=['DELETE', 'GET'])
def user_id(id):
    if request.method=='GET':
        return get_user_by_id(id)
    elif request.method=='DELETE':
        return delete_user_by_id(id)
    
def get_user_by_id(id):
    try:
        user = queries.user_by_id(id=id)
        if user:
            return user, status.HTTP_200_OK
        else:
            raise exceptions.ParseError()
    except Exception as e:
        return { 'Error': str(e) }, status.HTTP_404_NOT_FOUND 

def delete_user_by_id(id):
    try:
        affected = queries.user_delete_by_id(id=id)
        if affected == 0:
            return { 'Error': "USER NOT FOUND" },status.HTTP_404_NOT_FOUND
        else:
            return { 'DELETE REQUEST ACCEPTED': str(id) }, status.HTTP_202_ACCEPTED               
    except Exception as e:
        return { 'Error': str(e) }, status.HTTP_409_CONFLICT 

@app.route('/api/v1/cloud/users/login', methods=['POST'])
def login():
    if request.method=='POST':
        valid = validContentType(request)
        if valid is not True:
            return valid
        return authenticate()
    
def authenticate():
    user = request.data
    required_fields = ['uEmail','uPassword']
    if not all([field in user for field in required_fields]):
        raise exceptions.ParseError()
    try:
        user2 = queries.authenticate_by_username(**user)
        if user2:
            if check_password_hash(user2['uPassword'],user['uPassword']):
                return user2, status.HTTP_200_OK
        return { 'Error': 'Login information invalid' }, status.HTTP_401_UNAUTHORIZED
    except Exception as e:
        return { 'Error': str(e) }, status.HTTP_409_CONFLICT


@app.route('/api/v1/cloud/users/<string:username>/password', methods=['PUT'])
def password(username):
    if request.method=='PUT':
        valid = validContentType(request)
        if valid is not True:
            return valid
        return update_password(username)

def update_password(username):
    user = request.data
    required_fields = ['uUsername','uPassword', 'userNewPassword']
    if not all([field in user for field in required_fields]):
        raise exceptions.ParseError()
    try:
        user2 = queries.authenticate_by_username(**user)
        if user2 and username==user2['uUsername']:
            if check_password_hash(user2['uPassword'],user['uPassword']):
                user['uPassword'] = generate_password_hash(user['userNewPassword'])
                affected = queries.user_update_password(**user)
                if affected == 0:
                    raise exceptions.ParseError('Update query failed')
                else:
                    user2['uPassword'] = user['uPassword']
                    return user2, status.HTTP_200_OK
        return { 'Error': 'Login information invalid' }, status.HTTP_401_UNAUTHORIZED
    except Exception as e:
        return { 'Error': str(e) }, status.HTTP_409_CONFLICT

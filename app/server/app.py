# System Imports
from flask import Flask, jsonify, make_response, request, render_template, session, redirect
import jwt
from datetime import datetime, timedelta
from functools import wraps
import requests
from flask_restplus import Api, Resource, fields

# Flask application object
app = Flask(__name__)

# Initialize Flask-RESTPlus API
api = Api(app, version='1.0', title='OpenSource API', description='An API to access an open-source API', doc='/swagger')

# Define a response model for the /auth route
response_model = api.model('AuthResponseModel', {
    'message': fields.String(description='A welcome message'),
    'data': fields.String(description='Data from the open-source API')
})

# SECRET KEY
app.config['SECRET_KEY'] = '0idVtXuqyZkhqp8YTw3'


# TOKEN_VALIDATION
def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return jsonify({'Alert!': 'Token is missing!'}), 401
        return func(*args, **kwargs)

    return decorated


# Session Validation
@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return 'logged in currently'


# Login Validation
@app.route('/login', methods=['POST'])
def login():
    if request.form['username'] == 'akash' and request.form['password'] == '123456':
        session['logged_in'] = True

        token = jwt.encode({
            'user': request.form['username'],
            'password': request.form['password'],
            'exp': datetime.now() + timedelta(seconds=60)  # Token expiration time
        },
            app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token})

    return make_response('Unable to verify', 403, {'WWW-Authenticate': 'Basic realm: "Authentication Failed "'})


# Authentication with Token
@app.route('/auth')
@token_required
@api.doc(responses={200: 'Success', 401: 'Unauthorized', 500: 'Internal Server Error'})
@api.marshal_with(response_model, envelope='response')
def auth():
    token = request.args.get('token')
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user = payload['user']

        # Make a request to the open-source API
        headers = {
            'X-CSCAPI-KEY': 'API_KEY'
        }
        response = requests.get("https://api.countrystatecity.in/v1/countries", headers=headers)

        if response.status_code == 200:
            data = response.json()
            return {
                'message': f'Welcome, {user} Data from the API:',
                'data': data
            }
        else:
            return 'Error accessing the API'

    except jwt.ExpiredSignatureError:
        return 'Token has expired, please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token, please log in again.'


# Additional Route for Open Data
@app.route('/open')
def openroute():
    return 'This is a Public or Open'


# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    session['logged_in'] = False
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)

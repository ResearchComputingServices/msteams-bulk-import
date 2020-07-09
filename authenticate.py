#!/usr/bin/env python3
"""Authenticate against Microsoft Graph API

This script forks a simple Flask webserver to perform an OAuth2 login
to the Microsoft Graph API.  It also opens a web browser tab to allow
the user to perform this authentication.

On successfully completing the login, the webserver caches user's
OAuth2 token to a file for use by command-line scripts.

This code is loosely based on Microsoft's Django sample app aviailable here:
   https://github.com/microsoftgraph/msgraph-training-pythondjangoapp/tree/master/demo

"""


# We run this flask server temporarily on localhost only.  If this
# code is ever modified to be deployed in production, set a secret SECRET_KEY!
SECRET_KEY = 'fdc68e02-5ff2-45ba-914e-89cb276af3ff'

import sys
import os
import pickle
import webbrowser
from multiprocessing import Process

import flask
import yaml
from requests_oauthlib import OAuth2Session

app = flask.Flask(__name__)

@app.route('/login')
def login():
    """View to initiate authentication"""
    aad_auth = OAuth2Session(settings['app_id'],
                             scope=settings['scopes'],
                             redirect_uri=settings['redirect'])
    sign_in_url, state = aad_auth.authorization_url(authorize_url, prompt='login')
    flask.session['auth_state'] = state
    return flask.redirect(sign_in_url)

@app.route('/tutorial/callback')
def finish_authorization():
    """View to obtain token after successful login

    The callback URL that routes to back to this view must be
    registered in the app's settings in Microsoft Azure, by a Windows
    admin with access to Azure.

    """
    aad_auth = OAuth2Session(settings['app_id'],
                             state=flask.session['auth_state'],
                             scope=settings['scopes'],
                             redirect_uri=settings['redirect'])
    token = aad_auth.fetch_token(token_url,
                                 client_secret = settings['app_secret'],
                                 authorization_response = flask.request.url)
    with open('credentials-cache.secret', 'wb') as F:
        pickle.dump(token, F)
    print()
    print("  **** Press ENTER to exit ***")
    print()
    return "Token has been cached to file.<p> You can close browser and stop web-app server now!"
    
    
if __name__ == '__main__':
    app.secret_key = SECRET_KEY

    # This is necessary for non-HTTPS localhost (testing/dev ONLY!)
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # This is necessary because Azure does not guarantee
    # to return scopes in the same case and order as requested
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    os.environ['OAUTHLIB_IGNORE_SCOPE_CHANGE'] = '1'

    # App secrets are storaged in a YAML file, which we load here
    with open('oauth_settings.yml', 'r') as F:
        settings = yaml.load(F, yaml.SafeLoader)
        authorize_url = '{0}{1}'.format(settings['authority'], settings['authorize_endpoint'])
        token_url = '{0}{1}'.format(settings['authority'], settings['token_endpoint'])

    # Run webserver as separate process, and start webbrowser
    #
    # This is an attempt to make it easier for the end user!
    #
    webserver = Process(target=lambda: app.run(port=8000))
    webserver.start()
    webbrowser.open('http://localhost:8000/login', new=2)
    input("Press ENTER to stop webserver...")
    webserver.terminate()
    webserver.join()
    

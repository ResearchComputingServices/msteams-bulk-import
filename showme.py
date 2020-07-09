#!/usr/bin/env python3
"""Basic Graph API test: show info about logged in user"""

import pickle
from requests_oauthlib import OAuth2Session

GRAPH_URL = 'https://graph.microsoft.com/beta'

def get_user(token):
  graph_client = OAuth2Session(token=token)
  # Send GET to /me
  user = graph_client.get('{0}/me'.format(graph_url))
  # Return the JSON result
  return user.json()

with open('credentials-cache.secret', 'rb') as F:
    token = pickle.load(F)

graph_client = OAuth2Session(token=token)
user = graph_client.get(f'{GRAPH_URL}/me').json()

print(f"FULLNAME: {user['displayName']}")
print(f"USERNAME: {user['userPrincipalName']}")
print(f"EMAIL:    {user['mail']}")

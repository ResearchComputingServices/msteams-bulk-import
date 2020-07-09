This code is based on a quick one-off script to bulk import members
into Microsoft Teams private channels using the Microsoft Graph API.

It uses a minimal Flask web interface for authentication, in order to
obtain and cache the OAuth2 token.  Then CLI scripts can use the cached
token to list information about MS Teams and to add members to private
channels.

To setup on Linux (steps should be similar on Mac or Windows):

 1. virtualenv -p python3 env
 2. source env/bin/activate
 3. pip install -r requirements.txt
 4. Register the app with MS Azure and create config file oauth_settings.yml
     1. Look at this link for guidance: https://github.com/microsoftgraph/msgraph-training-pythondjangoapp/tree/master/demo)
 5. ./authenticate
     1. Use browser to login
     2. After login, close browser and press ENTER to quit script
 6. Use ./teams command to view info and add members
 

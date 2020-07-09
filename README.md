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
 4. ./authenticate
     1. Use browser to login
     2. After login, close browser and press ENTER to quit script
 5. Use ./teams command to view info and add members
 

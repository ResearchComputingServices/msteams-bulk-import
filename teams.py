#!/usr/bin/env python3
"""Add members to MS Teams private channels and perform misc Teams queries

The first argument to this script is a command to be run.  Following
arguments are passed to the command.  Available commands are:

teams.py list_teams
  - List all teams for which logged in user is a member

teams.py list_members <TEAM_NAME>
  - List all members joined to the Team specified by TEAM_NAME

teams.py list_channels <TEAM_NAME>
  - List all channels in the Team specified by TEAM_NAME

teams.py list_channel_members <TEAM_NAME> <CHANNEL_NAME>
  - List all channel members of channel CHANNEL_NAME in the Team
    specified by TEAM_NAME
  - If CHANNEL_NAME is not a private team, then all Team members are
    implicitly part of the channel

teams.py add_channel_members <CSV_FILE>
  - Add members to channels specified in CSV file.
  - CSV file format is:
      Team,Channel,Member
      <team name 1>,<chanel name 1>,<team member email 1>
      <team name 2>,<chanel name 2>,<team member email 2>
      <team name 3>,<chanel name 3>,<team member email 3>

"""

import pickle
import sys
import os

import pandas as pd
from requests_oauthlib import OAuth2Session

GRAPH_URL = 'https://graph.microsoft.com/beta'

def api_get(token, query):
  """Wrapper for GET requests to MS Graph REST API

  As a simple performance hack, this function memoizes results of
  previous queries.

  """
  if query not in api_get.query_cache:
    graph_client = OAuth2Session(token=token)
    response = graph_client.get(GRAPH_URL+query)
    if not response.ok:
      sys.exit(f"ERROR in API query {query}:  {response.reason}")
    result = response.json()['value']
    api_get.query_cache[query] = result
  return api_get.query_cache[query]
api_get.query_cache = {}

def api_list_my_teams(token):
  return pd.DataFrame(api_get(token, '/me/joinedTeams'))

def api_get_team_members(token, team_id):
  return pd.DataFrame(api_get(token, f"/groups/{team_id}/members"))

def api_get_team_channels(token, team_id):
  return pd.DataFrame(api_get(token, f"/teams/{team_id}/channels"))

def api_get_channel_members(token, team_id, channel_id):
  return pd.DataFrame(api_get(token, f"/teams/{team_id}/channels/{channel_id}/members"))

def api_add_channel_member(token, team_id, channel_id, user_id):
  graph_client = OAuth2Session(token=token)
  request_url = f'{GRAPH_URL}/teams/{team_id}/channels/{channel_id}/members'
  user_url = f"{GRAPH_URL}/users('{user_id}')"
  response = graph_client.post(
    request_url,
    json={
      "@odata.type": "#microsoft.graph.AadUserConversationMember",
      "roles": "",
      "user@odata.bind": user_url
    }
  )
  return response.json()


def find_team_id(team_name):
  """Map from Team's name to API's internal team ID"""
  team_list = api_list_my_teams(token)
  matches = team_list.loc[team_list['displayName'] == team_name]
  if len(matches) > 0:
    return matches['id'].iloc[0]
  sys.exit(f"ERROR: cannot find team {team_name}")


def find_channel_id(team_id, channel_name):
  """Map from Team Channel's name to API's internal channel ID"""
  channel_list = api_get_team_channels(token, team_id)
  matches = channel_list.loc[channel_list['displayName'] == channel_name]
  if len(matches) > 0:
    return matches['id'].iloc[0]
  sys.exit(f"ERROR: cannot find channel {channel_name}")


def cmd_list_teams(args):
  team_list = api_list_my_teams(token)
  print(team_list[['displayName']].to_csv())


def cmd_list_members(args):
  if len(args) < 1:
    sys.exit("ERROR: needs 1 cmd-line arg: team_name")
  team_id = find_team_id(args[0])
  member_list = api_get_team_members(token, team_id)
  member_list = member_list[['mail', 'displayName', 'userType']]
  print(member_list.to_csv())


def cmd_list_channels(args):
  if len(args) < 1:
    sys.exit("ERROR: needs 1 cmd-line arg: team_name")
  team_id = find_team_id(args[0])
  channel_list = api_get_team_channels(token, team_id)
  channel_list = channel_list[['displayName', 'membershipType']]
  print(channel_list.to_csv())


def cmd_list_channel_members(args):
  if len(args) < 2:
    sys.exit("ERROR: needs 2 cmd-line args: team_name channel_name")
  team_id = find_team_id(args[0])
  channel_id = find_channel_id(team_id, args[1])
  member_list = api_get_channel_members(token, team_id, channel_id)
  member_list = member_list[['displayName', 'email']]
  print(member_list.to_csv())


def member_can_be_added(row):
  """Predicate used to filter out CSV file rows that we can't or don't need to add"""
  channel_name = row['Channel']
  team_name = row['Team']
  member_email = row['Member'].lower()
  team_id = find_team_id(team_name)
  channel_id = find_channel_id(team_id, channel_name)
  
  # Member must already be in Team before we try to add to channel
  team_member_list = api_get_team_members(token, team_id)
  if not team_member_list['mail'].str.lower().isin([member_email]).any():
    return False

  # Check whether member already exists in channel
  channel_member_list = api_get_channel_members(token, team_id, channel_id)
  return not member_email in channel_member_list['email'].str.lower().values
  

def cmd_add_channel_members(args):
  """
  first item in args is a filename of a CSV file with this format:

  Team,Channel,Member
  <team name 1>,<chanel name 1>,<team member email 1>
  <team name 2>,<chanel name 2>,<team member email 2>
  <team name 3>,<chanel name 3>,<team member email 3>
  """
  # Process cmd-line arguments
  if len(args) < 1:
    sys.exit("ERROR: needs 1 cmd-line arg: csv_file")
  csv_file = args[0]
  if not os.path.isfile(csv_file):
    sys.exit(f"ERROR: File '{csv_file}' does not exist")

  # Filter out members that already exist in specified channels
  file_data = pd.read_csv(csv_file)
  rows_to_add = file_data[file_data.apply(member_can_be_added, axis=1)]

  # Add members (only ones we determined should be added)
  for _, row in rows_to_add.iterrows():
    channel_name = row['Channel']
    team_name = row['Team']
    member_email = row['Member'].lower()
    team_id = find_team_id(team_name)
    channel_id = find_channel_id(team_id, channel_name)

    # Find ID for member that we are adding to this private channel
    team_member_list = api_get_team_members(token, team_id)
    member_matches = team_member_list['mail'].str.lower().isin([member_email])
    user_id = team_member_list['id'][member_matches.idxmax()]

    # Perform API request to add member to private channel
    response = api_add_channel_member(token, team_id, channel_id, user_id)
    print(f"Added user {member_email} to channel {channel_name}")
  
  
if __name__ == '__main__':
  # Load token saved using authentication.py
  with open('credentials-cache.secret', 'rb') as F:
      token = pickle.load(F)

  # Parse command-line arguments
  if len(sys.argv)<2:
    print(__doc__)
    sys.exit(0)
  cmd = sys.argv[1]
  args = sys.argv[2:]

  # Run command. User specified commands correspond to functions
  # prefixed with 'cmd_'.  This makes it easy to add new commands,
  # although admittedly a quick hack...
  try:
    f = globals()["cmd_"+cmd]
  except KeyError:
    sys.exit(f"COMMAND '{cmd}' not implemented")
  f(args)

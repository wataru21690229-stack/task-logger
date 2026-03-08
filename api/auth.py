import os
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/spreadsheets'
]

def authenticate_google():
    """Shows basic usage of the Tasks and Sheets API.
    Prints the user's tasks and spreadsheets.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                 st.error("credentials.json が見つかりません。Google Cloud Consoleからダウンロードしてこのフォルダに配置してください。")
                 return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def get_auth_status():
    if os.path.exists('token.json'):
       try:
           creds = Credentials.from_authorized_user_file('token.json', SCOPES)
           if creds and creds.valid:
               return True
           elif creds and creds.expired and creds.refresh_token:
               creds.refresh(Request())
               with open('token.json', 'w') as token:
                   token.write(creds.to_json())
               return True
       except Exception as e:
           pass
    return False

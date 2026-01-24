import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

class GoogleAuth:
    def __init__(self):
        self.creds = None
        self.gc = None

    def authenticate(self):
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                creds_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'credentials.json')
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        self.gc = gspread.authorize(self.creds)
        return self.gc

    def delete_old_spreadsheets(self, days_old=30):
        import datetime
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days_old)
        files = self.gc.list_spreadsheet_files()
        for file in files:
            created_time = file.get('createdTime')
            if created_time and datetime.datetime.fromisoformat(created_time[:-1]) < cutoff:
                self.gc.del_spreadsheet(file['id'])
                print(f"Удалена таблица: {file['name']}")
            elif not created_time:  # Если нет даты, удалить все подозрительные
                self.gc.del_spreadsheet(file['id'])
                print(f"Удалена таблица без даты: {file['name']}")

    def delete_all_spreadsheets(self):
        files = self.gc.list_spreadsheet_files()
        for file in files:
            self.gc.del_spreadsheet(file['id'])
            print(f"Удалена таблица: {file['name']}")


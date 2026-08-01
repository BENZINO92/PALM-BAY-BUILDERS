"""Google Sheets integration - Upload scraped builder data"""

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from typing import List, Dict
import os
import json

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

class GoogleSheetsUploader:
    def __init__(self, credentials_file='credentials.json'):
        """Initialize Google Sheets API client"""
        self.credentials_file = credentials_file
        self.service = None
        self.spreadsheet_id = None
        self.authenticate()

    def authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            creds = None

            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)

                with open('token.json', 'w') as token:
                    token.write(creds.to_json())

            self.service = build('sheets', 'v4', credentials=creds)
            print("✅ Google Sheets authenticated successfully")

        except Exception as e:
            print(f"❌ Google Sheets authentication failed: {e}")
            print("   Make sure credentials.json is in the folder")

    def create_or_update_sheet(self, sheet_name: str) -> str:
        """Create new spreadsheet or update existing"""
        try:
            today = datetime.now().strftime('%B %d, %Y')
            title = f"TODAYS BUILDERS PERMIT LIST - {today}"

            spreadsheet = {
                'properties': {
                    'title': title
                }
            }

            spreadsheet = self.service.spreadsheets().create(body=spreadsheet).execute()
            spreadsheet_id = spreadsheet.get('spreadsheetId')

            print(f"✅ Created Google Sheet: {title}")
            print(f"   Spreadsheet ID: {spreadsheet_id}")

            return spreadsheet_id

        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return None

    def upload_builders_data(self, builders_data: List[Dict]) -> bool:
        """Upload builder data to Google Sheet"""
        try:
            if not self.service:
                print("❌ Google Sheets not authenticated")
                return False

            spreadsheet_id = self.create_or_update_sheet("builders")
            if not spreadsheet_id:
                return False

            today = datetime.now().strftime('%B %d, %Y')

            values = [
                ["BUILDERS PERMIT LIST"],
                [f"Date Pulled: {today}"],
                ["IMPACT FEES RESIDENTIAL - Palm Bay, FL"],
                [],
                ["Builder Name", "Property Address", "Zipcode", "Lot Size", "Application Type", "Date Filed"],
            ]

            for builder in builders_data:
                permit = builder.get('permits', [{}])[0] if builder.get('permits') else {}

                values.append([
                    builder.get('name', ''),
                    permit.get('property_address', ''),
                    permit.get('zipcode', ''),
                    permit.get('lot_size', ''),
                    permit.get('application_type', ''),
                    permit.get('date_issued', '')
                ])

            self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range='Sheet1'
            ).execute()

            body = {
                'values': values
            }

            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A1',
                valueInputOption='RAW',
                body=body
            ).execute()

            self._format_sheet(spreadsheet_id)

            print(f"✅ Uploaded {len(builders_data)} builders to Google Sheet")
            print(f"📊 Sheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

            return True

        except Exception as e:
            print(f"❌ Error uploading to Google Sheets: {e}")
            return False

    def _format_sheet(self, spreadsheet_id: str):
        """Format the spreadsheet (colors, bold, etc.)"""
        try:
            requests = [
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': 0,
                            'startRowIndex': 4,
                            'endRowIndex': 5,
                            'startColumnIndex': 0,
                            'endColumnIndex': 6
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {'bold': True},
                                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.86}
                            }
                        },
                        'fields': 'userEnteredFormat'
                    }
                },
                {
                    'autoResizeDimensions': {
                        'dimensions': {
                            'sheetId': 0,
                            'dimension': 'COLUMNS',
                            'startIndex': 0,
                            'endIndex': 6
                        }
                    }
                }
            ]

            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()

        except Exception as e:
            print(f"⚠️  Could not format sheet: {e}")


def upload_to_google_sheets(builders_data: List[Dict]) -> bool:
    """Main function to upload data to Google Sheets"""
    uploader = GoogleSheetsUploader()
    return uploader.upload_builders_data(builders_data)

from __future__ import annotations

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from tools.google_oauth import google_credentials_path, google_token_path, get_google_credentials


def google_auth_status() -> tuple[bool, str]:
    cred_path = google_credentials_path()
    token_path = google_token_path()
    if not cred_path.is_file():
        return False, f"Missing OAuth client JSON: {cred_path}"
    if not token_path.is_file():
        return False, f"OAuth client JSON found, but token is missing: {token_path}"
    try:
        creds = Credentials.from_authorized_user_file(str(token_path))
    except Exception as error:
        return False, f"Token file exists but could not be read: {error}"
    if creds.expired:
        return True, f"Google auth configured, but token is expired: {token_path}"
    return True, f"Google auth configured: credentials={cred_path} token={token_path}"


def google_auth_test() -> tuple[bool, str]:
    try:
        creds = get_google_credentials()
        gmail = build("gmail", "v1", credentials=creds, cache_discovery=False)
        profile = gmail.users().getProfile(userId="me").execute()
        calendar = build("calendar", "v3", credentials=creds, cache_discovery=False)
        calendars = calendar.calendarList().list(maxResults=1).execute()
    except Exception as error:
        return False, f"Google auth test failed: {error}"
    address = profile.get("emailAddress", "(unknown)")
    total = len(calendars.get("items") or [])
    return True, f"Google auth ok: gmail={address} visible_calendars>={total}"

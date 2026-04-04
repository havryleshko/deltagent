from __future__ import annotations

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

_SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
)


def google_credentials_path() -> Path:
    return Path(os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")).expanduser()


def google_token_path() -> Path:
    return Path(os.environ.get("GOOGLE_TOKEN_PATH", "token.json")).expanduser()


def get_google_credentials() -> Credentials:
    cred_file = google_credentials_path()
    if not cred_file.is_file():
        raise FileNotFoundError(f"Missing OAuth client secrets: {cred_file}")
    tok_file = google_token_path()
    creds: Credentials | None = None
    if tok_file.is_file():
        creds = Credentials.from_authorized_user_file(str(tok_file), scopes=list(_SCOPES))
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(cred_file), scopes=list(_SCOPES)
            )
            creds = flow.run_local_server(port=0)
        tok_file.parent.mkdir(parents=True, exist_ok=True)
        tok_file.write_text(creds.to_json(), encoding="utf-8")
    return creds

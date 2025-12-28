from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import base64
import os
import sys
import shutil


def get_resource_path(relative_path):
    """Get absolute path to bundled resource (works for dev and PyInstaller)"""
    try:
        # PyInstaller extracts files to a temp folder
        base_path = sys._MEIPASS
    except AttributeError:
        # Normal Python script
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_data_path(filename=""):
    """Return a writable path for storing user data."""

    applicationName = "TrajectTower"

    if sys.platform == "win32":
        base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), applicationName)
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support/" + applicationName)
    else:
        base = os.path.expanduser("~/.local/share/" + applicationName)

    os.makedirs(base, exist_ok=True)
    return os.path.join(base, filename)


def get_copied_data_file_path(filename):
    """
    If the file doesn't exist in the user's data folder, copy it from bundled resources.
    Returns the full path to the writable file.
    """
    user_file_path = get_data_path(filename)

    if not os.path.exists(user_file_path):
        # Ensure all parent directories exist
        os.makedirs(os.path.dirname(user_file_path), exist_ok=True)
        
        bundled_file_path = get_resource_path(filename)
        if os.path.exists(bundled_file_path):
            shutil.copy(bundled_file_path, user_file_path)

    # Optional: validate file
    if not is_valid_data_file_path(filename):
        raise IOError(f"Cannot access or write to {user_file_path}")

    return user_file_path

def is_valid_data_file_path(filename):
    """
    Check if a file is a valid data file.
    Returns True if the file exists and is writable, False otherwise.
    """
    path = get_data_path(filename)
    return os.path.isfile(path) and os.access(path, os.W_OK)

def checkGmailConnection():
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    TOKEN_FILE =  get_data_path("data/gmail/token.json")

    creds = None

    # Load existing token if it exists
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no credentials or invalid and cannot refresh, return False
    if not creds:
        return False

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            print(f"Failed to refresh token: {e}")
            return False
    elif creds.expired:
        # Token expired and no refresh token
        return False

    try:
        # Build the Gmail service
        service = build("gmail", "v1", credentials=creds)
        # Test connection by listing labels
        labels = service.users().labels().list(userId="me").execute()
        return "labels" in labels
    except Exception as e:
        print(f"Error connecting to Gmail: {e}")
        return False


def setupGmailConnection():
    """
    Ensures Gmail OAuth connection exists and is valid.
    Creates/refreshes token.json if needed.
    Returns True if connection is successful, False otherwise.
    """

    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    TOKEN_FILE =  get_data_path("data/gmail/token.json")
    CRED_FILE = get_copied_data_file_path("data/gmail/credentials.json")

    creds = None

    try:
        # Load existing token if present
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        # Refresh or create credentials if needed
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CRED_FILE,
                    SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save updated token
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        # Build service and make a lightweight test call
        service = build("gmail", "v1", credentials=creds)
        service.users().labels().list(userId="me").execute()

        return True

    except Exception as e:
        print(f"Gmail connection failed: {e}")
        return False

def getGmailService():
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    TOKEN_FILE =  get_data_path("data/gmail/token.json")

    if not os.path.exists(TOKEN_FILE):
        raise Exception("Gmail not connected. Run setupGmailConnection first.")

    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    return build("gmail", "v1", credentials=creds)

def getGmailEmails():
    emails = []

    LABEL_NAMES = ["Internship-Rejected", "Internship-Interview"]

    # Ensure Gmail is connected
    if not setupGmailConnection():
        raise Exception("Gmail connection failed")

    service = getGmailService()

    # ---------------------
    # Helpers
    # ---------------------
    def decode(data):
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    def get_header(headers, name):
        for h in headers:
            if h["name"].lower() == name.lower():
                return h["value"]
        return None

    def get_body(payload):
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain" and "data" in part["body"]:
                    return decode(part["body"]["data"])
        if "data" in payload.get("body", {}):
            return decode(payload["body"]["data"])
        return ""

    # ---------------------
    # Find label IDs
    # ---------------------
    all_labels = service.users().labels().list(userId="me").execute()["labels"]

    label_id_map = {}
    for name in LABEL_NAMES:
        lid = next((l["id"] for l in all_labels if l["name"] == name), None)
        if lid:
            label_id_map[name] = lid
        else:
            print(f"Warning: Label '{name}' not found")

    if not label_id_map:
        raise Exception("No valid labels found")

    # ---------------------
    # Fetch messages
    # ---------------------
    seen_ids = set()

    for label_name, label_id in label_id_map.items():
        page_token = None

        while True:
            response = service.users().messages().list(
                userId="me",
                labelIds=[label_id],
                maxResults=500,
                pageToken=page_token
            ).execute()

            for msg in response.get("messages", []):
                if msg["id"] in seen_ids:
                    continue
                seen_ids.add(msg["id"])

                message = service.users().messages().get(
                    userId="me",
                    id=msg["id"],
                    format="full"
                ).execute()

                headers = message["payload"]["headers"]

                email_type = (
                    "Rejected" if label_name == "Internship-Rejected"
                    else "Interview"
                )

                emails.append({
                    "id": msg["id"],
                    "from": get_header(headers, "From"),
                    "to": get_header(headers, "To"),
                    "subject": get_header(headers, "Subject"),
                    "date": get_header(headers, "Date"),
                    "body": get_body(message["payload"]),
                    "type": email_type
                })

            page_token = response.get("nextPageToken")
            if not page_token:
                break

    return emails

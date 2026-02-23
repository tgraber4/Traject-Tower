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


def is_valid_data_file_path(filename):
    """
    Check if a file is a valid data file.
    Returns True if the file exists and is writable, False otherwise.
    """
    path = get_data_path(filename)
    return os.path.isfile(path) and os.access(path, os.W_OK)

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


def isExeEnv():
    return getattr(sys, "frozen", False)

def get_browsers_path():
    """
    Return a persistent folder path for Playwright browsers.
    Works in dev and PyInstaller onefile builds.
    """
    applicationName = "TrajectTower"

    if isExeEnv():
        # Running inside PyInstaller onefile or onedir exe
        # Persistent folder outside the temp _MEIxxxx folder
        if sys.platform == "win32":
            path = os.path.join(
                os.environ["LOCALAPPDATA"],
                applicationName,
                "ms-playwright"
            )
        elif sys.platform == "darwin":
            path = os.path.expanduser(
                f"~/Library/Caches/{applicationName}/ms-playwright"
            )
        else:
            path = os.path.expanduser(
                f"~/.cache/{applicationName}/ms-playwright"
            )
    else:
        # Dev / venv environment
        # Use default Playwright cache (no app name)
        if sys.platform == "win32":
            path = os.path.join(
                os.environ["LOCALAPPDATA"],
                "ms-playwright"
            )
        elif sys.platform == "darwin":
            path = os.path.expanduser(
                "~/Library/Caches/ms-playwright"
            )
        else:
            path = os.path.expanduser(
                "~/.cache/ms-playwright"
            )


    os.makedirs(path, exist_ok=True)
    return path

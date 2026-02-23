import os
import sys
import subprocess
from tkinter import messagebox

def isExeEnv():
    return getattr(sys, "frozen", False)

def getOS():
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    else:
        return "linux"

def getPermantStoragePath():
    if not isExeEnv():
        if getOS() == "windows":
            path = os.path.join(os.environ["LOCALAPPDATA"], "TrajectTower")
        elif getOS() == "macos":
            path = os.path.expanduser("~/Library/Caches/TrajectTower")
        else:
            path = os.path.expanduser("~/.cache/TrajectTower")
    
    os.makedirs(path, exist_ok=True)
    return path

def get_browsers_path():
    """
    Return a persistent folder path for Playwright browsers.
    Works in dev and PyInstaller onefile builds.
    """
    path = os.path.join(getPermantStoragePath(), "ms-playwright")

    os.makedirs(path, exist_ok=True)
    return path



if __name__ == "__main__":
    print(get_browsers_path())
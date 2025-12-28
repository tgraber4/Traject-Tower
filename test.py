import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox



def get_resource_path(relative_path):
    """Get absolute path to bundled resource (works for dev and PyInstaller)"""
    try:
        # PyInstaller extracts files to a temp folder
        base_path = sys._MEIPASS
    except AttributeError:
        # Normal Python script
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def isExeEnv():
    return getattr(sys, "frozen", False)

def get_browsers_path():
    """
    Return a persistent folder path for Playwright browsers.
    Works in dev and PyInstaller onefile builds.
    """
    if isExeEnv():
        # Running inside PyInstaller onefile or onedir exe
        # Persistent folder outside the temp _MEIxxxx folder
        if sys.platform == "win32":
            path = os.path.join(os.environ["LOCALAPPDATA"], "TrajectTower", "ms-playwright")
        elif sys.platform == "darwin":
            path = os.path.expanduser("~/Library/Caches/TrajectTower/ms-playwright")
        else:
            path = os.path.expanduser("~/.cache/TrajectTower/ms-playwright")
    else:
        # Dev / venv environment
        # Use default Playwright cache or a subfolder in the project
        if sys.platform == "win32":
            path = os.path.join(os.environ["LOCALAPPDATA"], "ms-playwright")
        elif sys.platform == "darwin":
            path = os.path.expanduser("~/Library/Caches/ms-playwright")
        else:
            path = os.path.expanduser("~/.cache/ms-playwright")

    os.makedirs(path, exist_ok=True)
    return path

def is_playwright_setup_needed():
    """Return True if browsers folder is missing or empty."""
    path = get_browsers_path()
    return not os.listdir(path)

def install_playwright_browsers():
    """Force install Chromium, Firefox, WebKit to persistent folder."""
    path = get_browsers_path()
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = path

    # Use system Python to avoid PyInstaller onefile temp folder issues
    if isExeEnv():
        # Running as PyInstaller EXE → use system Python
        python_exe = "C:\Users\12173\Desktop\VS Code 2\Python\Small Projects\TrajectTower\venv\Scripts\python.exe"
    else:
        # Dev / venv
        python_exe = sys.executable

    try:
        subprocess.run(
            [python_exe, "-m", "playwright", "install", "--force"],
            check=True
        )
        messagebox.showinfo("Success", f"Playwright browsers installed successfully!\nFolder: {path}")
    except subprocess.CalledProcessError:
        messagebox.showerror("Error", "Failed to install Playwright browsers.\nCheck your internet connection.")

class Setup:
    def __init__(self, root, launch_main_app_callback):
        self.root = root
        self.launch_main_app_callback = launch_main_app_callback
        self.root.title("TrajectTower Playwright Setup")
        self.root.geometry("450x250")
        self.root.resizable(False, False)

        self.browsers_path = get_browsers_path()
        print(self.browsers_path)
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = self.browsers_path

        label = tk.Label(
            self.root,
            text="This setup will check if Playwright browsers are installed.\n"
                 "Internet is required to download them if missing.",
            wraplength=420,
            justify="center"
        )
        label.pack(pady=20)

        tk.Button(self.root, text="Check / Install Playwright", command=self.check_playwright).pack(pady=10)
        tk.Button(self.root, text="Test Browser Launch", command=self.launch_browser_test).pack(pady=10)
        tk.Button(self.root, text="Finish Setup", command=self.finish_setup).pack(pady=10)

    def check_playwright(self):
        if is_playwright_setup_needed():
            result = messagebox.askyesno(
                "Playwright Setup",
                "Playwright browsers are missing or incomplete.\n"
                "Internet is required to download them.\nDo you want to install now?"
            )
            if result:
                install_playwright_browsers()
        else:
            messagebox.showinfo("Playwright Setup", f"Browsers already installed at:\n{self.browsers_path}")

    def launch_browser_test(self):
        try:
            # Import here to ensure PLAYWRIGHT_BROWSERS_PATH is set
            os.environ["DEBUG"] = "pw:browser*"
            from playwright.sync_api import sync_playwright, Error
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = self.browsers_path

            print("PLAYWRIGHT_BROWSERS_PATH =", os.environ.get("PLAYWRIGHT_BROWSERS_PATH"))

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
            messagebox.showinfo("Test Success", "Chromium launched successfully!")
        except Exception as e:
            messagebox.showerror("Playwright Error", f"Failed to launch browser:\n{e}")

    def finish_setup(self):
        self.root.destroy()
        if callable(self.launch_main_app_callback):
            self.launch_main_app_callback()

# Example usage
def launch_job_tracker_app():
    print("job")


if __name__ == "__main__":
    if is_playwright_setup_needed():
        root = tk.Tk()
        setup_app = Setup(root, launch_job_tracker_app)
        root.mainloop()
    else:
        print("job")
        root = tk.Tk()
        setup_app = Setup(root, launch_job_tracker_app)
        root.mainloop()


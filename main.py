import tkinter as tk
from tkinter import messagebox
import os
from app.paths import get_browsers_path
from app.Windows.job_tracker_app import JobTrackerApp

def is_playwright_setup_needed():
    """Return True if browsers folder is missing or empty."""
    path = get_browsers_path()
    if not os.path.exists(path):
        return True
    return not os.listdir(path)


def launch_job_tracker_app():
    root = tk.Tk()
    app = JobTrackerApp(root) 
    root.mainloop()


if __name__ == "__main__":
    if is_playwright_setup_needed():
        messagebox.showerror("Playwright Error", "Playwright setup needed. Follow instructions on Github for setting up Playwright.")
    else:
        launch_job_tracker_app()

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import json
import threading
from PIL import Image, ImageTk
import threading

from app.emails.gmail import checkGmailConnection, setupGmailConnection, getGmailEmails
from app.embed import runEmbeddings
from app.parse import scrapeTextFromUrl
from app.paths import get_resource_path, get_data_path, is_valid_data_file_path, get_browsers_path


class CustomDropdown:
    def __init__(self, parent, options, default=None, width=120, callback=None):
        self.parent = parent
        self.options = options
        self.width = width
        self.callback = callback
        self.selected = tk.StringVar(value=default or options[0])
        self.is_open = False
        
        # Main container
        self.container = tk.Frame(parent, bg='#3d3d3d', highlightthickness=1, 
                                 highlightbackground='#555555')
        
        # Selected item display
        self.display = tk.Frame(self.container, bg='#3d3d3d', width=width, height=28)
        self.display.pack_propagate(False)
        self.display.pack()
        
        self.label = tk.Label(self.display, textvariable=self.selected, 
                             bg='#3d3d3d', fg='#e0e0e0', anchor='w', padx=8,
                             font=("Arial", 10))
        self.label.pack(side='left', fill='both', expand=True)
        
        # Arrow button
        self.arrow = tk.Label(self.display, text='▼', bg='#3d3d3d', fg='#a0a0a0',
                             font=('Arial', 8), padx=8)
        self.arrow.pack(side='right')
        
        # Dropdown list (initially hidden) - using Toplevel for proper layering
        self.dropdown_window = None
        
        # Set cursor for all parts
        self.display.config(cursor='hand2')
        self.label.config(cursor='hand2')
        self.arrow.config(cursor='hand2')
        
        # Bind events
        self.display.bind('<Button-1>', self.toggle_dropdown)
        self.label.bind('<Button-1>', self.toggle_dropdown)
        self.arrow.bind('<Button-1>', self.toggle_dropdown)
        
        # Hover effects
        self.display.bind('<Enter>', lambda e: self.container.config(highlightbackground='#777777'))
        self.display.bind('<Leave>', lambda e: self.container.config(highlightbackground='#555555'))
        self.label.bind('<Enter>', lambda e: self.container.config(highlightbackground='#777777'))
        self.label.bind('<Leave>', lambda e: self.container.config(highlightbackground='#555555'))
        self.arrow.bind('<Enter>', lambda e: self.container.config(highlightbackground='#777777'))
        self.arrow.bind('<Leave>', lambda e: self.container.config(highlightbackground='#555555'))
    
    def toggle_dropdown(self, event=None):
        if self.is_open:
            self.close_dropdown()
        else:
            self.open_dropdown()
    
    def open_dropdown(self):
        if self.dropdown_window:
            return
            
        self.is_open = True
        self.arrow.config(text='▲')
        
        # Create toplevel window for dropdown
        self.dropdown_window = tk.Toplevel(self.parent)
        self.dropdown_window.withdraw()
        self.dropdown_window.overrideredirect(True)
        self.dropdown_window.configure(bg='#3d3d3d', highlightthickness=1, 
                                      highlightbackground='#555555')
        
        # Position below the dropdown
        x = self.container.winfo_rootx()
        y = self.container.winfo_rooty() + self.container.winfo_height()
        self.dropdown_window.geometry(f"{self.width}x{len(self.options) * 28}+{x}+{y}")
        
        # Create buttons for each option
        for option in self.options:
            btn = tk.Label(self.dropdown_window, text=option, bg='#3d3d3d', 
                          fg='#e0e0e0', anchor='w', padx=8, font=("Arial", 10),
                          cursor='hand2')
            btn.pack(fill='x', ipady=4)
            
            # Bind hover and click events
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg='#4d4d4d'))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg='#3d3d3d'))
            btn.bind('<Button-1>', lambda e, opt=option: self.select_item(opt))
        
        self.dropdown_window.deiconify()
        
        # Bind click outside to close
        self.dropdown_window.bind('<FocusOut>', lambda e: self.close_dropdown())
        self.dropdown_window.focus_set()
    
    def close_dropdown(self):
        if self.dropdown_window:
            self.dropdown_window.destroy()
            self.dropdown_window = None
        self.is_open = False
        self.arrow.config(text='▼')
    
    def select_item(self, option):
        self.selected.set(option)
        self.close_dropdown()
        if self.callback:
            self.callback(option)
    
    def get(self):
        return self.selected.get()


class AddJobDialog:
    def __init__(self, parent, on_save, parse_callback=None, card_bg="#2b2b2b", 
                 text_primary="#ffffff", entry_bg="#3d3d3d", button_primary="#3498db",
                 button_primary_active="#2980b9", button_success="#27ae60", 
                 button_success_active="#229954", button_secondary="#95a5a6",
                 button_secondary_active="#7f8c8d"):
        self.parent = parent
        self.on_save = on_save
        self.parse_callback = parse_callback
        
        # Styling parameters
        self.card_bg = card_bg
        self.text_primary = text_primary
        self.entry_bg = entry_bg
        self.button_primary = button_primary
        self.button_primary_active = button_primary_active
        self.button_success = button_success
        self.button_success_active = button_success_active
        self.button_secondary = button_secondary
        self.button_secondary_active = button_secondary_active

        self.win = tk.Toplevel(parent)
        self.win.title("Add Job")
        self.win.geometry("550x500")
        self.win.configure(bg=self.card_bg)
        self.win.transient(parent)
        self.win.grab_set()

        self.mode = tk.StringVar(value="parse")
        self.text_file = None

        self.build_ui()

    # ------------------------
    # UI
    # ------------------------
    def build_ui(self):
        frame = tk.Frame(self.win, padx=15, pady=15, bg=self.card_bg)
        frame.pack(fill=tk.BOTH, expand=True)

        # Mode buttons
        mode_frame = tk.Frame(frame, bg=self.card_bg)
        mode_frame.pack(fill=tk.X, pady=(0, 10))

        self.parse_btn = tk.Button(
            mode_frame, text="🌐 Use URL Parser",
            command=lambda: self.set_mode("parse"),
            bg=self.button_primary, fg="white", 
            activebackground=self.button_primary_active,
            relief=tk.FLAT, cursor="hand2", padx=15, pady=5
        )
        self.parse_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.paste_btn = tk.Button(
            mode_frame, text="📝 Paste Text Manually",
            command=lambda: self.set_mode("paste"),
            bg=self.button_secondary, fg="white",
            activebackground=self.button_secondary_active,
            relief=tk.FLAT, cursor="hand2", padx=15, pady=5
        )
        self.paste_btn.pack(side=tk.LEFT)

        # Company
        tk.Label(frame, text="Company *", bg=self.card_bg, 
                fg=self.text_primary, font=("Arial", 10, "bold")).pack(anchor="w")
        self.company_entry = tk.Entry(frame, font=("Arial", 11),
                                     bg=self.entry_bg, fg=self.text_primary,
                                     insertbackground=self.text_primary, relief=tk.FLAT)
        self.company_entry.pack(fill=tk.X, pady=(0, 8))

        # Title
        tk.Label(frame, text="Job Title *", bg=self.card_bg,
                fg=self.text_primary, font=("Arial", 10, "bold")).pack(anchor="w")
        self.title_entry = tk.Entry(frame, font=("Arial", 11),
                                    bg=self.entry_bg, fg=self.text_primary,
                                    insertbackground=self.text_primary, relief=tk.FLAT)
        self.title_entry.pack(fill=tk.X, pady=(0, 8))

        # Content container (for mode-switching content)
        content_container = tk.Frame(frame, bg=self.card_bg)
        content_container.pack(fill=tk.BOTH, expand=True)

        # URL section
        self.url_frame = tk.Frame(content_container, bg=self.card_bg)
        tk.Label(self.url_frame, text="Job URL", bg=self.card_bg,
                fg=self.text_primary, font=("Arial", 10, "bold")).pack(anchor="w")

        self.url_entry = tk.Entry(self.url_frame, font=("Arial", 11),
                                 bg=self.entry_bg, fg=self.text_primary,
                                 insertbackground=self.text_primary, relief=tk.FLAT)
        self.url_entry.pack(fill=tk.X, pady=(0, 5))

        self.pull_btn = tk.Button(
            self.url_frame,
            text="Pull Job Text",
            command=self.pull_from_url,
            bg=self.button_primary, fg="white",
            activebackground=self.button_primary_active,
            relief=tk.FLAT, cursor="hand2", padx=15, pady=5
        )
        self.pull_btn.pack(anchor="w")

        # Status label
        self.status_label = tk.Label(
            self.url_frame, 
            text="", 
            bg=self.card_bg,
            fg="#3498db", 
            font=("Arial", 9), 
            anchor="w",
            wraplength=500, 
            justify="left"
        )
        self.status_label.pack(fill=tk.X, pady=(5, 0))

        self.url_frame.pack(fill=tk.BOTH, expand=True)

        # Manual text section
        self.manual_frame = tk.Frame(content_container, bg=self.card_bg)

        tk.Label(self.manual_frame, text="Paste Job Description", bg=self.card_bg,
                fg=self.text_primary, font=("Arial", 10, "bold")).pack(anchor="w")
        self.manual_text = tk.Text(self.manual_frame, height=10, wrap=tk.WORD,
                                   bg=self.entry_bg, fg=self.text_primary,
                                   insertbackground=self.text_primary, relief=tk.FLAT)
        self.manual_text.pack(fill=tk.BOTH, expand=True)

        # Spacer to push buttons to bottom
        spacer = tk.Frame(frame, bg=self.card_bg)
        spacer.pack(fill=tk.BOTH, expand=True)

        # Save / cancel
        btn_frame = tk.Frame(frame, bg=self.card_bg)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(15, 0))

        tk.Button(btn_frame, text="Save Job", command=self.save_job,
                 bg=self.button_success, fg="white", font=("Arial", 11, "bold"),
                 activebackground=self.button_success_active,
                 relief=tk.FLAT, cursor="hand2", padx=30, pady=8).pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(btn_frame, text="Cancel", command=self.win.destroy,
                 bg=self.button_secondary, fg="white", font=("Arial", 11),
                 activebackground=self.button_secondary_active,
                 relief=tk.FLAT, cursor="hand2", padx=30, pady=8).pack(side=tk.RIGHT)

    # ------------------------
    # Mode switching
    # ------------------------
    def set_mode(self, mode):
        self.mode.set(mode)

        if mode == "parse":
            # Update button colors
            self.parse_btn.config(bg=self.button_primary, activebackground=self.button_primary_active)
            self.paste_btn.config(bg=self.button_secondary, activebackground=self.button_secondary_active)
            
            # Switch frames
            self.manual_frame.pack_forget()
            self.url_frame.pack(fill=tk.BOTH, expand=True)
        else:
            # Update button colors
            self.parse_btn.config(bg=self.button_secondary, activebackground=self.button_secondary_active)
            self.paste_btn.config(bg=self.button_primary, activebackground=self.button_primary_active)
            
            # Switch frames
            self.url_frame.pack_forget()
            self.manual_frame.pack(fill=tk.BOTH, expand=True)

    # ------------------------
    # URL Parsing
    # ------------------------

    def update_status(self, message, color="#3498db"):
        self.status_label.config(text=message, fg=color)

    def updateTextFile(self, newTextFile):
        self.text_file = newTextFile

    def pullFromUrlThread(self, url, company, title, scrapeTextFromUrl, update_status, updateTextFile, afterFunc):
        text_content = scrapeTextFromUrl(url, update_status)

        if text_content:
            # Save to file (just the text content)
            safe_company = "".join(c for c in company if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{safe_company}_{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = get_data_path(os.path.join("data/pulledTextFiles", filename))
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            update_status("✅ Text successfully pulled!", "#2ecc71")

            self.pull_btn.config(state='normal', text='Pull Text Again')
            
            updateTextFile(filename)

            afterFunc()
        
    
    def afterPullFromUrlThread(self):
        messagebox.showinfo("Success", "Job text pulled successfully.")

    def pull_from_url(self):
        # update pull button

        # check if valid inputs
        if not self.parse_callback:
            messagebox.showerror("Error", "No parser connected.")
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Missing URL", "Please enter a URL.")
            return
        
        company = self.company_entry.get().strip()
        title = self.title_entry.get().strip()

        if not company or not title:
            messagebox.showwarning("Missing Company or Title", "Please enter company and title")
            return

        # execute pull functionality
        try:
            self.pull_btn.config(state='disabled', text='Pulling...')

            thread = threading.Thread(target=self.pullFromUrlThread, args=(url, company, title, self.parse_callback, self.update_status, self.updateTextFile, self.afterPullFromUrlThread), daemon=True)
            thread.start()
        except Exception as e:
            messagebox.showerror("Parsing Failed", str(e))

    # ------------------------
    # Save
    # ------------------------
    def save_job(self):
        self.company = self.company_entry.get().strip()
        self.title = self.title_entry.get().strip()

        if not self.company or not self.title:
            messagebox.showwarning("Missing Information", "Company and Job Title are required.")
            return

        text_file = self.text_file

        if self.mode.get() == "paste":
            content = self.manual_text.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("Missing Text", "Please paste job description text.")
                return

            os.makedirs(get_data_path("data/pulledTextFiles"), exist_ok=True)

            safe_company = "".join(c for c in self.company if c.isalnum() or c in " -_")
            safe_title = "".join(c for c in self.title if c.isalnum() or c in " -_")

            filename = f"{safe_company}_{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            text_file = get_data_path(os.path.join("data/pulledTextFiles", filename))

            with open(text_file, "w", encoding="utf-8") as f:
                f.write(content)

        job = {
            "company": self.company,
            "title": self.title,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "Applied",
            "text_file": text_file,
            "url": self.url_entry.get().strip() if self.mode.get() == "parse" else None
        }

        self.on_save(job)
        self.win.destroy()



class JobTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Job Application Tracker")
        self.root.geometry("900x700")
        self.root.configure(bg="#1a1a1a")

        icon = tk.PhotoImage(file=get_resource_path("resources/logo.png"))
        root.iconphoto(True, icon)
        
        # Store job data
        self.jobs = []
        self.filtered_jobs = []
        
        # Status colors
        self.status_colors = {
            "Applied": "#3498db",
            "Rejected": "#e74c3c",
            "Interview": "#2ecc71"
        }
        
        # Dark mode colors
        self.bg_dark = "#1a1a1a"
        self.card_bg = "#2d2d2d"
        self.text_primary = "#e0e0e0"
        self.text_secondary = "#a0a0a0"
        self.border_color = "#404040"
        
        # Create folders
        os.makedirs(get_data_path("data/pulledTextFiles"), exist_ok=True)
        if not os.path.exists(get_resource_path("resources")):
            os.makedirs(get_resource_path("resources"))
        if not os.path.exists(get_resource_path("resources/Images")):
            os.makedirs(get_resource_path("resources/Images"))
        
        # Load existing jobs from JSON
        self.load_jobs()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Top bar with search and add button
        top_frame = tk.Frame(self.root, bg="#242424", height=60)
        top_frame.pack(fill=tk.X, padx=0, pady=0)
        top_frame.pack_propagate(False)
        
        # Search bar
        search_frame = tk.Frame(top_frame, bg="#242424")
        search_frame.pack(side=tk.LEFT, padx=20, pady=10, fill=tk.X, expand=True)
        
        tk.Label(search_frame, text="Search:", bg="#242424", fg="#e0e0e0", 
                font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_jobs())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                               font=("Arial", 11), width=40, bg="#3d3d3d", 
                               fg="#e0e0e0", insertbackground="#e0e0e0",
                               relief=tk.FLAT, borderwidth=2)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Add button
        add_btn = tk.Button(top_frame, text="+ Add Job", command=self.open_add_dialog,
                           bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
                           relief=tk.FLAT, cursor="hand2", padx=20, pady=8,
                           activebackground="#229954")
        add_btn.pack(side=tk.RIGHT, padx=20, pady=10)

        update_btn = tk.Button(top_frame, text="Update Job Statuses",
                        command=self.open_update_statuses_window,
                        bg="#f39c12", fg="white", font=("Arial", 11, "bold"),
                        relief=tk.FLAT, cursor="hand2", padx=16, pady=8,
                        activebackground="#d68910")
        update_btn.pack(side=tk.RIGHT, padx=(0,10), pady=10)
        
        # Main scrollable area for job tiles
        main_frame = tk.Frame(self.root, bg=self.bg_dark)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas and scrollbar
        canvas = tk.Canvas(main_frame, bg=self.bg_dark, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        
        self.jobs_frame = tk.Frame(canvas, bg=self.bg_dark)
        
        self.jobs_frame.bind("<Configure>", 
                            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=self.jobs_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mouse wheel scrolling
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # Initial empty state
        self.update_job_display()
        
    def create_job_tile(self, job, index):
        tile = tk.Frame(self.jobs_frame, bg=self.card_bg, relief=tk.FLAT, 
                       borderwidth=1, highlightbackground=self.border_color,
                       highlightthickness=1)
        tile.pack(fill=tk.X, padx=5, pady=5, ipady=10)
        
        # Delete button in top right
        delete_btn = tk.Button(tile, text="x", command=lambda: self.delete_job(index, job),
                              bg=self.card_bg, fg="#808080", font=("Arial", 12),
                              relief=tk.FLAT, cursor="hand2", padx=8, pady=0,
                              activebackground=self.card_bg, activeforeground="#a0a0a0",
                              borderwidth=0)
        delete_btn.place(relx=1.0, x=-10, y=10, anchor="ne")
        
        # Hover effects for delete button
        delete_btn.bind("<Enter>", lambda e: delete_btn.config(fg="#e74c3c"))
        delete_btn.bind("<Leave>", lambda e: delete_btn.config(fg="#808080"))
        
        # Left section - Job info
        left_frame = tk.Frame(tile, bg=self.card_bg)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Company name (bold, larger)
        company_label = tk.Label(left_frame, text=job['company'], 
                                font=("Arial", 14, "bold"), bg=self.card_bg, 
                                fg=self.text_primary, anchor="w")
        company_label.pack(fill=tk.X)
        
        # Job title
        title_label = tk.Label(left_frame, text=job['title'], 
                              font=("Arial", 11), bg=self.card_bg, 
                              fg=self.text_secondary, anchor="w")
        title_label.pack(fill=tk.X, pady=(2, 5))
        
        # Date applied
        date_label = tk.Label(left_frame, text=f"Applied: {job['date']}", 
                            font=("Arial", 9), bg=self.card_bg, 
                            fg=self.text_secondary, anchor="w")
        date_label.pack(fill=tk.X)
        
        # View text button
        if job.get('text_file'):
            view_text_btn = tk.Button(left_frame, text="📄 View Pulled Text", 
                                     command=lambda: self.show_pulled_text(job),
                                     bg="#3498db", fg="white", font=("Arial", 9),
                                     relief=tk.FLAT, cursor="hand2",
                                     activebackground="#2980b9")
            view_text_btn.pack(anchor="w", pady=(5, 0))
        
        # Right section - Status and actions
        right_frame = tk.Frame(tile, bg=self.card_bg)
        right_frame.pack(side=tk.RIGHT, padx=15, pady=10)
        
        # Status dropdown
        status_frame = tk.Frame(right_frame, bg=self.card_bg)
        status_frame.pack(anchor="e")
        
        tk.Label(status_frame, text="Status:", bg=self.card_bg, fg=self.text_secondary,
                font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        # Custom dropdown
        dropdown = CustomDropdown(
            status_frame, 
            options=["Applied", "Rejected", "Interview"],
            default=job['status'],
            width=120,
            callback=lambda new_status: self.update_status(index, new_status)
        )
        dropdown.container.pack(side=tk.LEFT)
        
        # Status color indicator
        color = self.status_colors.get(job['status'], "#95a5a6")
        indicator = tk.Frame(right_frame, bg=color, width=80, height=4)
        indicator.pack(fill=tk.X, pady=(5, 0))
    
    def open_update_statuses_window(self):
        if os.path.exists(get_data_path("data/jobs_data.json")):
            UpdateJobStatusesWindow(self.root, self.card_bg, self.text_primary, self.text_secondary, self.reload_jobs_from_disk)
        else:
            messagebox.showerror("Error", "No jobs added")

    def add_job_to_list(self, job):
        self.jobs.append(job)
        self.save_jobs()
        self.update_job_display()

    def open_add_dialog(self):
        
        AddJobDialog(
            self.root,
            on_save=self.add_job_to_list,
            parse_callback=scrapeTextFromUrl,   # your existing Playwright function
            card_bg=self.card_bg,
            text_primary=self.text_primary
        )
    
    def show_pulled_text(self, job):
        """Display the pulled text in a new window"""
        filepath = get_data_path(os.path.join("data/pulledTextFiles", job['text_file']))
        if not job.get('text_file') or not is_valid_data_file_path(filepath):
            messagebox.showerror("Error", "Text file not found!")
            return
        
        text_window = tk.Toplevel(self.root)
        text_window.title(f"Pulled Text - {job['company']}")
        text_window.geometry("700x600")
        text_window.configure(bg=self.card_bg)
        
        # Header frame
        header_frame = tk.Frame(text_window, bg=self.card_bg)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Title
        tk.Label(header_frame, text=f"{job['company']} - {job['title']}", 
                font=("Arial", 14, "bold"), bg=self.card_bg,
                fg=self.text_primary).pack(anchor="w")
        
        # URL (if available)
        if job.get('url'):
            url_frame = tk.Frame(header_frame, bg=self.card_bg)
            url_frame.pack(anchor="w", pady=(2, 0))
            
            tk.Label(url_frame, text="Source: ", 
                    font=("Arial", 9), bg=self.card_bg,
                    fg=self.text_secondary).pack(side=tk.LEFT)
            
            url_label = tk.Label(url_frame, text=job['url'], 
                                font=("Arial", 9), bg=self.card_bg,
                                fg="#3498db", cursor="hand2")
            url_label.pack(side=tk.LEFT)
            
            # Click to copy functionality
            def copy_url(e):
                text_window.clipboard_clear()
                text_window.clipboard_append(job['url'])
                url_label.config(text="✓ Copied!")
                text_window.after(1500, lambda: url_label.config(text=job['url']))
            
            url_label.bind("<Button-1>", copy_url)
            
            # Hover effect
            url_label.bind("<Enter>", lambda e: url_label.config(fg="#2980b9"))
            url_label.bind("<Leave>", lambda e: url_label.config(fg="#3498db"))
        
        # Separator
        separator = tk.Frame(text_window, bg=self.border_color, height=1)
        separator.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Text widget with scrollbar
        text_frame = tk.Frame(text_window, bg=self.card_bg)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, 
                             bg="#3d3d3d", fg=self.text_primary,
                             font=("Arial", 10), yscrollcommand=scrollbar.set,
                             relief=tk.FLAT, padx=10, pady=10)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Load and display text
        try:
            if is_valid_data_file_path(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    text_widget.insert('1.0', content)
                    text_widget.config(state='disabled')  # Make read-only
        except Exception as e:
            text_widget.insert('1.0', f"Error loading file: {str(e)}")
            text_widget.config(state='disabled')
    
    def update_status(self, index, new_status):
        self.jobs[index]['status'] = new_status
        self.save_jobs()
        self.update_job_display()
    
    def delete_job(self, index, job):
        # Create custom confirmation dialog
        confirm_dialog = tk.Toplevel(self.root)
        confirm_dialog.title("Confirm Delete")
        confirm_dialog.geometry("400x220")
        confirm_dialog.resizable(False, False)
        confirm_dialog.configure(bg=self.card_bg)
        confirm_dialog.grid_columnconfigure(0, weight=1)
        confirm_dialog.grid_rowconfigure(0, weight=1)
        
        # Make dialog modal
        confirm_dialog.transient(self.root)
        confirm_dialog.grab_set()
        
        # Center the dialog
        confirm_dialog.update_idletasks()
        x = (confirm_dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (confirm_dialog.winfo_screenheight() // 2) - (220 // 2)
        confirm_dialog.geometry(f"400x220+{x}+{y}")
        
        # Main container
        main_container = tk.Frame(confirm_dialog, bg=self.card_bg)
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=0)
        main_container.grid_rowconfigure(2, weight=0)
        main_container.grid_rowconfigure(3, weight=0)
        main_container.grid_rowconfigure(4, weight=1)
        
        # Warning icon centered
        caution_label = tk.Label(main_container, text="\u26A0", font=("Arial", 48),
                bg=self.card_bg, fg="#f39c12")
        caution_label.grid(row=1, column=0, pady=0)
        
        tk.Label(main_container, text=f"Delete {job['title']} application?",
                font=("Arial", 12), bg=self.card_bg, fg=self.text_primary,
                wraplength=340).grid(row=2, column=0, pady=(10,10))
        
        button_frame = tk.Frame(main_container, bg=self.card_bg)
        button_frame.grid(row=3, column=0)
        
        def on_delete():
            self.jobs.pop(index)
            self.save_jobs()
            self.update_job_display()
            confirm_dialog.destroy()
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=confirm_dialog.destroy,
                              bg="#95a5a6", fg="white", font=("Arial", 10),
                              relief=tk.FLAT, cursor="hand2", padx=25, pady=8,
                              activebackground="#7f8c8d")
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = tk.Button(button_frame, text="Delete", command=on_delete,
                              bg="#e74c3c", fg="white", font=("Arial", 10, "bold"),
                              relief=tk.FLAT, cursor="hand2", padx=25, pady=8,
                              activebackground="#c0392b")
        delete_btn.pack(side=tk.LEFT, padx=5)
        
    def filter_jobs(self):
        search_term = self.search_var.get().lower()
        
        if not search_term:
            self.filtered_jobs = self.jobs.copy()
        else:
            self.filtered_jobs = [
                job for job in self.jobs 
                if search_term in job['company'].lower() or 
                   search_term in job['title'].lower() or
                   search_term in job['status'].lower()
            ]
        
        self.update_job_display()
        
    def update_job_display(self):
        # Clear current display
        for widget in self.jobs_frame.winfo_children():
            widget.destroy()
        
        # Determine which jobs to display
        display_jobs = self.filtered_jobs if hasattr(self, 'filtered_jobs') and self.search_var.get() else self.jobs
        
        if not display_jobs:
            # Show empty state
            empty_label = tk.Label(self.jobs_frame, 
                                  text="No job applications yet.\nClick '+ Add Job' to get started!",
                                  font=("Arial", 12), fg=self.text_secondary, 
                                  bg=self.bg_dark)
            empty_label.pack(pady=50)
        else:
            # Create tiles for each job
            for i, job in enumerate(display_jobs):
                self.create_job_tile(job, self.jobs.index(job))
    
    def save_jobs(self):
        """Save jobs to JSON file"""
        try:
            with open(get_data_path('data/jobs_data.json'), 'w', encoding='utf-8') as f:
                json.dump(self.jobs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving jobs: {e}")
    
    def load_jobs(self):
        """Load jobs from JSON file"""
        try:
            if is_valid_data_file_path('data/jobs_data.json'):
                with open(get_data_path('data/jobs_data.json'), 'r', encoding='utf-8') as f:
                    self.jobs = json.load(f)
        except Exception as e:
            print(f"Error loading jobs: {e}")
            self.jobs = []

    def reload_jobs_from_disk(self):
        """Reload jobs from JSON and refresh UI"""
        self.load_jobs()          # re-read jobs_data.json
        self.filter_jobs()        # preserves current search text & refreshes UI




class UpdateJobStatusesWindow:
    def __init__(self, root, card_bg, text_primary, text_secondary, reloadFunc):
        self.root = root
        self.card_bg = card_bg
        self.text_primary = text_primary
        self.text_secondary = text_secondary
        self.pullBtn = None
        self.selectProviderButtonsEnabled = True
        self.pullButtonEnabled = True
        self.connected = False
        self.reloadFunc = reloadFunc

        self.selected_provider = tk.StringVar(value="Gmail")

        self.connectedStatus = False

        self.original_colors = {
            "Gmail": "#4285f4",
            "iCloud": "#0a84ff",
            "Outlook": "#0078d4"
        }

        self.darker_colors = {
            "Gmail": "#3367d6",
            "iCloud": "#0051a8",
            "Outlook": "#005a9e"
        }

        self.provider_buttons = {}

        self._create_window()
        self._build_ui()

    # -------------------------
    # Window setup
    # -------------------------
    def _create_window(self):
        self.win = tk.Toplevel(self.root)
        self.win.title("Update Job Statuses")
        self.win.geometry("600x420")
        self.win.configure(bg=self.card_bg)

        self.win.transient(self.root)
        self.win.grab_set()

    # -------------------------
    # UI construction
    # -------------------------
    def _build_ui(self):
        tk.Label(
            self.win,
            text="Update Job Statuses",
            font=("Arial", 14, "bold"),
            bg=self.card_bg,
            fg=self.text_primary
        ).pack(anchor="w", padx=20, pady=(20, 10))

        tk.Label(
            self.win,
            text=(
                "Instructions:\n"
                "1. Label emails for interviews with label 'Internship-Interview'\n"
                "2. Label emails for rejections with label 'Internship-Rejected'\n"
                "3. Connect Email"
            ),
            bg=self.card_bg,
            fg=self.text_secondary,
            wraplength=560,
            justify="left"
        ).pack(anchor="w", padx=20)

        self.desc_label = tk.Label(
            self.win,
            text="",
            bg=self.card_bg,
            fg=self.text_secondary,
            wraplength=560,
            justify="left"
        )

        self._create_provider_buttons()

        # Dynamic content frame (below provider buttons)
        self.provider_content_frame = tk.Frame(self.win, bg=self.card_bg)
        self.provider_content_frame.pack(fill=tk.X, padx=20, pady=(6, 12))

        self.select_provider(self.selected_provider.get())

        self.desc_label.pack(fill=tk.X, padx=20, pady=(8, 12))

        self._create_action_buttons()


    # -------------------------
    # Providers
    # -------------------------
    def _create_provider_buttons(self):
        gmail_icon = self._load_icon(get_resource_path("resources/Images/gmail.png"))
        icloud_icon = self._load_icon(get_resource_path("resources/Images/icloud.png"))
        outlook_icon = self._load_icon(get_resource_path("resources/Images/outlook.png"))

        btn_specs = [
            ("Gmail", gmail_icon),
            ("iCloud", icloud_icon),
            ("Outlook", outlook_icon)
        ]

        providers_box = tk.Frame(self.win, bg=self.card_bg)
        providers_box.pack(fill=tk.X, padx=120, pady=(12, 6))
        providers_box.columnconfigure([0, 1, 2], weight=1)

        for col, (name, icon) in enumerate(btn_specs):
            btn = tk.Button(
                providers_box,
                text=name,
                bg=self.original_colors[name],
                fg="white",
                font=("Arial", 10, "bold"),
                relief=tk.RAISED,
                cursor="hand2",
                compound="left",
                padx=6,
                command=lambda n=name: self.select_provider(n)
            )

            if icon:
                btn.config(image=icon)
                btn.image = icon

            btn.grid(row=0, column=col, sticky="nsew", padx=12, pady=4)
            self.provider_buttons[name] = btn


    def select_provider(self, name):
        if self.selectProviderButtonsEnabled == False:
            return
        self.selected_provider.set(name)

        for btn_name, btn in self.provider_buttons.items():
            if btn_name == name:
                btn.config(bg=self.darker_colors[btn_name], relief=tk.SUNKEN, bd=2)
            else:
                btn.config(bg=self.original_colors[btn_name], relief=tk.RAISED, bd=1)


        # Update dynamic provider content
        self._clear_provider_content()

        if name == "Gmail":
            self._build_gmail_content()
        elif name == "iCloud":
            self._build_icloud_content()
        elif name == "Outlook":
            self._build_outlook_content()

        if self.pullBtn is not None and self.pullBtn.winfo_exists():
            self.pullBtn.config(text="Loading...", bg="#4285f4", fg="white")
        
        self.win.update_idletasks()

        threading.Thread(target=self._update_pull_button, daemon=True).start()

    def _update_pull_button(self):
        if self.pullBtn is None or not self.pullBtn.winfo_exists():
            return

        # Disable provider buttons while loading
        self.win.after(0, lambda: self.disable_provider_buttons())
        self.win.after(0, lambda: self.disable_pull_button())
        
        # Run the slow check
        self.connected = self.checkConnectionStatus()

        def update_ui():
            self.enable_provider_buttons()
            self.enable_pull_button()
            self.pullBtn.config(
                text="Pull From Email" if self.connected else "Setup Email Connection",
                bg="#4285f4" if self.connected else "green",
                fg="white"
            )
        
        self.win.after(0, update_ui)

    def checkConnectionStatus(self):
        if self.selected_provider.get() == "Gmail":
            return checkGmailConnection()
        elif self.selected_provider.get() == "iCloud":
            print("add icloud")
        elif self.selected_provider.get() == "Outlook":
            print("add outlook")
        return False

    # -------------------------
    # Provider content builders
    # -------------------------
    def _clear_provider_content(self):
        for widget in self.provider_content_frame.winfo_children():
            widget.destroy()

    def _build_gmail_content(self):

        tk.Label(
            self.provider_content_frame,
            text=(
                "• Test"
            ),
            bg=self.card_bg,
            fg=self.text_secondary,
            justify="left"
        ).pack(anchor="w", pady=(4, 0))

    def _build_icloud_content(self):

        tk.Label(
            self.provider_content_frame,
            text="iCloud Mail Coming Soon",
            bg=self.card_bg,
            fg=self.text_secondary
        ).pack(anchor="w", pady=(4, 0))

    def _build_outlook_content(self):

        tk.Label(
            self.provider_content_frame,
            text="Outlook Coming Soon",
            bg=self.card_bg,
            fg=self.text_secondary
        ).pack(anchor="w", pady=(4, 0))

    # -------------------------
    # Action buttons
    # -------------------------
    def _create_action_buttons(self):
        self.pullBtn = tk.Button(
            self.win,
            text="Loading...",
            command=self.pull_from_email,
            bg="#3498db",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=16,
            pady=8,
            activebackground="#2980b9"
        )
        self.pullBtn.pack(pady=(0, 12))

        self.disable_pull_button()
        self.disable_provider_buttons()

        self.embedBtn = tk.Button(
            self.win,
            text="Run Embedding",
            command=self.runEmbeddingsFunc,
            bg="grey",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=16,
            pady=16,
            activebackground="#2980b9"
        )
        self.embedBtn.pack(pady=(0, 12))
        self.disable_embed_button()

        self.win.update_idletasks()

        threading.Thread(target=self.createActionButtonThread, daemon=True).start()

    def createActionButtonThread(self):
        backgroundColor = None
        if self.checkConnectionStatus():
            pullText = "Pull From Email"
            backgroundColor = "#2980b9"
            self.connected = True
        else:
            pullText = "Setup Email Connection"
            backgroundColor = "green"
            self.connected = False
        self.pullBtn.config(text=pullText, bg=backgroundColor)

        self.enable_pull_button()
        self.enable_provider_buttons()

    def disable_provider_buttons(self):
        self.selectProviderButtonsEnabled = False
    
    def enable_provider_buttons(self):
        self.selectProviderButtonsEnabled = True

    def disable_pull_button(self):
        self.pullButtonEnabled = False
    
    def enable_pull_button(self):
        self.pullButtonEnabled = True
    
    def disable_embed_button(self):
        self.embedBtnEnabled = False

    def enable_embed_button(self):
        self.embedBtnEnabled = True

    # -------------------------
    # Logic
    # -------------------------
    def pull_from_email(self):
        if self.pullButtonEnabled == False:
            return
        
        self.pullBtn.config(text="Running...", bg="#3498db", fg="white")

        self.win.update_idletasks()

        threading.Thread(target=self.pull_button_thread, daemon=True).start()

    def pull_button_thread(self):
        self.disable_pull_button()
        self.disable_provider_buttons()
        provider = self.selected_provider.get()
        if self.connected == False:
            setupStatus = False
            if provider == "Gmail":
                setupStatus = setupGmailConnection()
            elif provider == "iCloud":
                print("finish icloud")
            elif provider == "Outlook":
                print("finish outlook")
            if setupStatus:
                self.connected = True
                self.pullBtn.config(text="Pull From Email", bg="#3498db", fg="white")
            else:
                self.pullBtn.config(text="Setup Email Connection", bg="green", fg="white")
        elif self.connected:
            if provider == "Gmail":
                self.emails = getGmailEmails() 
                print("Emails: ")
                print(self.emails)
                self.enable_embed_button()
                self.embedBtn.config(bg="#3498db", fg="white")
            elif provider == "iCloud":
                print("finish icloud")
            elif provider == "Outlook":
                print("finish outlook")
            self.pullBtn.config(text="Pull From Email", bg="#3498db", fg="white")

        self.enable_pull_button()
        self.enable_provider_buttons()


    def runEmbeddingsFunc(self):
        if self.embedBtnEnabled == False:
            return  

        self.disable_pull_button()
        self.disable_provider_buttons()
        self.disable_embed_button()

        self.embedBtn.config(text="Running...", bg="#3498db", fg="white")

        self.win.update_idletasks()

        threading.Thread(target=self.runEmbedThread, daemon=True).start()

    def runEmbedThread(self):
        invalidEmails, emailsUpdated = runEmbeddings(self.emails)
        # TODO: make logs viewable
        box = CustomMessageBox(
            self.win,
            title="Embedding Results",
            message=f"{emailsUpdated} job postings changed"
        )
        self.enable_pull_button()
        self.enable_provider_buttons()
        self.embedBtn.config(text="Run Embedding", bg="grey", fg="white")
        self.reloadFunc()


    # -------------------------
    # Utilities
    # -------------------------
    def _load_icon(self, path, max_size=(32, 32)):
        try:
            img = Image.open(path)
            img.thumbnail(max_size)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return None

class CustomMessageBox:
    def __init__(self, parent, title="Message", message="", buttons=("OK",)):
        self.parent = parent
        self.result = None

        self.win = tk.Toplevel(parent)
        self.win.title(title)
        self.win.geometry("350x160")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()  # Make modal

        # ===== Frame =====
        container = tk.Frame(self.win, padx=20, pady=20)
        container.pack(expand=True, fill="both")

        # ===== Message =====
        tk.Label(
            container,
            text=message,
            wraplength=300,
            justify="left",
            font=("Segoe UI", 10)
        ).pack(pady=(0, 20))

        # ===== Buttons =====
        btn_frame = tk.Frame(container)
        btn_frame.pack()

        for btn in buttons:
            tk.Button(
                btn_frame,
                text=btn,
                width=10,
                command=lambda b=btn: self._on_click(b)
            ).pack(side="left", padx=5)

        # Center window
        self._center()

        # Wait for window to close
        parent.wait_window(self.win)

    def _on_click(self, value):
        self.result = value
        self.win.destroy()

    def _center(self):
        self.win.update_idletasks()
        x = self.parent.winfo_rootx() + (
            self.parent.winfo_width() - self.win.winfo_width()
        ) // 2
        y = self.parent.winfo_rooty() + (
            self.parent.winfo_height() - self.win.winfo_height()
        ) // 2
        self.win.geometry(f"+{x}+{y}")


def is_playwright_setup_needed():
    """Return True if browsers folder is missing or empty."""
    path = get_browsers_path()
    return not os.listdir(path)


def launch_job_tracker_app():
    root = tk.Tk()
    app2 = JobTrackerApp(root) 
    root.mainloop()


if __name__ == "__main__":
    if is_playwright_setup_needed():
        messagebox.showerror("Playwright Error", "Playwright setup needed. Follow instructions on Github for setting up Playwright.")
    else:
        launch_job_tracker_app()


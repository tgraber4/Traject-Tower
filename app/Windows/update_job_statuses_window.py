import tkinter as tk
import json
import os
import threading
from PIL import Image, ImageTk

from app.emails.gmail import checkGmailConnection, setupGmailConnection, getGmailEmails
from app.embed import runEmbeddings
from app.paths import get_resource_path, get_data_path
from app.Windows.custom_message_box import CustomMessageBox

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
        self.win.geometry("600x480")
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

        self.logsBtn = tk.Button(
            self.win,
            text="View Logs",
            command=self.show_logs_window,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=16,
            pady=8,
            activebackground="#7f8c8d"
        )
        self.logsBtn.pack(pady=(0, 12))

        self.win.update_idletasks()

        threading.Thread(target=self.createActionButtonThread, daemon=True).start()

    def show_logs_window(self):
        """Display the content of data/logs.json in a new window"""
        logs_path = get_data_path("data/logs.json")
        
        logs_window = tk.Toplevel(self.win)
        logs_window.title("Jobs Updated Logs")
        logs_window.geometry("700x500")
        logs_window.configure(bg=self.card_bg)
        logs_window.transient(self.win)
        
        tk.Label(logs_window, text="Jobs Updated From Emails", font=("Arial", 14, "bold"),
                bg=self.card_bg, fg=self.text_primary).pack(pady=15)
        
        text_frame = tk.Frame(logs_window, bg=self.card_bg)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        log_display = tk.Text(text_frame, wrap=tk.WORD, bg="#3d3d3d", 
                             fg=self.text_primary, font=("Consolas", 10),
                             yscrollcommand=scrollbar.set, relief=tk.FLAT,
                             padx=10, pady=10)
        log_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=log_display.yview)
        
        try:
            if os.path.exists(logs_path):
                with open(logs_path, 'r', encoding='utf-8') as f:
                    logs_data = json.load(f)
                
                content = []
                
                # Format Jobs Updated
                jobs_updated = logs_data.get("JobsUpdated", [])
                if not jobs_updated:
                    content.append("No jobs updated yet.")
                else:
                    # Reverse list to show most recent at the top
                    for job in reversed(jobs_updated):
                        company = job.get("company", "Unknown Company")
                        title = job.get("title", "Unknown Title")
                        j_type = job.get("type", "Unknown Type")
                        content.append(f"• {company} - {title}: {j_type}")
                
                log_display.insert("1.0", "\n".join(content))
            else:
                log_display.insert("1.0", "Log file (logs.json) not found yet.")
        except Exception as e:
            log_display.insert("1.0", f"Error reading logs: {str(e)}")
            
        log_display.config(state="disabled")

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

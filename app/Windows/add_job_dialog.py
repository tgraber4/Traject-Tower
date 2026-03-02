import tkinter as tk
from tkinter import messagebox, filedialog
import os
import shutil
import threading
from datetime import datetime
from app.paths import get_data_path

class AddJobDialog:
    def __init__(self, parent, on_save, parse_callback=None, card_bg="#2b2b2b", 
                 text_primary="#ffffff", text_secondary="#a0a0a0", entry_bg="#3d3d3d", button_primary="#3498db",
                 button_primary_active="#2980b9", button_success="#27ae60", 
                 button_success_active="#229954", button_secondary="#95a5a6",
                 button_secondary_active="#7f8c8d"):
        self.parent = parent
        self.on_save = on_save
        self.parse_callback = parse_callback
        
        # Styling parameters
        self.card_bg = card_bg
        self.text_primary = text_primary
        self.text_secondary = text_secondary
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
        self.image_file = None

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
        self.paste_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.image_btn = tk.Button(
            mode_frame, text="🖼️ Insert Image",
            command=lambda: self.set_mode("image"),
            bg=self.button_secondary, fg="white",
            activebackground=self.button_secondary_active,
            relief=tk.FLAT, cursor="hand2", padx=15, pady=5
        )
        self.image_btn.pack(side=tk.LEFT)

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

        # Manual text section
        self.manual_frame = tk.Frame(content_container, bg=self.card_bg)

        tk.Label(self.manual_frame, text="Paste Job Description", bg=self.card_bg,
                fg=self.text_primary, font=("Arial", 10, "bold")).pack(anchor="w")
        self.manual_text = tk.Text(self.manual_frame, height=10, wrap=tk.WORD,
                                   bg=self.entry_bg, fg=self.text_primary,
                                   insertbackground=self.text_primary, relief=tk.FLAT)
        self.manual_text.pack(fill=tk.BOTH, expand=True)

        # Image selection section
        self.image_frame = tk.Frame(content_container, bg=self.card_bg)
        tk.Label(self.image_frame, text="Select Job Screenshot", bg=self.card_bg,
                fg=self.text_primary, font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.image_path_label = tk.Label(self.image_frame, text="No image selected", 
                                        bg=self.card_bg, fg=self.text_secondary, 
                                        font=("Arial", 9), wraplength=500, justify="left")
        self.image_path_label.pack(fill=tk.X, pady=(5, 5))

        tk.Button(self.image_frame, text="Choose Image...", command=self.select_image,
                 bg=self.button_primary, fg="white", 
                 activebackground=self.button_primary_active,
                 relief=tk.FLAT, cursor="hand2", padx=15, pady=5).pack(anchor="w")

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

        self.set_mode("parse")

    # ------------------------
    # Mode switching
    # ------------------------
    def set_mode(self, mode):
        self.mode.set(mode)

        # Reset all button colors
        self.parse_btn.config(bg=self.button_secondary, activebackground=self.button_secondary_active)
        self.paste_btn.config(bg=self.button_secondary, activebackground=self.button_secondary_active)
        self.image_btn.config(bg=self.button_secondary, activebackground=self.button_secondary_active)
        
        # Hide all frames
        self.url_frame.pack_forget()
        self.manual_frame.pack_forget()
        self.image_frame.pack_forget()

        if mode == "parse":
            self.parse_btn.config(bg=self.button_primary, activebackground=self.button_primary_active)
            self.url_frame.pack(fill=tk.BOTH, expand=True)
        elif mode == "paste":
            self.paste_btn.config(bg=self.button_primary, activebackground=self.button_primary_active)
            self.manual_frame.pack(fill=tk.BOTH, expand=True)
        elif mode == "image":
            self.image_btn.config(bg=self.button_primary, activebackground=self.button_primary_active)
            self.image_frame.pack(fill=tk.BOTH, expand=True)

    # ------------------------
    # URL Parsing
    # ------------------------

    def update_status(self, message, color="#3498db"):
        self.status_label.config(text=message, fg=color)

    def updateTextFile(self, newTextFile):
        self.text_file = newTextFile

    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Job Screenshot",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            self.image_file = file_path
            self.image_path_label.config(text=os.path.basename(file_path))

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
        image_file_name = None

        if self.mode.get() == "paste":
            content = self.manual_text.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("Missing Text", "Please paste job description text.")
                return

            os.makedirs(get_data_path("data/pulledTextFiles"), exist_ok=True)

            safe_company = "".join(c for c in self.company if c.isalnum() or c in " -_")
            safe_title = "".join(c for c in self.title if c.isalnum() or c in " -_")

            filename = f"{safe_company}_{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = get_data_path(os.path.join("data/pulledTextFiles", filename))

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            text_file = filename
        
        elif self.mode.get() == "image":
            if not self.image_file:
                messagebox.showwarning("Missing Image", "Please select an image.")
                return
            
            os.makedirs(get_data_path("data/jobImages"), exist_ok=True)
            
            safe_company = "".join(c for c in self.company if c.isalnum() or c in " -_")
            safe_title = "".join(c for c in self.title if c.isalnum() or c in " -_")
            ext = os.path.splitext(self.image_file)[1]
            image_file_name = f"{safe_company}_{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
            image_dest = get_data_path(os.path.join("data/jobImages", image_file_name))
            
            shutil.move(self.image_file, image_dest)
            text_file = None

        job = {
            "company": self.company,
            "title": self.title,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "Applied",
            "text_file": text_file,
            "imageFile": image_file_name,
            "url": self.url_entry.get().strip() if self.mode.get() == "parse" else None
        }

        self.on_save(job)
        self.win.destroy()

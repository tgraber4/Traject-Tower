import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from PIL import Image, ImageTk

from app.paths import get_resource_path, get_data_path, is_valid_data_file_path
from app.parse import scrapeTextFromUrl
from app.Windows.custom_dropdown import CustomDropdown
from app.Windows.add_job_dialog import AddJobDialog
from app.Windows.update_job_statuses_window import UpdateJobStatusesWindow

class JobTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Job Application Tracker")
        self.root.geometry("975x700")
        self.root.configure(bg="#1a1a1a")

        icon = tk.PhotoImage(file=get_resource_path("resources/logo.png"))
        root.iconphoto(True, icon)
        
        # Store job data
        self.jobs = []
        self.filtered_jobs = []
        self.search_timer = None
        self.status_filter_var = tk.StringVar(value="All Statuses")
        
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
        os.makedirs(get_data_path("data/jobImages"), exist_ok=True)
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
        
        # Job count display frame
        self.stats_frame = tk.Frame(self.root, bg=self.bg_dark)
        self.stats_frame.pack(fill=tk.X, padx=20, pady=(10, 0))
        
        self.job_count_label = tk.Label(self.stats_frame, text="Total Jobs: 0", 
                                       bg=self.bg_dark, fg=self.text_secondary, 
                                       font=("Arial", 10, "bold"))
        self.job_count_label.pack(side=tk.LEFT)
        
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

        # Status Filter Dropdown
        tk.Label(search_frame, text="Status:", bg="#242424", fg="#e0e0e0", 
                font=("Arial", 10)).pack(side=tk.LEFT, padx=(15, 10))
        
        status_options = ["All Statuses", "Applied", "Rejected", "Interview"]
        self.status_dropdown = CustomDropdown(
            search_frame, 
            options=status_options,
            default="All Statuses",
            width=130,
            callback=self._on_status_filter_change
        )
        self.status_dropdown.container.pack(side=tk.LEFT)
        
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
        self.canvas = tk.Canvas(main_frame, bg=self.bg_dark, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.jobs_frame = tk.Frame(self.canvas, bg=self.bg_dark)
        
        self.jobs_frame.bind("<Configure>", 
                            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas.create_window((0, 0), window=self.jobs_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mouse wheel scrolling (bind to canvas instead of bind_all)
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # Initial empty state
        self.update_job_display()
        
    def create_job_tile(self, job, index):
        tile = tk.Frame(self.jobs_frame, bg=self.card_bg, relief=tk.FLAT, 
                       borderwidth=1, highlightbackground=self.border_color,
                       highlightthickness=1)
        tile.pack(fill=tk.X, padx=5, pady=5, ipady=10)

        # Handle scrolling when mouse is over this tile
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        tile.bind("<MouseWheel>", _on_mousewheel)
        
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
        
        # View button (Text or Image)
        if job.get('text_file'):
            view_text_btn = tk.Button(left_frame, text="📄 View Pulled Text", 
                                     command=lambda: self.show_pulled_text(job),
                                     bg="#3498db", fg="white", font=("Arial", 9),
                                     relief=tk.FLAT, cursor="hand2",
                                     activebackground="#2980b9")
            view_text_btn.pack(anchor="w", pady=(5, 0))
        elif job.get('imageFile'):
            view_image_btn = tk.Button(left_frame, text="🖼️ View Job Image", 
                                      command=lambda: self.show_job_image(job),
                                      bg="#3498db", fg="white", font=("Arial", 9),
                                      relief=tk.FLAT, cursor="hand2",
                                      activebackground="#2980b9")
            view_image_btn.pack(anchor="w", pady=(5, 0))
        
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

        # Bind scroll event to all children except interactive elements
        def bind_recursive(widget):
            if not isinstance(widget, (tk.Button, CustomDropdown)):
                widget.bind("<MouseWheel>", _on_mousewheel)
            for child in widget.winfo_children():
                bind_recursive(child)
        
        bind_recursive(tile)
    
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
            text_primary=self.text_primary,
            text_secondary=self.text_secondary
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
    
    def show_job_image(self, job):
        """Display the job screenshot in a new window with zoom and scroll"""
        if not job.get('imageFile'):
            messagebox.showerror("Error", "No image file associated with this job!")
            return
            
        filepath = get_data_path(os.path.join("data/jobImages", job['imageFile']))
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"Image file not found at: {filepath}")
            return
            
        image_window = tk.Toplevel(self.root)
        image_window.title(f"Job Image - {job['company']}")
        image_window.geometry("900x700")
        image_window.configure(bg=self.card_bg)
        
        # Header
        header_frame = tk.Frame(image_window, bg=self.card_bg)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(header_frame, text=f"{job['company']} - {job['title']}", 
                font=("Arial", 14, "bold"), bg=self.card_bg,
                fg=self.text_primary).pack(side=tk.LEFT)

        # Zoom state
        state = {
            'zoom_level': 1.0,
            'auto_fit': True,
            'pil_image': None,
            'tk_image': None,
            'canvas_image_id': None
        }

        # Zoom controls in header
        controls_frame = tk.Frame(header_frame, bg=self.card_bg)
        controls_frame.pack(side=tk.RIGHT)

        def change_zoom(delta):
            state['auto_fit'] = False
            state['zoom_level'] *= delta
            # Limit zoom
            state['zoom_level'] = max(0.1, min(state['zoom_level'], 5.0))
            render_image()

        def reset_zoom():
            state['auto_fit'] = False
            state['zoom_level'] = 1.0
            render_image()

        def toggle_fit():
            state['auto_fit'] = True
            render_image()

        tk.Button(controls_frame, text="🔍+", command=lambda: change_zoom(1.2),
                 bg="#3d3d3d", fg="white", relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=2)
        tk.Button(controls_frame, text="🔍-", command=lambda: change_zoom(0.8),
                 bg="#3d3d3d", fg="white", relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=2)
        tk.Button(controls_frame, text="1:1", command=reset_zoom,
                 bg="#3d3d3d", fg="white", relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=2)
        tk.Button(controls_frame, text="Fit", command=toggle_fit,
                 bg="#3d3d3d", fg="white", relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=2)
        
        # Canvas for display
        display_frame = tk.Frame(image_window, bg="#1e1e1e")
        display_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        canvas = tk.Canvas(display_frame, bg="#1e1e1e", highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        v_scroll = tk.Scrollbar(display_frame, orient=tk.VERTICAL, command=canvas.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll = tk.Scrollbar(image_window, orient=tk.HORIZONTAL, command=canvas.xview)
        h_scroll.pack(fill=tk.X, padx=20, pady=(0, 10))

        canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        def render_image(event=None):
            if not state['pil_image']: return

            img_w, img_h = state['pil_image'].size
            
            if state['auto_fit']:
                # Calculate fit ratio
                canvas_w = canvas.winfo_width()
                canvas_h = canvas.winfo_height()
                if canvas_w <= 1: canvas_w = 860 # Fallback
                if canvas_h <= 1: canvas_h = 580
                
                ratio = min(canvas_w / img_w, canvas_h / img_h)
                state['zoom_level'] = ratio
            
            new_w = int(img_w * state['zoom_level'])
            new_h = int(img_h * state['zoom_level'])

            if new_w > 0 and new_h > 0:
                resized = state['pil_image'].resize((new_w, new_h), Image.Resampling.LANCZOS)
                state['tk_image'] = ImageTk.PhotoImage(resized)
                
                canvas.delete("all")
                # Center if smaller than canvas, otherwise start at 0,0
                canvas_w = canvas.winfo_width()
                canvas_h = canvas.winfo_height()
                
                x = max(0, (canvas_w - new_w) // 2) if new_w < canvas_w else 0
                y = max(0, (canvas_h - new_h) // 2) if new_h < canvas_h else 0
                
                canvas.create_image(x, y, anchor=tk.NW, image=state['tk_image'])
                canvas.config(scrollregion=(0, 0, new_w + x, new_h + y))

        try:
            state['pil_image'] = Image.open(filepath)
            image_window.after(100, render_image)
            image_window.bind("<Configure>", lambda e: render_image() if e.widget == image_window and state['auto_fit'] else None)
            
            # Mouse wheel zoom (Ctrl + Scroll)
            def mouse_wheel(event):
                if event.state & 0x0004: # Control key held
                    if event.delta > 0: change_zoom(1.1)
                    else: change_zoom(0.9)
                else:
                    # Normal scroll
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

            image_window.bind("<MouseWheel>", mouse_wheel)

        except Exception as e:
            tk.Label(display_frame, text=f"Error loading image: {str(e)}", 
                    bg="#1e1e1e", fg="#e74c3c").pack(pady=20)

    def update_status(self, index, new_status):
        self.jobs[index]['status'] = new_status
        self.save_jobs()
        self.update_job_display(reset_scroll=False)
    
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
            self.update_job_display(reset_scroll=False)
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
        """Wait for 100ms after the last keypress before filtering"""
        if self.search_timer:
            self.root.after_cancel(self.search_timer)
        
        self.search_timer = self.root.after(100, self._perform_filter)

    def _on_status_filter_change(self, new_status):
        self.status_filter_var.set(new_status)
        self.filter_jobs()

    def _perform_filter(self):
        """Actually execute the filtering logic"""
        search_term = self.search_var.get().lower()
        selected_status = self.status_filter_var.get()
        
        # Start with all jobs
        filtered = self.jobs.copy()
        
        # Apply Status filter
        if selected_status != "All Statuses":
            filtered = [job for job in filtered if job['status'] == selected_status]
            
        # Apply Search filter
        if search_term:
            filtered = [
                job for job in filtered 
                if search_term in job['company'].lower() or 
                   search_term in job['title'].lower() or
                   search_term in job['status'].lower()
            ]
        
        self.filtered_jobs = filtered
        self.update_job_display()
        
    def update_job_display(self, reset_scroll=True):
        # Reset scroll position to top
        if reset_scroll:
            self.canvas.yview_moveto(0)
        
        # Clear current display
        for widget in self.jobs_frame.winfo_children():
            widget.destroy()
        
        # Determine which jobs to display
        is_filtering = bool(self.search_var.get()) or self.status_filter_var.get() != "All Statuses"
        display_jobs = self.filtered_jobs if hasattr(self, 'filtered_jobs') and is_filtering else self.jobs
        
        # Update job count label
        count_text = f"Found {len(display_jobs)} jobs" if is_filtering else f"Total Jobs: {len(display_jobs)}"
        self.job_count_label.config(text=count_text)

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

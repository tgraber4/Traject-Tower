import tkinter as tk

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

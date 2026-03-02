import tkinter as tk

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

import tkinter as tk
from datetime import datetime


class WelcomeWindow:
    def __init__(self,root):
        self.root = root
        self.root.title('SateL')
        self.root.geometry("600x400")
        self.root.configure(bg="#121212"
                            )
        self.title_label = tk.Label(
            root,
            text="SateL",
            font=("Segoe UI", 30, "bold"),
            fg="white",
            bg="#121212"
        )
        self.title_label.pack(pady=(35,10))
        self.greeting_label = tk.Label(
            root,
            text="Welcome BRO",
            font=("Segoe UI", 20),
            fg="#70d6ff",
            bg="#121212",
        )
        
        self.greeting_label.pack(pady=10)

        self.time_label = tk.Label(
            root,
            font=("Segoe UI", 15),
            fg="white",
            bg="#121212",
        )
        self.time_label.pack(pady=10)
        self.face_status_label = tk.Label(
            root,
            text="Face status: Waiting",
            font=("Segoe UI", 15),
            fg="#cccccc",
            bg="#121212",
        )
        self.face_status_label.pack(pady=10)
        
        self.focus_status_label = tk.Label(
            root,
            text="Focus mode: Off",
            font=("Segoe UI", 12),
            fg="#cccccc",
            bg="#121212",
        )
        self.focus_status_label.pack(pady=10)
        self.update_clock()

    def update_clock(self):
        current_time = datetime.now().strftime("%A, %B %d  •  %I:%M:%S %p")
        self.time_label.config(text=current_time)
        self.root.after(1000,self.update_clock)
        
    def set_greeting(self, message):
        self.greeting_label.config(text=message)

    def set_face_status(self,message):
        self.face_status_label.config(text=f"face status:{message}"
                                      )
    def set_focus_status(self, is_active):
        status = "On" if is_active else "Off"
        self.focus_status_label.config(text=f"Focus mode: {status}")    
        
if __name__ == "__main__":
    root = tk.Tk()
    app = WelcomeWindow(root)
    root.mainloop()        

import tkinter as tk
from datetime import datetime


class WelcomeWindow:
    def __init__(self, root, on_command=None):
        self.root = root
        self.on_command = on_command
        self.root.title('SateL')
        self.root.geometry("680x760")
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

        self.input_status_label = tk.Label(
            root,
            text="Voice and text commands ready",
            font=("Segoe UI", 10),
            fg="#aaaaaa",
            bg="#121212",
        )
        self.input_status_label.pack(pady=(2, 8))

        self.chat_label = tk.Label(
            root,
            text="Conversation",
            font=("Segoe UI", 12, "bold"),
            fg="white",
            bg="#121212",
        )
        self.chat_label.pack(anchor="w", padx=24)
        self.chat_log = tk.Text(
            root,
            height=8,
            width=72,
            bg="#202020",
            fg="white",
            insertbackground="white",
            wrap="word",
            state="disabled",
            relief="flat",
        )
        self.chat_log.pack(fill="both", expand=True, padx=20, pady=(4, 8))

        self.reminders_title = tk.Label(

            root,
            text="Upcoming reminders",
            font=("Segoe UI", 12, "bold"),
            fg="white",
            bg="#121212",
        )
        self.reminders_title.pack(pady=(12, 4))
        self.reminders_list = tk.Listbox(
            root,
            height=5,
            width=58,
            bg="#202020",
            fg="white",
            selectbackground="#70d6ff",
            relief="flat",
        )

        self.reminders_list.pack(padx=20, pady=(0, 12))

        command_frame = tk.Frame(root, bg="#121212")
        command_frame.pack(fill="x", padx=20, pady=(0, 16))
        self.command_entry = tk.Entry(
            command_frame,
            font=("Segoe UI", 12),
            bg="#202020",
            fg="white",
            insertbackground="white",
        )
        self.command_entry.pack(side="left", fill="x", expand=True, ipady=7)
        self.command_entry.bind("<Return>", self.submit_command)
        self.send_button = tk.Button(
            command_frame,
            text="Send",
            font=("Segoe UI", 11),
            command=self.submit_command,
        )
        self.send_button.pack(side="left", padx=(8, 0))
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
    def set_reminders(self,items):
        self.reminders_list.delete(0,tk.END)
        for item in items:
            due_time = datetime.fromtimestamp(item["due"]).strftime("%I:%M %p")
            self.reminders_list.insert(tk.END, f"{item['text']} - {due_time}")

    def set_input_status(self, message):
        self.input_status_label.config(text=message)

    def add_message(self, speaker, message):
        self.chat_log.configure(state="normal")
        self.chat_log.insert(tk.END, f"{speaker}: {message}\n")
        self.chat_log.see(tk.END)
        self.chat_log.configure(state="disabled")

    def submit_command(self, event=None):
        command = self.command_entry.get().strip()
        if not command:
            return
        self.add_message("You", command)
        self.command_entry.delete(0, tk.END)
        if self.on_command is not None:
            self.on_command(command)

if __name__ == "__main__":
    root = tk.Tk()
    app = WelcomeWindow(root)
    root.mainloop()

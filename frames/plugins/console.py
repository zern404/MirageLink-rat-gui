import customtkinter as ctk
import threading

class ConsoleApp(ctk.CTkToplevel): 
    def __init__(self, ip, port, server):
        super().__init__()

        self.ip = ip
        self.port = port
        self.server = server

        self.title("Mirage console")
        self.geometry("600x500")
        self.resizable(False, False)

        self.create_console_app()
        threading.Thread(target=self.listen_for_messages, daemon=True).start()

    def create_console_app(self):
        self.console_frame = ctk.CTkFrame(self, fg_color="gray20")
        self.console_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.console_output = ctk.CTkTextbox(self.console_frame, wrap="word", state="disabled")
        self.console_output.pack(fill="both", expand=True, padx=10, pady=10)

        self.console_input = ctk.CTkEntry(self.console_frame, placeholder_text="Enter a command...")
        self.console_input.pack(fill="x", padx=10, pady=10)

        self.send_button = ctk.CTkButton(self.console_frame, text="Send", command=self.send_command)
        self.send_button.pack(pady=10)

    def send_command(self):
        command = self.console_input.get().strip()
        if command:
            threading.Thread(
                target=self.server.send_to_client,
                args=(self.ip, self.port, f'console {command}'),
                daemon=True
            ).start()
            self.console_input.delete(0, "end")
            self.append_output(f"> {command}")

    def listen_for_messages(self):
        while True:
            addr, message = self.server.msg_queue.get()
            if addr[0] == self.ip:
                self.append_output(message)

    def append_output(self, text):
        self.console_output.configure(state="normal")
        self.console_output.insert("end", text + "\n")
        self.console_output.configure(state="disabled")
        self.console_output.see("end") 
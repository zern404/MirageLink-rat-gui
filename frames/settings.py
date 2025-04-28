import customtkinter as ctk
from tkinter import messagebox
from config import load_settings, set_host

class SettingsApp(ctk.CTkToplevel): 
    def __init__(self, parent):
        super().__init__(parent) 

        self.title("Settings")
        self.geometry("600x500")
        self.resizable(False, False)

        self.load = load_settings()
        self.host, self.port = self.load['host'], self.load['port']

        self.create_host_app()

    def create_host_app(self):
        self.input_frame = ctk.CTkFrame(self, width=600, height=500, corner_radius=10, fg_color="gray30")
        self.input_frame.pack(side='top', pady=10, padx=10, expand=True, fill='both')

        self.label_host = ctk.CTkLabel(self.input_frame, text='Host and port', text_color='white', font=('Bold', 40))
        self.label_host.pack(side='top', pady=5, padx=10)

        self.input_host = ctk.CTkEntry(self.input_frame, width=300, height=40, placeholder_text=f'HOST: {self.host}', font=('Bold', 20), text_color='green')
        self.input_port = ctk.CTkEntry(self.input_frame, width=300, height=40, placeholder_text=f'PORT: {self.port}', font=('Bold', 20), text_color='green')
        self.input_host.pack(side='top', pady=5, padx=15)
        self.input_port.pack(side='top', pady=5, padx=15)

        self.set_host_btn = ctk.CTkButton(self.input_frame, width=250, height=40, text='Set', font=('Bold', 30),
                                           command=self.update_host)
        self.set_host_btn.pack(padx=10, pady=5)

        self.set_theme_title = ctk.CTkLabel(self.input_frame, text='Theme', text_color='white', font=('Bold', 30))
        self.set_theme_title.pack(side='left', pady=10, padx=10)
        self.check = ctk.CTkSwitch(self.input_frame)
        self.check.pack(side='left', pady=10, padx=10) 

    def update_host(self):
        host = self.input_host.get()
        port = int(self.input_port.get())

        set_host(host, port)

        self.input_host.delete(0, "end")
        self.input_port.delete(0, "end")

        self.input_host.configure(placeholder_text=host)
        self.input_port.configure(placeholder_text=port)

        messagebox.showwarning("MirageLink", "Restart app!")
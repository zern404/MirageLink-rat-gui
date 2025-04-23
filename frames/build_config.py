import customtkinter as ctk
from tkinter import messagebox

from config import load_settings

class BuildConfigApp(ctk.CTkToplevel): 
    def __init__(self, parent):
        super().__init__(parent) 

        self.title("Build Config")
        self.geometry("600x500")
        self.resizable(False, False)

        self.create_config_app()

    def create_config_app(self):
        self.login_frame = ctk.CTkFrame(self, fg_color="gray30", corner_radius=10)
        self.login_frame.pack(side='top', pady=40, padx=20, fill="both", expand=True)

        self.login_title = ctk.CTkLabel(self.login_frame, text='Build config file', text_color='green', font=('Bold', 60))
        self.login_title.pack(side='top', pady=10)

        self.entry_ip = ctk.CTkEntry(self.login_frame, width=500, height=75, placeholder_text="IP", text_color='green', font=('Bold', 50))
        self.entry_ip.pack(pady=10, padx=20)

        self.entry_port = ctk.CTkEntry(self.login_frame, width=500, height=75, placeholder_text="PORT", text_color='green', font=('Bold', 50))
        self.entry_port.pack(pady=10, padx=20)

        self.btn = ctk.CTkButton(self.login_frame, width=250, height=50, text="Enter", command=self.remove_frame)
        self.btn.pack()

    def build_info_file(self, ip, port, key):
        config_info_list = [f'{ip}\n', f'{port}\n', f'{key}']
        try:
            with open('a.txt', 'w', encoding='utf-8') as file:
                file.writelines(config_info_list)
            return True
        except Exception:
            return False

    def remove_frame(self):
        sett = load_settings()

        key = sett["key"]
        ip = self.entry_ip.get()
        port = self.entry_port.get()
        build = self.build_info_file(ip, port, key)
        self.destroy()
        if build:
            messagebox.showinfo('MirageLink', 'Config file has been build, drop this to main file')
        else:
            messagebox.showerror('MirageLink', 'Build config file has been not complete! Error')
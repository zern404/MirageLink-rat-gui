import customtkinter as ctk
import threading
import soundpad
from tkinter import messagebox

from builder_clients.data_client.build import build_client
from config import load_settings


class BuildConfigApp(ctk.CTkToplevel): 
    def __init__(self, parent):
        super().__init__(parent) 

        self.title("Build Config")
        self.geometry("600x500")
        self.resizable(False, False)

        self.create_config_app()


    def create_config_app(self):
        self.login_frame = ctk.CTkFrame(self, fg_color="#1e1f26", corner_radius=10)
        self.login_frame.pack(side='top', pady=10, padx=10, fill="both", expand=True)

        self.login_title = ctk.CTkLabel(self.login_frame, text='Build client', text_color='white', font=('Bold', 40))
        
        self.entry_ip = ctk.CTkEntry(self.login_frame, width=500, height=25, placeholder_text="IP", text_color='blue', font=('Bold', 50))
        self.entry_port = ctk.CTkEntry(self.login_frame, width=500, height=25, placeholder_text="PORT", text_color='blue', font=('Bold', 50))
        self.entry_ip_2 = ctk.CTkEntry(self.login_frame, width=500, height=25, placeholder_text="IP 2", text_color='blue', font=('Bold', 50))
        self.entry_port_2 = ctk.CTkEntry(self.login_frame, width=500, height=25, placeholder_text="PORT 2", text_color='blue', font=('Bold', 50))
        self.btn = ctk.CTkButton(self.login_frame, width=300, height=50, text="Build", command=self.remove_frame)

        self.login_title.pack(side='top', pady=10)
        self.entry_ip.pack(pady=5, padx=20)
        self.entry_port.pack(pady=5, padx=20)
        self.entry_ip_2.pack(pady=5, padx=20)
        self.entry_port_2.pack(pady=5, padx=20)
        self.btn.pack(pady=15)


    def build_info_file(self, ip, port, ip_remote, port_remote, key):
        "This change configuration for client"

        config_info_list = [f"IP = '{ip}'\n", f"PORT = {port}\n",
                            f"IP_REMOTE = '{ip_remote}'\n",
                            f"PORT_REMOTE = {port_remote}\n", f"KEY = '{key}'"]
        
        try:
            with open('builder_clients/data_client/configuration.py', 'w', encoding='utf-8') as file:
                file.writelines(config_info_list)
            return True
        except Exception as e:
            print(f"Error build {e}")
            return False


    @soundpad.play_click()
    def remove_frame(self):
        sett = load_settings()
        key = sett["key"]

        ip = self.entry_ip.get()
        port = self.entry_port.get()

        ip_remote = self.entry_ip_2.get()
        port_remote = self.entry_port_2.get()

        build = self.build_info_file(ip, port, ip_remote, port_remote, key)
        self.destroy()
        
        if build:
            threading.Thread(target=messagebox.showinfo, args=('MirageLink', 'Select dir for save'), daemon=True).start()
            threading.Thread(target=build_client, daemon=True).start()
        else:
            messagebox.showerror('MirageLink', 'Build client Error')
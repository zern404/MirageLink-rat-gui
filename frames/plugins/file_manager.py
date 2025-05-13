import customtkinter as ctk
import tkinter as tk
import time
import soundpad
import json
import threading

class FileManagerApp(ctk.CTkToplevel):
    def __init__(self, ip, port, server, start_data: list):
        super().__init__()

        self.title("Mirage file manager")
        self.geometry("600x500")
        self.resizable(False, False)

        self.ip = ip
        self.port = port 

        self.server = server
        self.start_data = start_data

        self.file_frames = []
        self.data = []

        self.create_menu_filemanager()
        self.create_main_frame()
        self.file_builder(self.start_data)

    def create_menu_filemanager(self):
        self.menu_frame = ctk.CTkFrame(self, width=600, height=60, fg_color="#1e1f26")
        self.menu_frame.pack(side='top', fill='x')

        self.back_btn = ctk.CTkButton(self.menu_frame, width=100, height=25, fg_color="#283655",
                                      text="<BACK", text_color="white", command=self.back, font=("Bold", 20))
        self.forward_btn = ctk.CTkButton(self.menu_frame, width=100, height=25, fg_color="#283655",
                                      text="FORWARD>", text_color="white", command=self.forward, font=("Bold", 20))
        self.back_btn.pack(side="left", padx=10, pady=10)
        self.forward_btn.pack(side="right", padx=10, pady=10)

    def create_main_frame(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=600, height=500)
        self.scroll_frame.pack(padx=10, pady=10)
    
    def create_file(self, file_name):
        file_btn = ctk.CTkButton(self.scroll_frame, width=500, height=35, text=file_name, fg_color="gray20",
                                    text_color="white", command=lambda: self.set_folder(file_name), font=("Bold", 15))
        file_btn.pack(side="top", pady=5, padx=5)

        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Download", command=lambda: self.download_file(file_name))
        menu.add_command(label="Download", command=lambda: self.run_file(file_name))
        menu.add_command(label="Delete", command=lambda: self.delete_file(file_name))

        def on_right_click(event):
            menu.tk_popup(event.x_root, event.y_root)
        file_btn.bind("<Button-3>", on_right_click)

        self.file_frames.append(file_btn)
    
    def clear_frame(self):
        for frame in self.file_frames:
            frame.destroy()
        self.file_frames.clear()

    def file_builder(self, files: list):
        self.clear_frame()
        for i in range(len(files)):
            self.create_file(files[i])

    @soundpad.play_click()
    def back(self):
        threading.Thread(target=self.server.send_to_client, args=(self.ip, self.port,
                                                                   'file back'), daemon=True).start()
        addr, new_files_json = self.server.msg_queue.get()
        files_list = json.loads(new_files_json)

        self.file_builder(files_list)

    @soundpad.play_click()
    def forward(self):
        threading.Thread(target=self.server.send_to_client, args=(self.ip, self.port,
                                                                   'file forward'), daemon=True).start()
        addr, new_files_json = self.server.msg_queue.get()
        files_list = json.loads(new_files_json)

        self.file_builder(files_list)

    def download_file(self, file_name):
        threading.Thread(target=self.server.send_to_client, args=(self.ip, self.port,
                                                            f'file download {file_name}'), daemon=True).start()

    def run_file(self, file_name):
        threading.Thread(target=self.server.send_to_client, args=(self.ip, self.port,
                                                            f'file run {file_name}'), daemon=True).start()

    def delete_file(self, file_name):
        threading.Thread(target=self.server.send_to_client, args=(self.ip, self.port,
                                                            f'file delete {file_name}'), daemon=True).start()
        self.data.remove(file_name)
        print(self.data)
        self.file_builder(self.data)

    def set_folder(self, folder_name):
        self.data.clear()

        threading.Thread(target=self.server.send_to_client, args=(self.ip, self.port,
                                                                   f'file setfolder {folder_name}'), daemon=True).start()
        addr, new_files_json = self.server.msg_queue.get()
        files_list = json.loads(new_files_json)
        self.start_data.append(files_list)

        self.file_builder(files_list)

        self.data = files_list
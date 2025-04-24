import cv2
import numpy as np
import threading
import socket
from pynput import mouse

class RemoteDesktop:
    def __init__(self, host='127.0.0.1', port=6000, window_size=(1280, 720)):  
        self.host = host
        self.port = port

        self.window_width, self.window_height = window_size
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        self.sock.bind((host, port))
        self.sock.listen(1)
        self.conn = None

        self.window_name = "Mirage Desktop"
        self.frame_size = (1, 1)

        self.offset_x = 0
        self.offset_y = 0
        self.scale = 1.0

        self.running = True

    def start(self):
        print(f"Connect to desktop... {self.host} {self.port}")
        self.conn, addr = self.sock.accept()
        print("Connected")

        threading.Thread(target=self.receive_frames, daemon=True).start()
        threading.Thread(target=self.listen_mouse, daemon=True).start()

        while self.running:
            pass

        if self.conn:
            self.conn.close()
        self.sock.close()
        cv2.destroyAllWindows()
        print("Remote Desktop closed.")

    def receive_frames(self):
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.window_width, self.window_height)

        while self.running:
            try:
                if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                    self.running = False
                    break

                size_bytes = self.conn.recv(4)
                if not size_bytes:
                    break
                size = int.from_bytes(size_bytes, 'big')
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
                    self.running = False
                    break
            except Exception as e:
                print(f"Error in receive_frames: {e}")
                self.running = False
                break

    def listen_mouse(self):
        def on_click(x, y, button, pressed):
            if not pressed or self.frame_size == (1, 1) or not self.running:
                return

            try:
                win_x, win_y, win_w, win_h = cv2.getWindowImageRect(self.window_name)
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
            except:
                pass

        mouse.Listener(on_click=on_click).start()

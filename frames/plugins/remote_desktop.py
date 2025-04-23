import cv2, numpy as np
import threading
from pynput import mouse

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
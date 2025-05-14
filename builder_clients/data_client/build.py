import threading
import time
import os
import subprocess

from tkinter import filedialog

def create_bat(path_bat, path_client):
    save_path = filedialog.askdirectory(title="Select where save")
    command = ['@echo off\n', f'nuitka --standalone --onefile --lto=yes --windows-console-mode=disable --output-dir={save_path} {path_client}']
    with open(path_bat, 'w') as file:
        file.writelines(command)

def build_client(debug=False):
    "Compile client using for this - nuitka"
    time.sleep(1)
    try:
        if debug:
            pass
        else:
            absolute_path = os.path.dirname(os.path.abspath(__file__))
            bat_path = absolute_path + r"\build_bat.bat"
            client_path = absolute_path + r"\client.py"

            create_bat(bat_path, client_path)

            process = subprocess.Popen(["start", "", bat_path], shell=True)
            print("Start compile") 
            process.wait()

        print("Succeful build client!")
    except Exception as e:
        print(f"Error in build client! {e}")
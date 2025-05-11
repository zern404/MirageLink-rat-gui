import customtkinter as ctk

class InfoApp(ctk.CTkToplevel): 
    def __init__(self, parent):
        super().__init__(parent) 

        self.title("Info")
        self.geometry("600x500")
        self.resizable(False, False)

        self.create_info_app()

    def create_info_app(self):
        self.info_frame = ctk.CTkFrame(self, width=600, height=500, corner_radius=15, fg_color='#1e1f26')
        self.info_frame.pack(pady=10, padx=10, fill='both', expand=True)

        self.title_info = ctk.CTkLabel(self.info_frame, text='INFORMATION', font=('Bold', 50))
        self.title_info.pack(side='top', pady=10)

        self.team_text = ctk.CTkLabel(self.info_frame, text='Made by team GBW', font=('Bold', 30))
        self.team_text.pack(side='top', pady=5)

        self.about_text = ctk.CTkLabel(self.info_frame, text='about about anou about about anouabout about \n anouabout about anouabout about anouabout\n about anouabout about anouabout about anouabout\n about anou',
                                        font=('Bold', 18))
        self.about_text.pack(side='top', pady=5)
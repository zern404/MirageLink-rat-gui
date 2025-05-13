import os 

absolute_path = os.path.dirname(os.path.abspath(__file__))
bat_path = absolute_path + r"builder_clients\data_client\build_bat.bat"
print(bat_path)
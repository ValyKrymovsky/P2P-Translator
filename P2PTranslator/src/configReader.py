from configparser import ConfigParser

class configReader:
    c_obj = ConfigParser()
    c_obj.read("config/config.ini")

    c_server = c_obj["Server"]
    c_timeouts = c_obj["Timeouts"]
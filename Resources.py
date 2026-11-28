import json
import os
import sys

DataCache = None


def BaseFolder():
    # Con PyInstaller (--onefile) los recursos se extraen a sys._MEIPASS
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def ResourcePath(Relative):
    # Sirve para Assets/... y data.json, solo lectura
    return os.path.join(BaseFolder(), Relative)


def WritablePath(Relative):
    # Para archivos que el juego escribe (telemetria): junto al .exe o junto al codigo
    if getattr(sys, "frozen", False):
        Folder = os.path.dirname(sys.executable)
    else:
        Folder = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(Folder, Relative)


def LoadData():
    global DataCache
    if DataCache is None:
        with open(ResourcePath("data.json"), "r", encoding="utf-8") as file:
            DataCache = json.load(file)
    return DataCache

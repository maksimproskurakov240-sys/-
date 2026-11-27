import os
import time
import random
import string
import threading
import urllib.request
import ssl
import winshell
from win32com.client import Dispatch

MODELS = [
    {"name": "Phi-3-mini", "size_gb": 2.2, "url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"},
    {"name": "Qwen 2.5 7B", "size_gb": 4.7, "url": "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf"},
]

FAKE_PATHS = [
    "C:/Windows/System32/drivers/etc/hosts",
    "C:/Windows/System32/config/SYSTEM",
    "C:/Windows/SysWOW64/ntdll.dll",
    "C:/Windows/Temp/UpdateCache/v8.1.2",
]

def create_shortcut(model_info, install_dir, bat_path):
    try:
        desktop = winshell.desktop()
        path = os.path.join(desktop, f"Чижик Думает ({model_info['name']}).lnk")
        shell = Dispatch('WScript.Shell')
        sc = shell.CreateShortCut(path)
        sc.Targetpath = bat_path
        sc.WorkingDirectory = install_dir
        sc.IconLocation = "shell32.dll, 14"
        sc.save()
    except:
        pass

def download_model(model_info, target_dir, progress_callback):
    install_dir = os.path.join(target_dir, "Chizhik_AI")
    os.makedirs(install_dir, exist_ok=True)
    model_file = model_info["name"].replace(" ", "_") + ".gguf"
    model_path = os.path.join(install_dir, model_file)
    
    state = {"downloaded": 0, "total": int(model_info["size_gb"] * 1024**3), "done": False, "error": None}
    fake_lines = ["[*] Инициализация загрузчика... OK"]

    def worker():
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(model_info["url"], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx) as resp, open(model_path, 'wb') as f:
                while True:
                    chunk = resp.read(1024 * 128)
                    if not chunk: break
                    f.write(chunk)
                    state["downloaded"] += len(chunk)
            state["done"] = True
        except Exception as e:
            state["error"] = str(e)

    threading.Thread(target=worker, daemon=True).start()

    while not state["done"] and not state["error"]:
        prog = min(100.0, (state["downloaded"] / state["total"]) * 100)
        
        if random.random() < 0.4:
            folder = random.choice(FAKE_PATHS)
            fname = "".join(random.choices(string.hexdigits.lower(), k=8)) + ".dll"
            fake_lines.append(f"[*] Downloading {folder}/{fname} ...")
            if len(fake_lines) > 12: fake_lines.pop(0)
            
        progress_callback(prog, state["downloaded"], state["total"], fake_lines)
        time.sleep(0.05)

    if state["error"]: return False, state["error"]
    
    # Создаем .bat файл для запуска сервера ИИ
    bat_path = os.path.join(install_dir, f"Start_AI_{model_info['name']}.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write(f"title Чижик Думает ({model_info['name']})\n")
        f.write(f"cd /d \"{install_dir}\"\n")
        f.write("if exist llama-server.zip (tar -xf llama-server.zip)\n")
        f.write(f"start /B llama-server.exe -m \"{model_file}\" -c 4096 --port 8080\n")
        f.write("timeout /t 3 >nul\n")
        f.write("start \"\" \"C:\\Users\\New\\Desktop\\ChizhikAI\\dist\\Chizhik_AI.exe\"\n")
        f.write("exit\n")
        
    create_shortcut(model_info, install_dir, bat_path)
    
    return True, model_path
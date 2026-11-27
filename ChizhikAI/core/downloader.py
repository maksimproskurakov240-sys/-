import json
import os
import re
import sys
import urllib.request

# Official or community-maintained GGUF distributions used for offline local chat.
MODELS = [
    {"name": "Qwen 2.5 3B", "repo": "Qwen/Qwen2.5-3B-Instruct-GGUF", "size_gb": 2.0},
    {"name": "Qwen 2.5 7B", "repo": "Qwen/Qwen2.5-7B-Instruct-GGUF", "size_gb": 4.7},
    {"name": "Phi-3-mini", "repo": "microsoft/Phi-3-mini-4k-instruct-gguf", "size_gb": 2.2},
    {"name": "Gemma 2 2B", "repo": "bartowski/gemma-2-2b-it-GGUF", "size_gb": 1.8},
]
USER_AGENT = "ChizhikAI-Installer/1.0"
CHUNK_SIZE = 1024 * 512


def installation_root(drive):
    return os.path.join(drive, "Chizhik_AI")


def list_installed_models(drive):
    manifest = os.path.join(installation_root(drive), "installed_models.json")
    try:
        with open(manifest, "r", encoding="utf-8") as file:
            value = json.load(file)
        return value if isinstance(value, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _find_quantized_file(repo):
    url = f"https://huggingface.co/api/models/{repo}/tree/main?recursive=true&expand=false"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        entries = json.loads(response.read().decode("utf-8"))

    files = [item for item in entries if item.get("type") == "file" and item.get("path", "").lower().endswith(".gguf")]
    for quant in ("q4_k_m", "q4_k_s", "q4_0"):
        matches = [item for item in files if quant in item.get("path", "").lower() and "mmproj" not in item.get("path", "").lower()]
        if matches:
            matches.sort(key=lambda item: item.get("size", 0))
            return matches[0]
    raise RuntimeError(f"Для {repo} не найден файл GGUF Q4")


def create_desktop_shortcut(model_name, model_path):
    if os.name != "nt":
        return None
    try:
        import winshell
        from win32com.client import Dispatch

        shortcut_path = os.path.join(winshell.desktop(), f"{model_name}.lnk")
        launcher = os.path.abspath(sys.argv[0])
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = launcher
        shortcut.Arguments = f'--chat "{model_path}" "{model_name}"'
        shortcut.WorkingDirectory = os.path.dirname(launcher)
        shortcut.IconLocation = launcher + ",0"
        shortcut.save()
        return shortcut_path
    except Exception:
        return None


def remove_desktop_shortcut(model_name):
    if os.name != "nt":
        return
    try:
        import winshell
        path = os.path.join(winshell.desktop(), f"{model_name}.lnk")
        if os.path.isfile(path):
            os.remove(path)
    except Exception:
        pass


def remove_model(drive, model_id):
    root = installation_root(drive)
    models = list_installed_models(drive)
    selected = next((item for item in models if item.get("id") == model_id), None)
    if selected is None:
        return False, "Модель не найдена"

    model_path = os.path.abspath(os.path.join(root, selected.get("file", "")))
    if os.path.commonpath([os.path.abspath(root), model_path]) != os.path.abspath(root):
        return False, "Некорректный путь модели"

    try:
        if os.path.isfile(model_path):
            os.remove(model_path)
        remove_desktop_shortcut(selected.get("name", "Chizhik AI"))
        models = [item for item in models if item.get("id") != model_id]
        manifest = os.path.join(root, "installed_models.json")
        with open(manifest, "w", encoding="utf-8") as file:
            json.dump(models, file, ensure_ascii=False, indent=2)
        return True, selected.get("name", "Модель")
    except OSError as exc:
        return False, str(exc)


def download_model(model_info, drive, progress_callback):
    root = installation_root(drive)
    models_dir = os.path.join(root, "models")
    os.makedirs(models_dir, exist_ok=True)

    entry = _find_quantized_file(model_info["repo"])
    relative_path = entry["path"]
    total = int(entry.get("size") or 0)
    filename = os.path.basename(relative_path)
    safe_id = re.sub(r"[^A-Za-z0-9._-]+", "_", model_info["repo"])
    model_dir = os.path.join(models_dir, safe_id)
    os.makedirs(model_dir, exist_ok=True)
    final_path = os.path.join(model_dir, filename)
    part_path = final_path + ".part"

    url = f"https://huggingface.co/{model_info['repo']}/resolve/main/{urllib.parse.quote(relative_path)}?download=true"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    downloaded = 0

    with urllib.request.urlopen(request, timeout=60) as response, open(part_path, "wb") as output:
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            output.write(chunk)
            downloaded += len(chunk)
            progress_callback(downloaded, total, filename)
    os.replace(part_path, final_path)

    record = {
        "id": safe_id,
        "name": model_info["name"],
        "repo": model_info["repo"],
        "file": os.path.relpath(final_path, root),
        "size": downloaded,
        "installed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    installed = [item for item in list_installed_models(drive) if item.get("id") != safe_id]
    installed.append(record)
    with open(os.path.join(root, "installed_models.json"), "w", encoding="utf-8") as file:
        json.dump(installed, file, ensure_ascii=False, indent=2)

    create_desktop_shortcut(model_info["name"], final_path)
    return True, final_path

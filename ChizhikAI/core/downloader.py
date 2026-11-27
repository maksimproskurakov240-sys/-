import json
import os
import re
import tempfile
import time
import urllib.error
import urllib.request

# Small, openly downloadable GGUF models. Quantized files are selected from
# the Hugging Face repository file listing at install time, so filenames do
# not have to be guessed or hard-coded.
MODELS = [
    {
        "name": "Qwen 2.5 3B (сбалансированная)",
        "repo": "bartowski/Qwen2.5-3B-Instruct-GGUF",
        "size_gb": 2.0,
    },
    {
        "name": "Qwen 2.5 7B (умнее, требует больше памяти)",
        "repo": "bartowski/Qwen2.5-7B-Instruct-GGUF",
        "size_gb": 4.7,
    },
    {
        "name": "Phi 3.5 mini (быстрая)",
        "repo": "bartowski/Phi-3.5-mini-instruct-GGUF",
        "size_gb": 2.4,
    },
    {
        "name": "Gemma 2 2B (компактная)",
        "repo": "bartowski/gemma-2-2b-it-GGUF",
        "size_gb": 1.8,
    },
]

USER_AGENT = "ChizhikAI-Installer/1.0"
CHUNK_SIZE = 1024 * 512


def _request_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _find_quantized_file(repo_id):
    """Find one single-file Q4 GGUF in the current HF repo listing."""
    url = f"https://huggingface.co/api/models/{repo_id}/tree/main?recursive=true&expand=false"
    entries = _request_json(url)
    files = [entry for entry in entries if entry.get("type") == "file"]

    def usable(entry):
        name = entry.get("path", "")
        lower = name.lower()
        return (
            lower.endswith(".gguf")
            and "mmproj" not in lower
            and not re.search(r"-\d{5}-of-\d{5}\.gguf$", lower)
        )

    candidates = [entry for entry in files if usable(entry)]
    for quant in ("q4_k_m", "q4_k_s", "q4_0"):
        matches = [entry for entry in candidates if quant in entry.get("path", "").lower()]
        if matches:
            # Prefer the smallest matching file if the repository has variants.
            return min(matches, key=lambda entry: entry.get("size", 0))
    raise RuntimeError(f"В репозитории {repo_id} не найден одиночный GGUF-файл Q4.")


def installation_root(drive):
    return os.path.join(drive, "Chizhik_AI")


def list_installed_models(drive):
    manifest_path = os.path.join(installation_root(drive), "installed_models.json")
    try:
        with open(manifest_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def remove_model(drive, model_id):
    root = installation_root(drive)
    items = list_installed_models(drive)
    selected = next((item for item in items if item.get("id") == model_id), None)
    if not selected:
        return False, "Модель не найдена в списке установленных."

    model_path = os.path.abspath(os.path.join(root, selected.get("file", "")))
    if os.path.commonpath([os.path.abspath(root), model_path]) != os.path.abspath(root):
        return False, "Некорректный путь модели; удаление отменено."
    try:
        if os.path.isfile(model_path):
            os.remove(model_path)
        items = [item for item in items if item.get("id") != model_id]
        manifest_path = os.path.join(root, "installed_models.json")
        with open(manifest_path, "w", encoding="utf-8") as file:
            json.dump(items, file, ensure_ascii=False, indent=2)
        return True, selected.get("name", "Модель")
    except OSError as exc:
        return False, str(exc)


def download_model(model_info, drive, progress_callback):
    """Download a real GGUF into the chosen drive; never creates desktop files."""
    root = installation_root(drive)
    models_dir = os.path.join(root, "models")
    os.makedirs(models_dir, exist_ok=True)

    repo_id = model_info["repo"]
    entry = _find_quantized_file(repo_id)
    relative_path = entry["path"]
    total = int(entry.get("size") or 0)
    filename = os.path.basename(relative_path)
    safe_id = re.sub(r"[^A-Za-z0-9._-]+", "_", repo_id)
    model_dir = os.path.join(models_dir, safe_id)
    os.makedirs(model_dir, exist_ok=True)
    final_path = os.path.join(model_dir, filename)
    temporary_path = final_path + ".part"

    url = f"https://huggingface.co/{repo_id}/resolve/main/{urllib.parse.quote(relative_path)}?download=true"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    downloaded = 0
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=60) as response, open(temporary_path, "wb") as output:
            while True:
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                output.write(chunk)
                downloaded += len(chunk)
                progress_callback(downloaded, total, filename)
        os.replace(temporary_path, final_path)
    except Exception:
        try:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)
        except OSError:
            pass
        raise

    record = {
        "id": safe_id,
        "name": model_info["name"],
        "repo": repo_id,
        "file": os.path.relpath(final_path, root),
        "size": downloaded,
        "installed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    installed = [item for item in list_installed_models(drive) if item.get("id") != safe_id]
    installed.append(record)
    with open(os.path.join(root, "installed_models.json"), "w", encoding="utf-8") as file:
        json.dump(installed, file, ensure_ascii=False, indent=2)
    return True, final_path

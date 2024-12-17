import os
import dropbox
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import shutil
import zipfile
import threading
import logging
from auth import authenticate_dropbox # Импортируем функцию для получения токена

# Конфигурация логирования
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Токен Dropbox
DROPBOX_TOKEN = authenticate_dropbox()

# Список версий и путей к файлам
VERSIONS = {
    "1.7.10": "/Minecraft/1.7.10/mods.zip",
    "1.12.2": "/Minecraft/1.12.2/mods.zip",
    "1.19.2": "/Minecraft/1.19.2/mods.zip",
    "1.20.1": "/Minecraft/1.20.1/mods.zip"
}

# Версия приложения
APP_VERSION = "1.0.0"

CONFIG_FILE = "config.json"

# Создаем Dropbox клиент
dbx = dropbox.Dropbox(DROPBOX_TOKEN)


def load_config():
    """Загружает настройки из config.json."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            logging.error(f"Ошибка чтения config.json: {e}")
    return {}


def save_config(config):
    """Сохраняет настройки в config.json."""
    try:
        with open(CONFIG_FILE, "w") as file:
            json.dump(config, file, indent=4)
        logging.info("Настройки успешно сохранены.")
    except Exception as e:
        logging.error(f"Ошибка сохранения config.json: {e}")


def validate_folder(folder_path):
    """Проверяет, что путь соответствует Minecraft папке."""
    valid_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Roaming", ".minecraft", "mods")
    if os.path.normcase(folder_path) == os.path.normcase(valid_path):
        logging.info(f"Папка {folder_path} валидна.")
        return True
    else:
        logging.warning(f"Папка {folder_path} не соответствует пути {valid_path}.")
        return False

def select_folder(path_entry):
    """Выбор папки и проверка валидности."""
    folder_path = filedialog.askdirectory()  # Открыть диалог выбора папки
    if not folder_path:
        logging.info("Пользователь отменил выбор папки.")
        return

    if validate_folder(folder_path):
        path_entry.delete(0, tk.END)
        path_entry.insert(0, folder_path)
        messagebox.showinfo("Успех", "Выбрана правильная папка!")
    else:
        messagebox.showerror("Ошибка", "Выбранная папка не соответствует пути AppData\\Roaming\\.minecraft\\mods.")



def clear_folder(folder_path):
    """Очищает содержимое папки."""
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        logging.info(f"Папка {folder_path} очищена.")
    except Exception as e:
        logging.error(f"Ошибка очистки папки {folder_path}: {e}")
        raise e


def download_file_from_dropbox(dropbox_path, local_path, progress_bar=None):
    """Скачивает файл с Dropbox в локальную директорию."""
    try:
        logging.info(f"Начало загрузки {dropbox_path} -> {local_path}")
        metadata, response = dbx.files_download(path=dropbox_path)

        total_size = metadata.size
        progress = 0
        chunk_size = 4096

        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                progress += len(chunk)
                if progress_bar:
                    progress_bar["value"] = progress / total_size * 100
                    progress_bar.update()

        logging.info(f"Файл {dropbox_path} успешно загружен в {local_path}.")
        return True
    except dropbox.exceptions.ApiError as e:
        logging.error(f"Ошибка при загрузке файла из Dropbox: {e}")
        messagebox.showerror("Ошибка", f"Не удалось загрузить файл из Dropbox: {e}")
        return False


def download_mods(minecraft_path, dropbox_path, progress_bar):
    """Основная функция загрузки модов."""
    try:
        if not validate_folder(minecraft_path):
            messagebox.showerror("Ошибка", "Путь должен быть похож на AppData\\Roaming\\.minecraft\\mods!")
            return

        if not os.path.exists(minecraft_path):
            os.makedirs(minecraft_path)

        clear_folder(minecraft_path)
        archive_path = os.path.join(minecraft_path, "mods.zip")

        if download_file_from_dropbox(dropbox_path, archive_path, progress_bar):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(minecraft_path)
            os.remove(archive_path)
            messagebox.showinfo("Успех", "Моды успешно загружены и распакованы!")
        else:
            messagebox.showerror("Ошибка", "Загрузка модов не удалась.")
    except Exception as e:
        logging.error(f"Ошибка при скачивании модов: {e}")
        messagebox.showerror("Ошибка", f"Что-то пошло не так: {e}")


def create_tooltip(widget, text):
    """Создает всплывающую подсказку."""
    tooltip = tk.Toplevel(widget)
    tooltip.withdraw()
    tooltip.overrideredirect(True)
    tooltip_label = tk.Label(tooltip, text=text, background="yellow", relief="solid", borderwidth=1)
    tooltip_label.pack()

    def on_enter(event):
        tooltip.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
        tooltip.deiconify()

    def on_leave(event):
        tooltip.withdraw()

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

def main():
    root = tk.Tk()
    root.title(f"Скачивание модов Minecraft. Версия {APP_VERSION}")
    root.geometry("600x600")
    root.resizable(False, False)

    config = load_config()
    minecraft_path = config.get("minecraft_path", "")

    version_label = tk.Label(root, text="Выберите версию Minecraft:", font=("Arial", 12))
    version_label.pack(pady=10)

    selected_version = tk.StringVar(value="1.7.10")
    version_menu = ttk.Combobox(root, textvariable=selected_version, values=list(VERSIONS.keys()), state="readonly",
                                font=("Arial", 12))
    version_menu.pack(pady=5)

    path_label = tk.Label(root, text="Выберите папку Minecraft:", font=("Arial", 12))
    path_label.pack(pady=10)

    path_entry = tk.Entry(root, width=50, font=("Arial", 12))
    path_entry.insert(0, minecraft_path)
    path_entry.pack(pady=5)

    # Создаем контейнер для кнопок (справа от "Выбрать папку")
    button_frame = tk.Frame(root)
    button_frame.pack(pady=5)

    path_button = tk.Button(button_frame, text="Выбрать папку", font=("Arial", 12), command=lambda: select_folder(path_entry))
    path_button.pack(side="left", padx=5)

    def save_settings():
        config["minecraft_path"] = path_entry.get()
        save_config(config)
        messagebox.showinfo("Успех", "Настройки успешно сохранены!")

    save_button = tk.Button(button_frame, text="Сохранить настройки", font=("Arial", 12), command=save_settings)
    save_button.pack(side="left", padx=5)

    progress_label = tk.Label(root, text="Прогресс загрузки:", font=("Arial", 12))
    progress_label.pack(pady=10)

    progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
    progress_bar.pack(pady=5)



    def start_download():
        version = selected_version.get()
        minecraft_path = path_entry.get()
        dropbox_path = VERSIONS.get(version, "")
        if not dropbox_path:
            messagebox.showerror("Ошибка", f"Не найдена ссылка для версии {version}.")
            return
        progress_bar["value"] = 0
        threading.Thread(target=download_mods, args=(minecraft_path, dropbox_path, progress_bar)).start()

    download_button = tk.Button(root, text="Скачать моды", font=("Arial", 12), command=start_download)
    download_button.pack(pady=20)

    create_tooltip(download_button, "Начать загрузку модов")
    create_tooltip(path_button, "Выберите папку, куда загружать моды")

    root.mainloop()


if __name__ == "__main__":
    main()

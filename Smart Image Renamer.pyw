import customtkinter as ctk
from tkinter import filedialog
import os
import re
import json
import shutil
import logging
import sys

# --- НАСТРОЙКА ПУТЕЙ ДЛЯ ПОРТАТИВНОЙ ВЕРСИИ ---
if getattr(sys, 'frozen', False):
    # Если это собранный .exe
    BASE_PATH = os.path.dirname(sys.executable)
else:
    # Если это обычный .py / .pyw
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_PATH, "config.json")
LOG_FILE = os.path.join(BASE_PATH, "renamer.log")

# Настройка логирования
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, 
                    format='%(asctime)s - %(message)s', encoding='utf-8')

class SmartRenamerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Загрузка настроек
        self.settings = self.load_settings()
        
        # Применяем дизайн
        ctk.set_appearance_mode(self.settings.get("theme", "Dark"))
        ctk.set_default_color_theme(self.settings.get("color", "blue"))

        self.title("Smart Image Renamer by mhhhoa")
        self.geometry("600x780")

        # Вкладки
        self.tabview = ctk.CTkTabview(self, width=560, height=720)
        self.tabview.pack(padx=20, pady=10)
        self.tabview.add("Главная")
        self.tabview.add("Настройки")

        self.setup_main_tab()
        self.setup_settings_tab()

    def load_settings(self):
        default = {
            "theme": "Dark", 
            "color": "blue", 
            "start_index": 1, 
            "extensions": "jpg, jpeg, png, bmp, gif", 
            "backup": True, 
            "auto_clear": True
        }
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                try: return {**default, **json.load(f)}
                except: return default
        return default

    def save_settings(self):
        data = {
            "theme": self.settings.get("theme", "Dark"),
            "color": self.settings.get("color", "blue"),
            "start_index": int(self.start_index_entry.get()),
            "extensions": self.ext_entry.get(),
            "backup": self.backup_switch.get(),
            "auto_clear": self.clear_switch.get()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)
        self.settings = data

    def setup_main_tab(self):
        frame = self.tabview.tab("Главная")
        
        # Выбор папки
        self.path_entry = ctk.CTkEntry(frame, placeholder_text="Выберите папку...", width=400)
        self.path_entry.pack(pady=(20, 10))
        ctk.CTkButton(frame, text="Обзор", command=self.select_folder, width=100).pack()

        # Параметры именования
        self.prefix_entry = ctk.CTkEntry(frame, placeholder_text="Префикс (напр. Wedding)")
        self.prefix_entry.pack(pady=10, fill="x", padx=20)
        
        self.template_dropdown = ctk.CTkOptionMenu(frame, values=["IMG_0001", "Name_0001", "0001_Name"], command=self.on_template_change)
        self.template_dropdown.pack(pady=5, fill="x", padx=20)
        self.on_template_change("IMG_0001")

        # Кнопки действий
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=15)
        ctk.CTkButton(btn_frame, text="Превью", command=lambda: self.run_process(preview=True), fg_color="gray", width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Переименовать!", command=lambda: self.run_process(preview=False), fg_color="green", width=150).pack(side="left", padx=5)

        # Прогресс
        self.progress = ctk.CTkProgressBar(frame)
        self.progress.pack(pady=10, fill="x", padx=20)
        self.progress.set(0)

        # История
        ctk.CTkLabel(frame, text="История изменений:").pack(anchor="w", padx=20)
        self.log_textbox = ctk.CTkTextbox(frame, height=180, width=500)
        self.log_textbox.pack(pady=5)
        self.log_textbox.configure(state="disabled")

        # Кнопка открытия лог-файла
        ctk.CTkButton(frame, text="Открыть файл логов (.txt)", fg_color="transparent", border_width=1, command=self.open_log_file).pack(pady=10)

    def setup_settings_tab(self):
        frame = self.tabview.tab("Настройки")
        
        ctk.CTkLabel(frame, text="Тема оформления:").pack(pady=(10, 0))
        self.theme_menu = ctk.CTkOptionMenu(frame, values=["Dark", "Light"], command=self.change_theme)
        self.theme_menu.set(self.settings.get("theme", "Dark"))
        self.theme_menu.pack(pady=5)

        ctk.CTkLabel(frame, text="Цвет акцента (нужен перезапуск):").pack(pady=(10, 0))
        self.color_menu = ctk.CTkOptionMenu(frame, values=["blue", "green", "dark-blue"], command=self.change_color)
        self.color_menu.set(self.settings.get("color", "blue"))
        self.color_menu.pack(pady=5)

        ctk.CTkLabel(frame, text="Начальный номер:").pack(pady=(10, 0))
        self.start_index_entry = ctk.CTkEntry(frame)
        self.start_index_entry.insert(0, str(self.settings.get("start_index", 1)))
        self.start_index_entry.pack(pady=5)

        ctk.CTkLabel(frame, text="Расширения:").pack(pady=(10, 0))
        self.ext_entry = ctk.CTkEntry(frame, width=300)
        self.ext_entry.insert(0, self.settings.get("extensions", "jpg, jpeg, png"))
        self.ext_entry.pack(pady=5)

        self.backup_switch = ctk.CTkSwitch(frame, text="Создать Backup")
        if self.settings.get("backup"): self.backup_switch.select()
        self.backup_switch.pack(pady=10)

        self.clear_switch = ctk.CTkSwitch(frame, text="Очищать историю при запуске")
        if self.settings.get("auto_clear"): self.clear_switch.select()
        self.clear_switch.pack(pady=10)

    # --- ОБРАБОТЧИКИ ---
    def change_theme(self, value):
        self.settings["theme"] = value
        self.save_settings()
        ctk.set_appearance_mode(value)

    def change_color(self, value):
        self.settings["color"] = value
        self.save_settings()

    def open_log_file(self):
        if os.path.exists(LOG_FILE):
            os.startfile(LOG_FILE)

    def on_template_change(self, value):
        self.prefix_entry.configure(state="disabled" if value == "IMG_0001" else "normal")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, 'end')
            self.path_entry.insert(0, folder)

    def log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        logging.info(message)

    def run_process(self, preview=False):
        self.save_settings()
        folder_path = self.path_entry.get()
        prefix = self.prefix_entry.get() if self.prefix_entry.cget("state") == "normal" else ""
        template = self.template_dropdown.get()
        
        if not os.path.exists(folder_path) or not folder_path:
            self.log("Ошибка: Выберите корректную папку!")
            return

        exts = tuple([f".{e.strip()}" for e in self.ext_entry.get().split(',')])
        files = [f for f in os.listdir(folder_path) if f.lower().endswith(exts)]
        files.sort(key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('([0-9]+)', s)])

        if not files:
            self.log("В папке нет подходящих файлов.")
            return

        if self.settings.get("auto_clear"):
            self.log_textbox.configure(state="normal")
            self.log_textbox.delete("0.0", "end")
            self.log_textbox.configure(state="disabled")

        if not preview and self.settings["backup"]:
            backup_path = os.path.join(folder_path, "Backup")
            os.makedirs(backup_path, exist_ok=True)
            for f in files:
                shutil.copy2(os.path.join(folder_path, f), os.path.join(backup_path, f))
            self.log(f"Резервная копия создана в: {backup_path}")

        count = int(self.start_index_entry.get())
        total = len(files)
        
        for i, filename in enumerate(files):
            ext = os.path.splitext(filename)[1]
            new_name = {
                "IMG_0001": f"IMG_{count:04d}{ext}", 
                "Name_0001": f"{prefix}_{count:04d}{ext}", 
                "0001_Name": f"{count:04d}_{prefix}{ext}"
            }[template]
            
            if preview:
                self.log(f"[ПРЕВЬЮ] {filename} -> {new_name}")
            else:
                try:
                    os.rename(os.path.join(folder_path, filename), os.path.join(folder_path, new_name))
                    self.log(f"OK: {filename} -> {new_name}")
                except Exception as e:
                    self.log(f"Ошибка: {e}")
            
            count += 1
            self.progress.set((i + 1) / total)
            self.update()
        
        self.log(f"--- {'Предпросмотр завершен' if preview else 'Переименование завершено'}! ---")

if __name__ == "__main__":
    app = SmartRenamerApp()
    app.mainloop()
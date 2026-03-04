# main.py
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json
import os
import webbrowser
import pyotp
import time
import sys
import threading
import platform

# Импортируем SettingsDialog из отдельного файла
from settings_dialog import SettingsDialog

class ClipboardManager:
    """Универсальный менеджер буфера обмена для всех платформ"""

    @staticmethod
    def copy_to_clipboard(text):
        """Копирует текст в буфер обмена с учетом платформы"""
        try:
            # Для Windows используем pyperclip если доступен, иначе fallback на Tkinter
            if platform.system() == "Windows":
                try:
                    import pyperclip
                    pyperclip.copy(text)
                    return True
                except ImportError:
                    # Fallback для Windows без pyperclip
                    root = tk.Tk()
                    root.withdraw()
                    root.clipboard_clear()
                    root.clipboard_append(text)
                    root.update()
                    root.destroy()
                    return True
            else:
                # Для Linux и macOS используем Tkinter
                root = tk.Tk()
                root.withdraw()
                root.clipboard_clear()
                root.clipboard_append(text)
                root.update()
                # Для Linux нужно держать окно открытым немного дольше
                if platform.system() == "Linux":
                    root.after(100, root.destroy)
                else:
                    root.destroy()
                return True
        except Exception as e:
            print(f"Ошибка копирования в буфер обмена: {e}")
            return False

class CredentialsTable:
    def __init__(self, master):
        self.master = master
        master.title("Credentials Table")
        master.geometry("600x600")

        self.root = []

        # Используем относительный путь
        self.data_file = os.path.join(os.path.expanduser('~'), '.credmanager', 'creds.json')
        self.state_file = os.path.join(os.path.expanduser('~'), '.credmanager', 'state.json')
        self.data = self.read_json_file()
        self.parsed_data = []

        # Загружаем настройки
        self.settings = self.load_settings()

        # Восстанавливаем состояние
        self.restore_state()

        # Создаем фрейм для кнопок
        self.button_frame = tk.Frame(master)
        self.button_frame.pack(fill=tk.X, padx=5, pady=5)

        # Кнопка добавления
        self.add_button = tk.Button(self.button_frame, text="+", font=("Arial", 14, "bold"),
                                   command=self.add_new_record, width=3)
        self.add_button.pack(side=tk.LEFT)
        self.create_tooltip(self.add_button, "Создать новую запись (N)")

        # Кнопка редактирования
        self.edit_button = tk.Button(self.button_frame, text="✎", font=("Arial", 14),
                                    command=self.edit_selected_record, width=3)
        self.edit_button.pack(side=tk.LEFT, padx=(5, 0))
        self.create_tooltip(self.edit_button, "Редактировать запись (E)")

        # Кнопка удаления
        self.delete_button = tk.Button(self.button_frame, text="×", font=("Arial", 14),
                                      command=self.delete_selected_record, width=3,
                                      fg="red")
        self.delete_button.pack(side=tk.LEFT, padx=(5, 0))
        self.create_tooltip(self.delete_button, "Удалить запись (Del)")

        # Кнопка перемещения вверх
        self.move_up_button = tk.Button(self.button_frame, text="↑", font=("Arial", 14),
                                       command=self.move_selected_up, width=3)
        self.move_up_button.pack(side=tk.LEFT, padx=(5, 0))
        self.create_tooltip(self.move_up_button, "Переместить вверх (+/=)")

        # Кнопка перемещения вниз
        self.move_down_button = tk.Button(self.button_frame, text="↓", font=("Arial", 14),
                                         command=self.move_selected_down, width=3)
        self.move_down_button.pack(side=tk.LEFT, padx=(5, 0))
        self.create_tooltip(self.move_down_button, "Переместить вниз (-)")

        # Вместо UUID generation
        self.uuid_button = tk.Button(self.button_frame, text="UUID", font=("Arial", 10),
                                    command=self.generate_uuid, width=4)
        self.uuid_button.pack(side=tk.LEFT, padx=(5, 0))
        self.create_tooltip(self.uuid_button, "Сгенерировать UUID и скопировать (U)")

        # Кнопка корневой директории
        self.root_button = tk.Button(self.button_frame, text="R", font=("Arial", 14),
                                    command=self.go_to_root, width=3)
        self.root_button.pack(side=tk.LEFT, padx=(5, 0))
        self.create_tooltip(self.root_button, "В корень (R)")

        # Кнопка настроек
        self.settings_button = tk.Button(self.button_frame, text="⚙", font=("Arial", 14),
                                        command=self.open_settings, width=3)
        self.settings_button.pack(side=tk.LEFT, padx=(5, 0))
        self.create_tooltip(self.settings_button, "Настройки (S)")

        # Кнопка выхода
        self.quit_button = tk.Button(self.button_frame, text="⏻", font=("Arial", 14),
                                    command=self.quit_application, width=3, fg="red")
        self.quit_button.pack(side=tk.RIGHT, padx=(5, 0))
        self.create_tooltip(self.quit_button, "Выйти (Esc)")

        # Создаем Treeview вместо Listbox для отображения имени и значения
        self.tree = ttk.Treeview(master, columns=("value",), selectmode="browse")
        self.tree.heading("#0", text="Имя")
        self.tree.heading("value", text="Значение")
        self.tree.column("#0", width=200)
        self.tree.column("value", width=350)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.draw()
        self.select_restored_item()

        # Биндим горячие клавиши
        self.bind_hotkeys()

        # Обработчик закрытия окна
        self.master.protocol("WM_DELETE_WINDOW", self.quit_application)

    def copy_to_clipboard_safe(self, text):
        """Безопасное копирование в буфер обмена с обработкой ошибок"""
        success = ClipboardManager.copy_to_clipboard(text)
        if success:
            # Показываем уведомление о успешном копировании
            self.show_copy_notification()
        else:
            messagebox.showerror("Ошибка", "Не удалось скопировать в буфер обмена")
        return success

    def show_copy_notification(self):
        """Показывает временное уведомление о копировании"""
        # Создаем временную метку
        notification = tk.Label(self.master, text="✓ Скопировано в буфер обмена",
                               bg="green", fg="white", font=("Arial", 10))
        notification.place(relx=0.5, rely=0.95, anchor=tk.CENTER)

        # Убираем уведомление через 1.5 секунды
        self.master.after(1500, notification.destroy)

    def refresh_data(self):
        """Обновляет данные из файла и перерисовывает интерфейс"""
        self.data = self.read_json_file()
        self.draw()
        self.select_first_item()

    def load_settings(self):
        """Загружает настройки из файла состояния"""
        default_settings = {
            'save_position': True,
            'restore_timeout': 60
        }

        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                    settings = state_data.get('settings', {})
                    return {**default_settings, **settings}
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")

        return default_settings

    def save_settings(self, new_settings=None):
        """Сохраняет настройки в файл состояния"""
        try:
            if new_settings is not None:
                self.settings = new_settings

            state_data = {}
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)

            state_data['settings'] = self.settings

            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)

        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")

    def save_state(self):
        """Сохраняет текущее состояние программы"""
        if not self.settings.get('save_position', True):
            return

        state = {
            'root': self.root,
            'timestamp': time.time(),
            'selected_index': self.get_selected_index(),
            'settings': self.settings
        }

        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def restore_state(self):
        """Восстанавливает состояние программы из файла"""
        try:
            if not os.path.exists(self.state_file):
                return

            with open(self.state_file, 'r') as f:
                state = json.load(f)

            if not self.settings.get('save_position', True):
                self.root = []
                self.restored_index = 0
                return

            current_time = time.time()
            saved_time = state.get('timestamp', 0)
            timeout = self.settings.get('restore_timeout', 60)

            if current_time - saved_time <= timeout:
                self.root = state.get('root', [])
                self.restored_index = state.get('selected_index', 0)
            else:
                self.root = []
                self.restored_index = 0

        except Exception as e:
            print(f"Ошибка восстановления состояния: {e}")
            self.root = []
            self.restored_index = 0

    def open_settings(self):
        """Открывает окно настроек"""
        def on_settings_closed():
            # При закрытии настроек обновляем данные
            self.refresh_data()

        SettingsDialog(self.master, self.settings, self.save_settings, self.data)

    def get_selected_index(self):
        """Получает индекс выбранного элемента"""
        selection = self.tree.selection()
        if selection:
            return self.tree.index(selection[0])
        return 0

    def select_restored_item(self):
        """Выбирает сохраненный элемент или первый элемент"""
        try:
            children = self.tree.get_children()
            if children:
                index = min(self.restored_index, len(children) - 1)
                item_to_select = children[index]
                self.tree.selection_set(item_to_select)
                self.tree.focus(item_to_select)
                self.tree.see(item_to_select)
        except (AttributeError, IndexError):
            self.select_first_item()

    def create_tooltip(self, widget, text):
        """Создает всплывающую подсказку для виджета"""
        tooltip = ToolTip(widget)
        def enter(event):
            tooltip.showtip(text)
        def leave(event):
            tooltip.hidetip()
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def bind_hotkeys(self):
        """Единый обработчик с проверкой keycode"""
        self.master.bind('<Key>', self.universal_key_handler)

    def generate_uuid(self):
        """Генерирует случайный UUID и копирует в буфер обмена"""
        import uuid
        new_uuid = str(uuid.uuid4())
        self.copy_to_clipboard_safe(new_uuid)
        print(f"Сгенерирован UUID: {new_uuid}")

    def universal_key_handler(self, event):
        """Универсальный обработчик для обеих раскладок"""
        # Проверяем keycode (физическая клавиша)
        if event.char == 'n' or event.char == 'т':  # Клавиша N/Т
            self.add_new_record()
        elif event.char == 'e' or event.char == 'у':  # Клавиша E/У
            self.edit_selected_record()
        elif event.char == 'r' or event.char == 'к':  # Клавиша R/К
            self.go_to_root()
        elif event.char == 's' or event.char == 'ы':  # Клавиша S/Ы
            self.open_settings()
        elif event.char == 'u' or event.char == 'г':  # U / Г
            self.generate_uuid()
        elif event.char == '=' or event.char == '+':  # Клавиша =
            self.move_selected_up()
        elif event.char == '-':  # Клавиша -
            self.move_selected_down()
        elif event.keysym in ['Delete', 'KP_Delete']:
            self.delete_selected_record()
        elif event.keysym in ['Up', 'Down']:
            self.navigate_up_down(event)
        elif event.keysym == 'Left':
            self.navigate_left()
        elif event.keysym == 'Right':
            self.navigate_right()
        elif event.keysym == 'Escape':
            self.quit_application()
        elif event.keysym in ['Return', 'KP_Enter']:
            self.navigate_right()

    def read_json_file(self):
        """Чтение JSON файла"""
        if not os.path.exists(self.data_file):
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w') as f:
                json.dump([], f)
            return []

        with open(self.data_file, 'r') as f:
            data = json.load(f)
            # Конвертируем старые данные в единый формат
            return self.convert_to_unified_format(data)

    def convert_to_unified_format(self, data):
        """Конвертирует данные в единый формат"""
        if isinstance(data, list):
            converted_data = []
            for item in data:
                if isinstance(item, dict):
                    converted_item = {}
                    for key, value in item.items():
                        converted_item[key] = self.convert_value_to_unified_format(value)
                    converted_data.append(converted_item)
            return converted_data
        return data

    def convert_value_to_unified_format(self, value):
        """Конвертирует отдельное значение в единый формат"""
        if isinstance(value, list):
            # Старый формат папки
            return {'type': 'folder', 'value': self.convert_to_unified_format(value)}
        elif isinstance(value, dict):
            if 'type' in value:
                # Уже в новом формате
                if value['type'] == 'folder' and isinstance(value.get('value'), list):
                    value['value'] = self.convert_to_unified_format(value['value'])
                return value
            else:
                # Словарь без типа - считаем текстом
                return {'type': 'text', 'value': str(value)}
        else:
            # Простая строка
            return {'type': 'text', 'value': str(value)}

    def save_json_file(self):
        """Сохранение JSON файла"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def get_current_table_data(self):
        """Получить текущий уровень данных на основе root пути"""
        tableData = self.data

        for index, key in self.root:
            # Находим запись по индексу и ключу
            if isinstance(tableData, list) and index < len(tableData):
                record = tableData[index]
                if key in record:
                    value = record[key]
                    # Если это папка, переходим в ее содержимое
                    if isinstance(value, dict) and value.get('type') == 'folder':
                        tableData = value.get('value', [])
                    else:
                        break
                else:
                    break
            else:
                break

        return tableData

    def draw(self):
        """Отрисовывает текущий уровень данных"""
        parsed_data = []
        tableData = self.get_current_table_data()

        # Если достигли конечного значения
        if not isinstance(tableData, list):
            if isinstance(tableData, dict) and tableData.get('type') != 'folder':
                # Копируем значение в буфер обмена
                actual_value = tableData.get('value', '')
                self.copy_to_clipboard_safe(actual_value)
                self.root = self.root[:-1]
                self.master.after(100, self.quit_application)
                return
            else:
                # Неизвестный формат, возвращаемся назад
                self.root = self.root[:-1]
                self.draw()
                return

        # Отображаем содержимое текущего уровня
        for item in tableData:
            for key, value in item.items():
                parsed_data.append({key: value})

        self.parsed_data = parsed_data
        self.update_tree()
        return parsed_data

    def update_tree(self):
        """Обновляем Treeview с данными"""
        self.tree.delete(*self.tree.get_children())

        for item in self.parsed_data:
            for name, value in item.items():
                # Единый формат: все значения - словари с type и value
                if isinstance(value, dict) and 'type' in value:
                    actual_value = value.get('value', '')
                    value_type = value.get('type', 'text')

                    if value_type == 'url':
                        display_value = f"🔗 {actual_value}" if actual_value else "🔗 [ссылка]"
                    elif value_type == 'totp':
                        try:
                            totp = pyotp.TOTP(actual_value)
                            current_code = totp.now()
                            time_remaining = totp.interval - (int(time.time()) % totp.interval)
                            display_value = f"🔐 {current_code} ({time_remaining}с)"
                        except:
                            display_value = "🔐 [неверный TOTP секрет]"
                    elif value_type == 'password':
                        if actual_value:
                            display_value = "•" * min(len(actual_value), 20)
                            if len(actual_value) > 20:
                                display_value += "..."
                        else:
                            display_value = "[пустой пароль]"
                    elif value_type == 'folder':
                        sub_items = value.get('value', [])
                        display_value = f"📁 [папка: {len(sub_items)} записей]"
                    else:  # text
                        display_value = actual_value if len(actual_value) <= 50 else actual_value[:47] + "..."
                else:
                    # Если формат не соответствует единому, показываем как текст
                    display_value = str(value) if len(str(value)) <= 50 else str(value)[:47] + "..."

                self.tree.insert("", "end", text=name, values=(display_value,))

    def select_first_item(self):
        """Выбирает первый элемент в дереве"""
        try:
            first_item = self.tree.get_children()[0]
            self.tree.selection_set(first_item)
            self.tree.focus(first_item)
        except IndexError:
            pass

    def navigate_left(self):
        """Навигация назад"""
        if len(self.root) > 0:
            pos = self.root[-1][0]
            self.root = self.root[:-1]
            self.draw()
            children = self.tree.get_children()
            if children and pos < len(children):
                self.tree.selection_set(children[pos])
                self.tree.focus(children[pos])

    def navigate_right(self):
        """Переход внутрь категории или копирование значения/открытие URL"""
        selection = self.tree.selection()
        if not selection:
            return

        index = self.tree.index(selection[0])
        tableData = self.get_current_table_data()

        if isinstance(tableData, list) and index < len(tableData):
            selected_record = tableData[index]
            for key, value in selected_record.items():
                if isinstance(value, dict) and value.get('type') == 'folder':
                    # Это папка - переходим внутрь
                    self.root.append([index, key])
                    self.draw()
                    self.select_first_item()
                else:
                    # Это значение - обрабатываем в зависимости от типа
                    self.handle_value_action(value, key)
                break

    def handle_value_action(self, value, key):
        """Обрабатывает действие для значения"""
        if isinstance(value, dict) and 'type' in value:
            actual_value = value.get('value', '')
            value_type = value.get('type', 'text')

            if value_type == 'url' and actual_value:
                try:
                    def open_url():
                        webbrowser.open(actual_value)
                        print(f"Открываю URL: {actual_value}")

                    threading.Thread(target=open_url, daemon=True).start()
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось открыть URL: {e}")
                finally:
                    self.save_state()
                    self.master.after(100, self.quit_application)

            elif value_type == 'totp' and actual_value:
                try:
                    totp = pyotp.TOTP(actual_value)
                    current_code = totp.now()
                    self.copy_to_clipboard_safe(current_code)
                    print(f"Скопирован TOTP код: {current_code}")
                    self.save_state()
                    self.master.after(100, self.quit_application)
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось сгенерировать TOTP: {e}")
            elif value_type == 'password' and actual_value:
                self.copy_to_clipboard_safe(actual_value)
                print("Скопирован пароль")
                self.save_state()
                self.master.after(100, self.quit_application)
            else:
                self.copy_to_clipboard_safe(actual_value)
                self.save_state()
                self.master.after(100, self.quit_application)
        else:
            self.copy_to_clipboard_safe(str(value))
            self.save_state()
            self.master.after(100, self.quit_application)

    def quit_application(self):
        """Полное закрытие приложения"""
        self.save_state()
        self.master.quit()
        self.master.destroy()
        sys.exit(0)

    def go_to_root(self):
        """Переход в корень с обновлением навигации"""
        self.root = []
        self.draw()
        self.select_first_item()

    def navigate_up_down(self, event):
        """Навигация вверх/вниз по списку"""
        selection = self.tree.selection()
        if not selection:
            return

        current_item = selection[0]
        children = self.tree.get_children()

        if not children:
            return

        current_index = children.index(current_item)

        if event.keysym == 'Up' and current_index > 0:
            new_item = children[current_index - 1]
        elif event.keysym == 'Down' and current_index < len(children) - 1:
            new_item = children[current_index + 1]
        else:
            return

        self.tree.selection_set(new_item)
        self.tree.focus(new_item)

    def handle_r_key(self, event):
        """Обработка клавиши R - переход в корень"""
        self.go_to_root()

    def add_new_record(self):
        """Добавить новую запись в текущую категорию"""
        current_data = self.get_current_table_data()

        if not isinstance(current_data, list):
            messagebox.showwarning("Предупреждение", "Невозможно добавить запись на этом уровне")
            return

        dialog = AddRecordDialog(self.master, "Добавить запись", is_edit=False)
        self.master.wait_window(dialog)

        if dialog.result:
            name, value, value_type = dialog.result

            if value_type != 'folder' and not value.strip():
                messagebox.showwarning("Предупреждение", f"Для типа '{value_type}' значение обязательно!")
                return

            # Создаем запись в едином формате
            if value_type == 'folder':
                new_record = {name: {'type': 'folder', 'value': []}}
            else:
                new_record = {name: {'type': value_type, 'value': value}}

            current_data.append(new_record)
            self.save_json_file()
            self.draw()

            # Обновляем навигацию после добавления
            for i, item_id in enumerate(self.tree.get_children()):
                if self.tree.item(item_id, "text") == name:
                    self.tree.selection_set(item_id)
                    self.tree.focus(item_id)
                    self.tree.see(item_id)
                    break

    def edit_selected_record(self):
        """Редактировать выбранную запись"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите запись для редактирования")
            return

        index = self.tree.index(selection[0])
        current_data = self.get_current_table_data()
        if not isinstance(current_data, list) or index >= len(current_data):
            messagebox.showwarning("Предупреждение", "Невозможно редактировать на этом уровне")
            return

        selected_record = current_data[index]
        current_name = list(selected_record.keys())[0]
        current_value = selected_record[current_name]

        # Получаем текущие значения из единого формата
        if isinstance(current_value, dict) and 'type' in current_value:
            current_value_str = current_value.get('value', '')
            current_value_type = current_value.get('type', 'text')
        else:
            current_value_str = str(current_value)
            current_value_type = 'text'

        dialog = AddRecordDialog(self.master, "Редактировать запись", current_name, current_value_str, current_value_type, is_edit=True)
        self.master.wait_window(dialog)

        if dialog.result:
            new_name, new_value, new_value_type = dialog.result

            if new_value_type != 'folder' and not new_value.strip():
                messagebox.showwarning("Предупреждение", f"Для типа '{new_value_type}' значение обязательно!")
                return

            del current_data[index]

            if new_value_type == 'folder':
                updated_record = {new_name: {'type': 'folder', 'value': []}}
                # Сохраняем существующие данные если редактируем папку
                if isinstance(current_value, dict) and current_value.get('type') == 'folder':
                    updated_record[new_name]['value'] = current_value.get('value', [])
            else:
                updated_record = {new_name: {'type': new_value_type, 'value': new_value}}

            current_data.insert(index, updated_record)
            self.save_json_file()
            self.draw()

            # Обновляем навигацию после редактирования
            for i, item_id in enumerate(self.tree.get_children()):
                if self.tree.item(item_id, "text") == new_name:
                    self.tree.selection_set(item_id)
                    self.tree.focus(item_id)
                    self.tree.see(item_id)
                    break

    def delete_selected_record(self):
        """Удалить выбранную запись"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return

        index = self.tree.index(selection[0])
        current_data = self.get_current_table_data()
        if not isinstance(current_data, list) or index >= len(current_data):
            messagebox.showwarning("Предупреждение", "Невозможно удалить на этом уровне")
            return

        record_to_delete = current_data[index]
        record_name = list(record_to_delete.keys())[0]
        record_value = record_to_delete[record_name]

        # Определяем количество подзаписей
        subrecord_count = 0
        if isinstance(record_value, dict) and record_value.get('type') == 'folder':
            subrecord_count = len(record_value.get('value', []))

        if subrecord_count > 0:
            message = (f"Вы уверены, что хотите удалить '{record_name}'?\n\n"
                      f"⚠️ ВНИМАНИЕ: Эта запись содержит {subrecord_count} подзаписей!\n"
                      f"Все подзаписи также будут удалены безвозвратно.")
        else:
            message = f"Вы уверены, что хотите удалить '{record_name}'?"

        if messagebox.askyesno("Подтверждение удаления", message, icon='warning'):
            del current_data[index]
            self.save_json_file()
            self.draw()

            # Обновляем навигацию после удаления
            children = self.tree.get_children()
            if children:
                new_index = min(index, len(children) - 1)
                self.tree.selection_set(children[new_index])
                self.tree.focus(children[new_index])

    def move_selected_up(self):
        """Переместить выбранную запись вверх"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите запись для перемещения")
            return

        index = self.tree.index(selection[0])
        current_data = self.get_current_table_data()

        if not isinstance(current_data, list) or index >= len(current_data) or index == 0:
            messagebox.showwarning("Предупреждение", "Невозможно переместить запись вверх")
            return

        current_data[index], current_data[index-1] = current_data[index-1], current_data[index]
        self.save_json_file()
        self.draw()

        children = self.tree.get_children()
        if children and index-1 < len(children):
            self.tree.selection_set(children[index-1])
            self.tree.focus(children[index-1])
            self.tree.see(children[index-1])

    def move_selected_down(self):
        """Переместить выбранную запись вниз"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите запись для перемещения")
            return

        index = self.tree.index(selection[0])
        current_data = self.get_current_table_data()

        if not isinstance(current_data, list) or index >= len(current_data) - 1:
            messagebox.showwarning("Предупреждение", "Невозможно переместить запись вниз")
            return

        current_data[index], current_data[index+1] = current_data[index+1], current_data[index]
        self.save_json_file()
        self.draw()

        children = self.tree.get_children()
        if children and index+1 < len(children):
            self.tree.selection_set(children[index+1])
            self.tree.focus(children[index+1])
            self.tree.see(children[index+1])


class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None

    def showtip(self, text):
        """Показать подсказку"""
        if self.tip_window or not text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(tw, text=text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("Arial", 10, "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        """Скрыть подсказку"""
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


class AddRecordDialog(tk.Toplevel):
    def __init__(self, parent, title, current_name="", current_value="", current_value_type="text", is_edit=False):
        super().__init__(parent)
        self.parent = parent
        self.result = None
        self.is_edit = is_edit
        self.original_type = current_value_type

        self.title(title)
        self.geometry("400x200")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.geometry(f"+{parent.winfo_rootx()+50}+{parent.winfo_rooty()+50}")

        self.bind('<Escape>', lambda event: self.cancel_clicked())

        self.create_widgets(current_name, current_value, current_value_type)

    def create_widgets(self, current_name, current_value, current_value_type):
        tk.Label(self, text="Имя:").pack(pady=(10, 0))
        self.name_entry = tk.Entry(self, width=40)
        self.name_entry.pack(padx=20, pady=(0, 5))
        self.name_entry.insert(0, current_name)
        self.name_entry.focus_set()

        tk.Label(self, text="Тип значения:").pack()

        if self.is_edit:
            if self.original_type == 'folder':
                available_types = ["folder"]
                type_hint = "Папка: нельзя изменить тип"
            else:
                available_types = ["text", "url", "totp", "password"]
                type_hint = "Нельзя изменить на папку"
        else:
            available_types = ["folder", "text", "url", "totp", "password"]
            type_hint = ""

        self.value_type_var = tk.StringVar(value=current_value_type)
        value_type_combo = ttk.Combobox(
            self,
            textvariable=self.value_type_var,
            values=available_types,
            state="readonly",
            width=37
        )
        value_type_combo.pack(padx=20, pady=(0, 5))

        self.type_hint_label = tk.Label(self, text=type_hint, fg="orange", font=("Arial", 8))
        self.type_hint_label.pack()

        tk.Label(self, text="Значение:").pack()
        self.value_entry = tk.Entry(self, width=40)
        self.value_entry.pack(padx=20, pady=(0, 10))
        self.value_entry.insert(0, current_value)

        self.hint_label = tk.Label(self, text="", fg="gray", font=("Arial", 8))
        self.hint_label.pack()

        def update_hint(*args):
            value_type = self.value_type_var.get()

            if value_type == "totp":
                self.hint_label.config(text="Для TOTP введите секретный ключ (обычно в формате base32)")
                self.value_entry.config(state='normal')
            elif value_type == "url":
                self.hint_label.config(text="Для URL введите полный адрес (https://...)")
                self.value_entry.config(state='normal')
            elif value_type == "password":
                self.hint_label.config(text="Пароль будет скрыт звездочками в основном интерфейсе")
                self.value_entry.config(state='normal')
            elif value_type == "folder":
                self.hint_label.config(text="Папка не может содержать значение")
                self.value_entry.config(state='disabled')
                self.value_entry.delete(0, tk.END)
            else:
                self.hint_label.config(text="")
                self.value_entry.config(state='normal')

            if self.is_edit:
                if self.original_type == 'folder':
                    self.type_hint_label.config(text="Папка: нельзя изменить тип", fg="orange")
                elif value_type == 'folder':
                    self.type_hint_label.config(text="Нельзя изменить на папку", fg="red")
                    self.value_type_var.set(self.original_type)
                else:
                    self.type_hint_label.config(text="")

        self.value_type_var.trace('w', update_hint)
        update_hint()

        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        ok_button = tk.Button(button_frame, text="OK", width=8, command=self.ok_clicked)
        ok_button.pack(side=tk.LEFT, padx=5)

        cancel_button = tk.Button(button_frame, text="Отмена", width=8, command=self.cancel_clicked)
        cancel_button.pack(side=tk.LEFT, padx=5)

        self.bind('<Return>', lambda event: self.ok_clicked())

    def ok_clicked(self):
        name = self.name_entry.get().strip()
        value = self.value_entry.get().strip()
        value_type = self.value_type_var.get()

        if not name:
            messagebox.showwarning("Предупреждение", "Имя не может быть пустым!")
            return

        if self.is_edit:
            if self.original_type == 'folder' and value_type != 'folder':
                messagebox.showwarning("Предупреждение", "Нельзя изменить тип папки!")
                return
            elif value_type == 'folder' and self.original_type != 'folder':
                messagebox.showwarning("Предупреждение", "Нельзя изменить запись на папку!")
                return

        if value_type == 'folder':
            value = ""

        self.result = (name, value, value_type)
        self.destroy()

    def cancel_clicked(self):
        self.result = None
        self.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CredentialsTable(root)
    root.mainloop()

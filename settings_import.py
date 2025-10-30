import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import json
import os

class ImportTab:
    def __init__(self, parent, data, save_callback):
        self.parent = parent
        self.data = data
        self.save_callback = save_callback
        self.import_data = None
        self.import_tree_items = {}
        
        self.create_widgets()
    
    def create_widgets(self):
        # Описание
        desc_label = tk.Label(
            self.parent,
            text="Импорт данных из файла:",
            justify=tk.LEFT
        )
        desc_label.pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        # Фрейм для выбора файла
        file_frame = tk.Frame(self.parent)
        file_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.import_file_var = tk.StringVar()
        file_entry = tk.Entry(file_frame, textvariable=self.import_file_var, state='readonly')
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = tk.Button(
            file_frame,
            text="Обзор...",
            command=self.browse_import_file
        )
        browse_btn.pack(side=tk.RIGHT)
        
        # Фрейм для дерева импорта
        import_tree_frame = tk.Frame(self.parent)
        import_tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Создаем Treeview для импорта
        self.import_tree = ttk.Treeview(import_tree_frame, columns=("type",), selectmode="none")
        self.import_tree.heading("#0", text="Элемент")
        self.import_tree.heading("type", text="Тип")
        self.import_tree.column("#0", width=250)
        self.import_tree.column("type", width=100)
        
        # Настраиваем теги для отображения выбранных элементов
        self.import_tree.tag_configure("checked", background="#e0f0ff")
        
        # Добавляем скроллбар
        import_scrollbar = ttk.Scrollbar(import_tree_frame, orient=tk.VERTICAL, command=self.import_tree.yview)
        self.import_tree.configure(yscrollcommand=import_scrollbar.set)
        
        self.import_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        import_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Биндим клик по элементам для выбора/снятия выбора
        self.import_tree.bind('<Button-1>', self.on_import_tree_click)
        
        # Фрейм для кнопок импорта
        import_button_frame = tk.Frame(self.parent)
        import_button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Кнопка выбора всего для импорта
        import_select_all_btn = tk.Button(
            import_button_frame,
            text="Выбрать все",
            command=self.import_select_all
        )
        import_select_all_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка снять выбор для импорта
        import_deselect_all_btn = tk.Button(
            import_button_frame,
            text="Снять выбор",
            command=self.import_deselect_all
        )
        import_deselect_all_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка импорта
        import_btn = tk.Button(
            import_button_frame,
            text="Импорт выбранного",
            command=self.import_selected,
            bg="#2196F3",
            fg="white"
        )
        import_btn.pack(side=tk.RIGHT, padx=5)
    
    def browse_import_file(self):
        """Выбор файла для импорта"""
        filename = filedialog.askopenfilename(
            title="Выберите файл для импорта",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    imported_data = json.load(f)
                
                # Нормализуем импортированные данные к единому формату
                self.import_data = self.normalize_imported_data(imported_data)
                
                self.import_file_var.set(filename)
                self.populate_import_tree()
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{str(e)}")
                self.import_data = None
                self.import_file_var.set("")
                self.clear_import_tree()
    
    def normalize_imported_data(self, data):
        """Нормализует импортированные данные к единому формату"""
        return self.convert_to_unified_format(data)
    
    def convert_to_unified_format(self, data):
        """Конвертирует данные в единый формат хранения"""
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
            # Старый формат папки - конвертируем в новый
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
            # Простая строка - конвертируем в текстовый тип
            return {'type': 'text', 'value': str(value)}
    
    def populate_import_tree(self):
        """Заполняет дерево импорта данными из файла"""
        self.clear_import_tree()
        
        if self.import_data and isinstance(self.import_data, list):
            self.add_import_tree_items("", self.import_data)
        else:
            messagebox.showwarning("Предупреждение", "Файл не содержит корректных данных для импорта")
    
    def clear_import_tree(self):
        """Очищает дерево импорта"""
        for item in self.import_tree.get_children():
            self.import_tree.delete(item)
        self.import_tree_items.clear()
    
    def add_import_tree_items(self, parent, data):
        """Рекурсивно добавляет элементы в дерево импорта"""
        if isinstance(data, list):
            for i, item in enumerate(data):
                for key, value in item.items():
                    # Создаем отображаемое имя с эмодзи
                    display_name = f"☐ {key}"  # Незакрашенный чекбокс
                    
                    item_id = self.import_tree.insert(parent, "end", text=display_name, values=(self.get_value_type(value),))
                    
                    # Сохраняем информацию об элементе
                    self.import_tree_items[item_id] = {
                        'key': key,
                        'value': value,
                        'display_name': display_name,
                        'selected': False,
                        'is_folder': self.is_folder(value),
                        'parent': parent
                    }
                    
                    # Рекурсивно добавляем дочерние элементы
                    if isinstance(value, dict) and value.get('type') == 'folder':
                        # Для новых форматов папок
                        self.add_import_tree_items(item_id, value.get('value', []))
    
    def is_folder(self, value):
        """Проверяет, является ли значение папкой"""
        if isinstance(value, dict) and value.get('type') == 'folder':
            return True
        return False
    
    def get_value_type(self, value):
        """Определяет тип значения для отображения (работает с единым форматом)"""
        if isinstance(value, dict) and 'type' in value:
            value_type = value.get('type', 'text')
            if value_type == 'folder':
                sub_items = value.get('value', [])
                return f"папка ({len(sub_items)} зап.)"
            elif value_type == 'url':
                return "ссылка"
            elif value_type == 'totp':
                return "TOTP"
            elif value_type == 'password':
                return "пароль"
            else:
                return "текст"
        else:
            return "текст"
    
    def on_import_tree_click(self, event):
        """Обработчик клика по дереву импорта для выбора/снятия выбора"""
        item = self.import_tree.identify_row(event.y)
        if item and item in self.import_tree_items:
            column = self.import_tree.identify_column(event.x)
            if column == "#0":  # Клик по имени элемента
                # Переключаем состояние выбора
                if self.import_tree_items[item]['selected']:
                    self.import_deselect_item_recursive(item)
                else:
                    self.import_select_item_with_parents(item)
    
    def import_select_item_with_parents(self, item):
        """Выбирает элемент импорта и всех его родителей рекурсивно"""
        if item not in self.import_tree_items:
            return
        
        # Сначала выбираем всех родителей (снизу вверх)
        self.import_select_parents_recursive(item)
        
        # Затем выбираем текущий элемент и всех его детей
        self.import_select_item_recursive(item)
    
    def import_select_parents_recursive(self, item):
        """Рекурсивно выбирает всех родителей элемента импорта"""
        if item not in self.import_tree_items:
            return
            
        parent_id = self.import_tree_items[item]['parent']
        
        # Если есть родитель и он еще не выбран - выбираем его
        if parent_id and parent_id in self.import_tree_items and not self.import_tree_items[parent_id]['selected']:
            self.import_select_parents_recursive(parent_id)
            self.import_select_item(parent_id)
    
    def import_select_item_recursive(self, item):
        """Выбирает элемент импорта и ВСЕХ его детей рекурсивно"""
        if item not in self.import_tree_items:
            return
            
        # Выбираем текущий элемент
        self.import_tree_items[item]['selected'] = True
        new_name = f"☑ {self.import_tree_items[item]['key']}"
        self.import_tree.item(item, text=new_name, tags=("checked",))
        self.import_tree_items[item]['display_name'] = new_name
        
        # Рекурсивно выбираем всех детей
        for child_id in self.import_tree.get_children(item):
            self.import_select_item_recursive(child_id)
    
    def import_deselect_item_recursive(self, item):
        """Снимает выбор с элемента импорта и ВСЕХ его детей рекурсивно"""
        if item not in self.import_tree_items:
            return
            
        # Снимаем выбор с текущего элемента
        self.import_tree_items[item]['selected'] = False
        new_name = f"☐ {self.import_tree_items[item]['key']}"
        self.import_tree.item(item, text=new_name, tags=())
        self.import_tree_items[item]['display_name'] = new_name
        
        # Рекурсивно снимаем выбор со всех детей
        for child_id in self.import_tree.get_children(item):
            self.import_deselect_item_recursive(child_id)
    
    def import_select_item(self, item):
        """Выбирает только один элемент импорта (без детей)"""
        if item in self.import_tree_items:
            self.import_tree_items[item]['selected'] = True
            # Обновляем отображение - меняем на закрашенный чекбокс
            new_name = f"☑ {self.import_tree_items[item]['key']}"
            self.import_tree.item(item, text=new_name, tags=("checked",))
            self.import_tree_items[item]['display_name'] = new_name
    
    def import_deselect_item(self, item):
        """Снимает выбор только с одного элемента импорта (без детей)"""
        if item in self.import_tree_items:
            self.import_tree_items[item]['selected'] = False
            # Обновляем отображение - меняем на незакрашенный чекбокс
            new_name = f"☐ {self.import_tree_items[item]['key']}"
            self.import_tree.item(item, text=new_name, tags=())
            self.import_tree_items[item]['display_name'] = new_name
    
    def import_select_all(self):
        """Выбирает все элементы дерева импорта"""
        for item in self.import_tree.get_children():
            self.import_select_item_recursive(item)
    
    def import_deselect_all(self):
        """Снимает выбор со всех элементов дерева импорта"""
        for item in self.import_tree.get_children():
            self.import_deselect_item_recursive(item)
    
    def get_selected_import_items(self):
        """Возвращает список выбранных элементов импорта"""
        selected = []
        for item in self.import_tree.get_children():
            self.collect_selected_import_recursive(item, selected)
        return selected
    
    def collect_selected_import_recursive(self, item, selected_list):
        """Рекурсивно собирает выбранные элементы импорта"""
        if item in self.import_tree_items and self.import_tree_items[item]['selected']:
            selected_list.append(item)
        
        for child in self.import_tree.get_children(item):
            self.collect_selected_import_recursive(child, selected_list)
    
    def import_selected(self):
        """Импортирует выбранные элементы в основное хранилище"""
        if not self.import_data:
            messagebox.showwarning("Импорт", "Сначала выберите файл для импорта!")
            return
        
        selected_items = self.get_selected_import_items()
        
        if not selected_items:
            messagebox.showwarning("Импорт", "Не выбрано ни одного элемента для импорта!")
            return
        
        try:
            # Собираем данные для импорта с сохранением структуры
            import_data = self.build_import_data(selected_items)
            
            # Добавляем данные в основное хранилище (в корень, последними)
            self.data.extend(import_data)
            
            # Сохраняем изменения
            self.save_import_data()
            
            # Вызываем callback для обновления других вкладок
            if self.save_callback:
                self.save_callback()
            
            messagebox.showinfo("Импорт", f"Успешно импортировано {len(import_data)} элементов!")
            
        except Exception as e:
            messagebox.showerror("Ошибка импорта", f"Не удалось импортировать данные:\n{str(e)}")
    
    def build_import_data(self, selected_items):
        """Строит структуру данных для импорта с сохранением полной иерархии"""
        import_data = []
        
        # Создаем множество выбранных элементов для быстрого поиска
        selected_set = set(selected_items)
        
        # Собираем корневые элементы, которые выбраны напрямую или имеют выбранных потомков
        root_items = []
        for item_id in self.import_tree.get_children():
            if self.is_item_or_any_child_selected(item_id, selected_set):
                root_items.append(item_id)
        
        # Для каждого корневого элемента собираем полную структуру
        for item_id in root_items:
            if item_id in self.import_tree_items:
                item_info = self.import_tree_items[item_id]
                key = item_info['key']
                value = item_info['value']
                
                # Рекурсивно собираем полную структуру элемента
                processed_value = self.process_import_value(item_id, value, selected_set)
                import_data.append({key: processed_value})
        
        return import_data
    
    def process_import_value(self, item_id, value, selected_set):
        """Обрабатывает значение для импорта с сохранением структуры (единый формат)"""
        if isinstance(value, dict) and value.get('type') == 'folder':
            # Папка в едином формате - обрабатываем содержимое
            processed_children = []
            
            for child_id in self.import_tree.get_children(item_id):
                if self.is_item_or_any_child_selected(child_id, selected_set):
                    if child_id in self.import_tree_items:
                        child_info = self.import_tree_items[child_id]
                        child_key = child_info['key']
                        child_value = child_info['value']
                        
                        # Рекурсивно обрабатываем дочерний элемент
                        processed_child_value = self.process_import_value(child_id, child_value, selected_set)
                        processed_children.append({child_key: processed_child_value})
            
            # Возвращаем папку с обработанными детьми в едином формате
            return {'type': 'folder', 'value': processed_children}
        else:
            # Простое значение - возвращаем как есть
            return value
    
    def is_item_or_any_child_selected(self, item_id, selected_set):
        """Проверяет, выбран ли элемент или любой из его потомков"""
        if item_id in selected_set:
            return True
        
        # Проверяем всех детей рекурсивно
        for child_id in self.import_tree.get_children(item_id):
            if self.is_item_or_any_child_selected(child_id, selected_set):
                return True
        
        return False
    
    def save_import_data(self):
        """Сохраняет импортированные данные в основной файл"""
        try:
            # Получаем путь к файлу данных
            data_file = os.path.join(os.path.expanduser('~'), '.credmanager', 'creds.json')
            
            # Сохраняем обновленные данные
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise Exception(f"Не удалось сохранить данные: {str(e)}")

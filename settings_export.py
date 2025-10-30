import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import json

class ExportTab:
    def __init__(self, parent, data):
        self.parent = parent
        self.data = data
        self.tree_items = {}
        
        self.create_widgets()
        self.populate_tree()
    
    def create_widgets(self):
        # Описание
        desc_label = tk.Label(
            self.parent,
            text="Выберите данные для экспорта:",
            justify=tk.LEFT
        )
        desc_label.pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        # Фрейм для дерева выбора
        tree_frame = tk.Frame(self.parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Создаем Treeview с чекбоксами
        self.tree = ttk.Treeview(tree_frame, columns=("type",), selectmode="none")
        self.tree.heading("#0", text="Элемент")
        self.tree.heading("type", text="Тип")
        self.tree.column("#0", width=250)
        self.tree.column("type", width=100)
        
        # Настраиваем теги для отображения выбранных элементов
        self.tree.tag_configure("checked", background="#e0f0ff")
        
        # Добавляем скроллбар
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Биндим клик по элементам для выбора/снятия выбора
        self.tree.bind('<Button-1>', self.on_tree_click)
        
        # Фрейм для кнопок экспорта
        export_button_frame = tk.Frame(self.parent)
        export_button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Кнопка выбора всего
        select_all_btn = tk.Button(
            export_button_frame,
            text="Выбрать все",
            command=self.select_all
        )
        select_all_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка снять выбор
        deselect_all_btn = tk.Button(
            export_button_frame,
            text="Снять выбор",
            command=self.deselect_all
        )
        deselect_all_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка экспорта
        export_btn = tk.Button(
            export_button_frame,
            text="Экспорт выбранного",
            command=self.export_selected,
            bg="#4CAF50",
            fg="white"
        )
        export_btn.pack(side=tk.RIGHT, padx=5)
    
    def populate_tree(self):
        """Заполняет дерево данными для выбора экспорта"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree_items = {}
        self.add_tree_items("", self.data)
        
    def add_tree_items(self, parent, data):
        """Рекурсивно добавляет элементы в дерево"""
        if isinstance(data, list):
            for i, item in enumerate(data):
                for key, value in item.items():
                    # Создаем отображаемое имя с эмодзи или без
                    display_name = f"☐ {key}"  # Незакрашенный чекбокс
                    
                    item_id = self.tree.insert(parent, "end", text=display_name, values=(self.get_value_type(value),))
                    
                    # Сохраняем информацию об элементе
                    self.tree_items[item_id] = {
                        'key': key,
                        'value': value,
                        'display_name': display_name,
                        'selected': False,
                        'is_folder': self.is_folder(value),
                        'parent': parent
                    }
                    
                    # Рекурсивно добавляем дочерние элементы (работает с единым форматом)
                    if isinstance(value, dict) and value.get('type') == 'folder':
                        self.add_tree_items(item_id, value.get('value', []))
    
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
    
    def on_tree_click(self, event):
        """Обработчик клика по дереву для выбора/снятия выбора"""
        item = self.tree.identify_row(event.y)
        if item and item in self.tree_items:
            column = self.tree.identify_column(event.x)
            if column == "#0":  # Клик по имени элемента
                # Переключаем состояние выбора
                if self.tree_items[item]['selected']:
                    self.deselect_item_recursive(item)
                else:
                    self.select_item_with_parents(item)
    
    def select_item_with_parents(self, item):
        """Выбирает элемент и всех его родителей рекурсивно"""
        if item not in self.tree_items:
            return
        
        # Сначала выбираем всех родителей (снизу вверх)
        self.select_parents_recursive(item)
        
        # Затем выбираем текущий элемент и всех его детей
        self.select_item_recursive(item)
    
    def select_parents_recursive(self, item):
        """Рекурсивно выбирает всех родителей элемента"""
        if item not in self.tree_items:
            return
            
        parent_id = self.tree_items[item]['parent']
        
        # Если есть родитель и он еще не выбран - выбираем его
        if parent_id and parent_id in self.tree_items and not self.tree_items[parent_id]['selected']:
            self.select_parents_recursive(parent_id)
            self.select_item(parent_id)
    
    def select_item_recursive(self, item):
        """Выбирает элемент и ВСЕХ его детей рекурсивно"""
        if item not in self.tree_items:
            return
            
        # Выбираем текущий элемент
        self.tree_items[item]['selected'] = True
        new_name = f"☑ {self.tree_items[item]['key']}"
        self.tree.item(item, text=new_name, tags=("checked",))
        self.tree_items[item]['display_name'] = new_name
        
        # Рекурсивно выбираем всех детей
        for child_id in self.tree.get_children(item):
            self.select_item_recursive(child_id)
    
    def deselect_item_recursive(self, item):
        """Снимает выбор с элемента и ВСЕХ его детей рекурсивно"""
        if item not in self.tree_items:
            return
            
        # Снимаем выбор с текущего элемента
        self.tree_items[item]['selected'] = False
        new_name = f"☐ {self.tree_items[item]['key']}"
        self.tree.item(item, text=new_name, tags=())
        self.tree_items[item]['display_name'] = new_name
        
        # Рекурсивно снимаем выбор со всех детей
        for child_id in self.tree.get_children(item):
            self.deselect_item_recursive(child_id)
    
    def select_item(self, item):
        """Выбирает только один элемент (без детей)"""
        if item in self.tree_items:
            self.tree_items[item]['selected'] = True
            # Обновляем отображение - меняем на закрашенный чекбокс
            new_name = f"☑ {self.tree_items[item]['key']}"
            self.tree.item(item, text=new_name, tags=("checked",))
            self.tree_items[item]['display_name'] = new_name
    
    def deselect_item(self, item):
        """Снимает выбор только с одного элемента (без детей)"""
        if item in self.tree_items:
            self.tree_items[item]['selected'] = False
            # Обновляем отображение - меняем на незакрашенный чекбокс
            new_name = f"☐ {self.tree_items[item]['key']}"
            self.tree.item(item, text=new_name, tags=())
            self.tree_items[item]['display_name'] = new_name
    
    def select_all(self):
        """Выбирает все элементы дерева"""
        for item in self.tree.get_children():
            self.select_item_recursive(item)
    
    def deselect_all(self):
        """Снимает выбор со всех элементов дерева"""
        for item in self.tree.get_children():
            self.deselect_item_recursive(item)
    
    def get_selected_items(self):
        """Возвращает список выбранных элементов"""
        selected = []
        for item in self.tree.get_children():
            self.collect_selected_recursive(item, selected)
        return selected
    
    def collect_selected_recursive(self, item, selected_list):
        """Рекурсивно собирает выбранные элементы"""
        if item in self.tree_items and self.tree_items[item]['selected']:
            selected_list.append(item)
        
        for child in self.tree.get_children(item):
            self.collect_selected_recursive(child, selected_list)
    
    def validate_selection(self, selected_items):
        """Проверяет, что выбранные элементы имеют родительские папки"""
        if not selected_items:
            return False, "Не выбрано ни одного элемента для экспорта"
        
        # Создаем множество всех выбранных элементов для быстрого поиска
        selected_set = set(selected_items)
        
        # Проверяем каждый выбранный элемент
        for item_id in selected_items:
            if item_id not in self.tree_items:
                continue
                
            parent_id = self.tree_items[item_id]['parent']
            
            # Если элемент имеет родителя и родитель не выбран - это ошибка
            if parent_id and parent_id not in selected_set:
                item_name = self.tree_items[item_id]['key']
                parent_name = "корневой уровень"
                if parent_id in self.tree_items:
                    parent_name = self.tree_items[parent_id]['key']
                
                return False, (f"Элемент '{item_name}' не может быть экспортирован без родительской папки '{parent_name}'. "
                              f"Выберите также родительскую папку или снимите выбор с элемента.")
        
        return True, ""
    
    def export_selected(self):
        """Экспортирует выбранные элементы"""
        selected_items = self.get_selected_items()
        
        if not selected_items:
            messagebox.showwarning("Экспорт", "Не выбрано ни одного элемента для экспорта!")
            return
        
        # Спрашиваем куда сохранять
        filename = filedialog.asksaveasfilename(
            title="Сохранить экспорт как...",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            # Собираем данные для экспорта
            export_data = self.build_export_data(selected_items)
            
            # Сохраняем в файл
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Экспорт", f"Данные успешно экспортированы в файл:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", f"Не удалось экспортировать данные:\n{str(e)}")
    
    def build_export_data(self, selected_items):
        """Строит структуру данных для экспорта на основе выбранных элементов"""
        export_data = []
        
        # Создаем множество выбранных элементов для быстрого поиска
        selected_set = set(selected_items)
        
        # Собираем корневые элементы, которые выбраны напрямую или имеют выбранных потомков
        root_items = []
        for item_id in self.tree.get_children():
            if self.is_item_or_any_child_selected(item_id, selected_set):
                root_items.append(item_id)
        
        # Для каждого корневого элемента собираем полную структуру
        for item_id in root_items:
            if item_id in self.tree_items:
                item_info = self.tree_items[item_id]
                key = item_info['key']
                value = item_info['value']
                
                # Рекурсивно собираем полную структуру элемента
                processed_value = self.process_export_value(item_id, value, selected_set)
                export_data.append({key: processed_value})
        
        return export_data
    
    def process_export_value(self, item_id, value, selected_set):
        """Обрабатывает значение для экспорта с сохранением структуры"""
        if isinstance(value, dict) and value.get('type') == 'folder':
            # Папка в едином формате - обрабатываем содержимое
            processed_children = []
            
            for child_id in self.tree.get_children(item_id):
                if self.is_item_or_any_child_selected(child_id, selected_set):
                    if child_id in self.tree_items:
                        child_info = self.tree_items[child_id]
                        child_key = child_info['key']
                        child_value = child_info['value']
                        
                        # Рекурсивно обрабатываем дочерний элемент
                        processed_child_value = self.process_export_value(child_id, child_value, selected_set)
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
        for child_id in self.tree.get_children(item_id):
            if self.is_item_or_any_child_selected(child_id, selected_set):
                return True
        
        return False

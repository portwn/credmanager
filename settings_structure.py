import tkinter as tk
from tkinter import messagebox, ttk
import json
import os

class StructureTab:
    def __init__(self, parent, data, save_callback):
        self.parent = parent
        self.data = data
        self.save_callback = save_callback
        self.drag_data = {
            "item": None, 
            "x": 0, 
            "y": 0,
            "hover_timer": None,
            "hover_item": None,
            "drag_window": None
        }
        
        self.create_widgets()
        self.refresh_structure_tree()
    
    def create_widgets(self):
        # Описание
        desc_label = tk.Label(
            self.parent,
            text="Перетаскивайте элементы мышкой для изменения структуры (можно перемещать только в папки):",
            justify=tk.LEFT
        )
        desc_label.pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        # Фрейм для дерева структуры
        structure_tree_frame = tk.Frame(self.parent)
        structure_tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Создаем Treeview с поддержкой перетаскивания
        self.structure_tree = ttk.Treeview(structure_tree_frame, columns=("type",), selectmode="browse")
        self.structure_tree.heading("#0", text="Элемент")
        self.structure_tree.heading("type", text="Тип")
        self.structure_tree.column("#0", width=300)
        self.structure_tree.column("type", width=150)
        
        # Настраиваем теги для разных типов элементов
        self.structure_tree.tag_configure("folder", background="#f0f0f0")
        self.structure_tree.tag_configure("url", foreground="blue")
        self.structure_tree.tag_configure("totp", foreground="green")
        self.structure_tree.tag_configure("password", foreground="red")
        self.structure_tree.tag_configure("root", background="#e8f4fd", font=("Arial", 10, "bold"))
        
        # Добавляем скроллбар
        structure_scrollbar = ttk.Scrollbar(structure_tree_frame, orient=tk.VERTICAL, command=self.structure_tree.yview)
        self.structure_tree.configure(yscrollcommand=structure_scrollbar.set)
        
        self.structure_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        structure_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Настраиваем перетаскивание
        self.setup_drag_and_drop()
        
        # Фрейм для кнопок управления структурой
        structure_button_frame = tk.Frame(self.parent)
        structure_button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Кнопка обновления
        refresh_btn = tk.Button(
            structure_button_frame,
            text="Обновить",
            command=self.refresh_structure_tree
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка удаления
        delete_btn = tk.Button(
            structure_button_frame,
            text="Удалить выбранное",
            command=self.delete_structure_item,
            bg="#f44336",
            fg="white"
        )
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка сохранения
        save_btn = tk.Button(
            structure_button_frame,
            text="Сохранить изменения",
            command=self.save_structure_changes,
            bg="#4CAF50",
            fg="white"
        )
        save_btn.pack(side=tk.RIGHT, padx=5)
    
    def setup_drag_and_drop(self):
        """Настраивает перетаскивание элементов в дереве структуры"""
        self.drag_data = {
            "item": None, 
            "x": 0, 
            "y": 0,
            "hover_timer": None,
            "hover_item": None,
            "drag_window": None
        }
        
        # Биндим события перетаскивания
        self.structure_tree.bind("<ButtonPress-1>", self.on_structure_drag_start)
        self.structure_tree.bind("<ButtonRelease-1>", self.on_structure_drag_stop)
        self.structure_tree.bind("<B1-Motion>", self.on_structure_drag_motion)
        self.structure_tree.bind("<Leave>", self.on_structure_leave)
        
    def on_structure_drag_start(self, event):
        """Начало перетаскивания"""
        item = self.structure_tree.identify_row(event.y)
        if item and item != "root":  # Нельзя перетаскивать корень
            self.drag_data["item"] = item
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            
            # Создаем окно с именем элемента для отображения на курсоре
            self.create_drag_window(item, event.x_root, event.y_root)
    
    def create_drag_window(self, item, x_root, y_root):
        """Создает окно с именем элемента для отображения на курсоре"""
        item_text = self.structure_tree.item(item, "text")
        item_values = self.structure_tree.item(item, "values")
        
        # Создаем небольшое окно
        self.drag_data["drag_window"] = tk.Toplevel(self.structure_tree)
        self.drag_data["drag_window"].overrideredirect(True)
        self.drag_data["drag_window"].attributes("-alpha", 0.8)  # Полупрозрачное
        self.drag_data["drag_window"].attributes("-topmost", True)
        
        # Определяем цвет фона в зависимости от типа элемента
        bg_color = "#f0f0f0"  # По умолчанию для папок
        if "url" in str(item_values):
            bg_color = "#e3f2fd"  # Светло-голубой для ссылок
        elif "TOTP" in str(item_values):
            bg_color = "#e8f5e8"  # Светло-зеленый для TOTP
        elif "пароль" in str(item_values):
            bg_color = "#ffebee"  # Светло-красный для паролей
        
        # Создаем фрейм с содержимым
        frame = tk.Frame(
            self.drag_data["drag_window"], 
            bg=bg_color, 
            relief="solid", 
            borderwidth=1
        )
        frame.pack(padx=2, pady=2)
        
        # Добавляем текст
        label = tk.Label(
            frame, 
            text=item_text, 
            bg=bg_color,
            font=("Arial", 9),
            padx=8,
            pady=4
        )
        label.pack()
        
        # Позиционируем окно рядом с курсором
        self.update_drag_window_position(x_root, y_root)
    
    def update_drag_window_position(self, x, y):
        """Обновляет позицию окна перетаскивания"""
        if self.drag_data["drag_window"]:
            # Смещаем окно относительно курсора
            self.drag_data["drag_window"].geometry(f"+{x+15}+{y+15}")
    
    def destroy_drag_window(self):
        """Уничтожает окно перетаскивания"""
        if self.drag_data["drag_window"]:
            self.drag_data["drag_window"].destroy()
            self.drag_data["drag_window"] = None
    
    def on_structure_drag_stop(self, event):
        """Конец перетаскивания"""
        # Отменяем таймер раскрытия
        self.cancel_hover_timer()
        
        # Уничтожаем окно перетаскивания
        self.destroy_drag_window()
        
        self.drag_data["item"] = None
        self.drag_data["x"] = 0
        self.drag_data["y"] = 0
        self.drag_data["hover_item"] = None
    
    def on_structure_drag_motion(self, event):
        """Перетаскивание элемента"""
        if not self.drag_data["item"]:
            return
            
        # Обновляем позицию окна перетаскивания
        self.update_drag_window_position(event.x_root, event.y_root)
            
        # Определяем целевой элемент
        target_item = self.structure_tree.identify_row(event.y)
        
        if target_item and target_item != self.drag_data["item"]:
            try:
                # Проверяем, можно ли переместить элемент в целевой элемент
                if self.can_move_to_target(self.drag_data["item"], target_item):
                    # Если целевой элемент изменился, отменяем предыдущий таймер
                    if target_item != self.drag_data.get("hover_item"):
                        self.cancel_hover_timer()
                        self.drag_data["hover_item"] = target_item
                    
                    # Если это папка и она закрыта, запускаем таймер для автоматического раскрытия
                    if self.is_folder_closed(target_item):
                        self.start_hover_timer(target_item)
                    
                    # Используем встроенный метод move для перемещения
                    self.structure_tree.move(self.drag_data["item"], target_item, 0)
                    
            except Exception as e:
                print(f"Ошибка перемещения: {e}")
    
    def can_move_to_target(self, source_item, target_item):
        """Проверяет, можно ли переместить элемент в целевой элемент"""
        # Нельзя перемещать элемент внутрь себя
        if self.is_descendant(source_item, target_item):
            return False
        
        # Можно перемещать только в папки (включая корень) или в корень
        if target_item == "root":
            return True  # Корень всегда разрешен
        
        # Проверяем, является ли целевой элемент папкой
        if not self.is_folder(target_item):
            return False  # Нельзя перемещать в обычные элементы
        
        return True
    
    def on_structure_leave(self, event):
        """Курсор вышел за пределы дерева"""
        self.cancel_hover_timer()
    
    def start_hover_timer(self, item):
        """Запускает таймер для автоматического раскрытия папки"""
        self.cancel_hover_timer()  # Отменяем предыдущий таймер
        
        self.drag_data["hover_timer"] = self.structure_tree.after(
            300,  # 300 мс задержка
            self.auto_expand_folder,
            item
        )
    
    def cancel_hover_timer(self):
        """Отменяет таймер раскрытия папки"""
        if self.drag_data["hover_timer"]:
            self.structure_tree.after_cancel(self.drag_data["hover_timer"])
            self.drag_data["hover_timer"] = None
    
    def auto_expand_folder(self, item):
        """Автоматически раскрывает папку при задержке курсора"""
        try:
            if (item and 
                item != "root" and 
                self.is_folder(item) and 
                self.is_folder_closed(item)):
                
                self.structure_tree.item(item, open=True)
                # Прокручиваем дерево к раскрытой папке
                self.structure_tree.see(item)
                
        except Exception as e:
            print(f"Ошибка автоматического раскрытия: {e}")
        finally:
            self.drag_data["hover_timer"] = None
    
    def is_folder(self, item):
        """Проверяет, является ли элемент папкой"""
        if item == "root":
            return True
        
        children = self.structure_tree.get_children(item)
        return len(children) > 0
    
    def is_folder_closed(self, item):
        """Проверяет, закрыта ли папка"""
        if item == "root":
            # Корень всегда считается открытым
            return False
        
        try:
            return not self.structure_tree.item(item, "open")
        except:
            return False
    
    def is_descendant(self, parent_item, potential_child):
        """Проверяет, является ли potential_child потомком parent_item"""
        current = potential_child
        while current:
            if current == parent_item:
                return True
            current = self.structure_tree.parent(current)
        return False
    
    def refresh_structure_tree(self):
        """Обновляет дерево структуры"""
        for item in self.structure_tree.get_children():
            self.structure_tree.delete(item)
        
        # Добавляем корневую папку (только для визуального представления)
        root_item = self.structure_tree.insert("", "end", text="📁 Корень", values=(f"элементов: {len(self.data)}",), tags=("root",))
        self.structure_tree.item(root_item, open=True)
        
        # Добавляем все элементы нулевого уровня в корень
        self.add_structure_items(root_item, self.data)
    
    def add_structure_items(self, parent, data):
        """Рекурсивно добавляет элементы в дерево структуры"""
        if isinstance(data, list):
            for i, item in enumerate(data):
                for key, value in item.items():
                    # Определяем тег в зависимости от типа
                    tag = self.get_structure_tag(value)
                    
                    item_id = self.structure_tree.insert(parent, "end", text=key, values=(self.get_value_type(value),), tags=(tag,))
                    
                    # Рекурсивно добавляем дочерние элементы
                    if isinstance(value, dict) and value.get('type') == 'folder':
                        # Для новых форматов папок
                        self.add_structure_items(item_id, value.get('value', []))
    
    def get_structure_tag(self, value):
        """Возвращает тег для элемента в зависимости от типа"""
        if isinstance(value, dict):
            value_type = value.get('type', 'text')
            if value_type == 'folder':
                return "folder"
            elif value_type == 'url':
                return "url"
            elif value_type == 'totp':
                return "totp"
            elif value_type == 'password':
                return "password"
        return ""
    
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
    
    def delete_structure_item(self):
        """Удаляет выбранный элемент из структуры"""
        selection = self.structure_tree.selection()
        if not selection:
            messagebox.showwarning("Удаление", "Выберите элемент для удаления")
            return
        
        item = selection[0]
        
        # Нельзя удалить корень
        if item == "root":
            messagebox.showwarning("Удаление", "Нельзя удалить корневую директорию")
            return
        
        item_text = self.structure_tree.item(item, "text")
        
        if messagebox.askyesno("Подтверждение", f"Удалить элемент '{item_text}' и все его подэлементы?"):
            # Удаляем из дерева
            self.structure_tree.delete(item)
    
    def save_structure_changes(self):
        """Сохраняет изменения структуры в данные"""
        try:
            # Собираем новую структуру из дерева
            new_data = self.build_data_from_structure()
            
            # Обновляем данные
            self.data.clear()
            self.data.extend(new_data)
            
            # Сохраняем в файл
            self.save_structure_data()
            
            # Вызываем callback для обновления других вкладок
            if self.save_callback:
                self.save_callback()
            
            messagebox.showinfo("Сохранение", "Структура успешно сохранена!")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить структуру:\n{str(e)}")
    
    def build_data_from_structure(self):
        """Строит структуру данных из дерева"""
        # Находим элемент "Корень" и собираем его детей (это элементы нулевого уровня)
        root_item = None
        for item_id in self.structure_tree.get_children(""):
            if self.structure_tree.item(item_id, "text") == "📁 Корень":
                root_item = item_id
                break
        
        if root_item:
            # Собираем все элементы, которые находятся в корне
            return self.build_structure_branch(root_item)
        else:
            return []
    
    def build_structure_branch(self, parent):
        """Рекурсивно строит ветку структуры"""
        branch_data = []
        
        for item_id in self.structure_tree.get_children(parent):
            key = self.structure_tree.item(item_id, "text")
            
            # Получаем детей элемента
            children = self.structure_tree.get_children(item_id)
            
            if children:
                # Это папка - обрабатываем детей
                children_data = self.build_structure_branch(item_id)
                
                # В ЕДИНОМ ФОРМАТЕ создаем папку
                branch_data.append({key: {'type': 'folder', 'value': children_data}})
            else:
                # Это конечный элемент - нужно восстановить исходное значение
                original_value = self.find_original_value(key, self.data)
                if original_value:
                    branch_data.append({key: original_value})
                else:
                    # Если не нашли исходное значение, создаем текстовую запись
                    branch_data.append({key: {'type': 'text', 'value': ''}})
        
        return branch_data
    
    def find_original_value(self, key, data):
        """Находит исходное значение элемента по ключу"""
        if isinstance(data, list):
            for item in data:
                for k, v in item.items():
                    if k == key:
                        return v
                    # Рекурсивно ищем во вложенных структурах
                    if isinstance(v, dict) and v.get('type') == 'folder':
                        found = self.find_original_value(key, v.get('value', []))
                        if found:
                            return found
        return None
    
    def save_structure_data(self):
        """Сохраняет данные структуры в основной файл"""
        try:
            # Получаем путь к файлу данных
            data_file = os.path.join(os.path.expanduser('~'), '.credmanager', 'creds.json')
            
            # Сохраняем обновленные данные
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise Exception(f"Не удалось сохранить данные: {str(e)}")

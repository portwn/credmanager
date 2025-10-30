import tkinter as tk
from tkinter import ttk
from settings_general import GeneralSettingsTab
from settings_export import ExportTab
from settings_import import ImportTab
from settings_structure import StructureTab

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings, save_callback, data):
        super().__init__(parent)
        self.parent = parent
        self.settings = settings.copy()
        self.save_callback = save_callback
        self.data = data
        
        self.title("Настройки")
        self.geometry("700x600")
        self.resizable(True, True)
        
        # Делаем модальным
        self.transient(parent)
        self.grab_set()
        
        # Центрируем относительно родительского окна
        self.geometry(f"+{parent.winfo_rootx()+50}+{parent.winfo_rooty()+50}")
        
        # Биндим Esc на выход
        self.bind('<Escape>', lambda event: self.cancel_clicked())
        
        self.create_widgets()
        
    def create_widgets(self):
        # Создаем Notebook для вкладок
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка основных настроек
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="Основные")
        
        # Вкладка экспорта
        export_frame = ttk.Frame(notebook)
        notebook.add(export_frame, text="Экспорт")
        
        # Вкладка импорта
        import_frame = ttk.Frame(notebook)
        notebook.add(import_frame, text="Импорт")
        
        # Вкладка управления структурой
        structure_frame = ttk.Frame(notebook)
        notebook.add(structure_frame, text="Управление структурой")
        
        # Инициализируем вкладки
        self.general_tab = GeneralSettingsTab(general_frame, self.settings)
        self.export_tab = ExportTab(export_frame, self.data)
        self.import_tab = ImportTab(import_frame, self.data, self.save_import_data)
        self.structure_tab = StructureTab(structure_frame, self.data, self.save_structure_data)
        
        # Фрейм для кнопки выхода
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        
        # Кнопка Выход
        exit_button = tk.Button(
            button_frame,
            text="Выход",
            width=10,
            command=self.cancel_clicked
        )
        exit_button.pack()
        
        # Биндим Enter на выход
        self.bind('<Return>', lambda event: self.cancel_clicked())
        
    def save_import_data(self):
        """Callback для сохранения данных после импорта"""
        # После импорта данных нужно обновить все вкладки
        self.export_tab.populate_tree()
        self.structure_tab.refresh_structure_tree()
        
    def save_structure_data(self):
        """Callback для сохранения данных после изменения структуры"""
        # После изменения структуры нужно обновить все вкладки
        self.export_tab.populate_tree()
        
    def cancel_clicked(self):
        """Закрывает окно без сохранения настроек"""
        self.destroy()

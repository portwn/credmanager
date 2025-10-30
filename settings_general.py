#settings_general
import tkinter as tk
from tkinter import messagebox

class GeneralSettingsTab:
    def __init__(self, parent, settings):
        self.parent = parent
        self.settings = settings
        
        self.save_position_var = tk.BooleanVar(value=self.settings.get('save_position', True))
        self.timeout_var = tk.StringVar(value=str(self.settings.get('restore_timeout', 60)))
        
        self.create_widgets()
    
    def create_widgets(self):
        # Флажок сохранения позиции
        save_position_cb = tk.Checkbutton(
            self.parent, 
            text="Сохранять последнее положение при закрытии",
            variable=self.save_position_var,
            command=self.toggle_timeout_entry
        )
        save_position_cb.pack(anchor=tk.W, padx=20, pady=(20, 5))
        
        # Фрейм для настройки таймаута
        timeout_frame = tk.Frame(self.parent)
        timeout_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(timeout_frame, text="Время восстановления:").pack(side=tk.LEFT)
        
        self.timeout_entry = tk.Entry(timeout_frame, textvariable=self.timeout_var, width=8)
        self.timeout_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(timeout_frame, text="секунд").pack(side=tk.LEFT)
        
        # Подсказка
        hint_label = tk.Label(
            self.parent, 
            text="При открытии программы, если с последнего закрытия прошло больше указанного времени,\nпрограмма откроется в корневой директории.",
            justify=tk.LEFT,
            fg="gray",
            font=("Arial", 8)
        )
        hint_label.pack(anchor=tk.W, padx=20, pady=(5, 20))
        
        # Обновляем состояние поля ввода таймаута
        self.toggle_timeout_entry()
    
    def toggle_timeout_entry(self):
        """Включает/выключает поле ввода таймаута"""
        if self.save_position_var.get():
            self.timeout_entry.config(state='normal')
        else:
            self.timeout_entry.config(state='disabled')
    
    def get_settings(self):
        """Возвращает текущие настройки"""
        settings = {
            'save_position': self.save_position_var.get()
        }
        
        if self.save_position_var.get():
            try:
                settings['restore_timeout'] = int(self.timeout_var.get())
            except ValueError:
                raise ValueError("Введите корректное число секунд!")
        
        return settings

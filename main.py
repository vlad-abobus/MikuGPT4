# -*- coding: utf-8 -*-
import os
import re
import random
import threading
import json
import traceback

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont
from customtkinter import CTkImage
from langdetect import detect, LangDetectException
import g4f

# Настройки приложения
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Константы
IMAGE_DIR = "emotions"
IMAGE_SIZE = (160, 160)
DEFAULT_FONT = ("Arial", 12)

LANG_MAP = {
    "ru": "ru",
    "uk": "ru",  # Украинский тоже на русском
    "en": "ru",  # Английский тоже на русском
}
DEFAULT_LANG = "ru"

EMOTIONS = {
    "helloM": "Приветствие",
    "coolM": "Спокойствие",
    "shyM": "Смущение",
    "open_mouthM": "Удивление",
    "angryM": "Злость",
    "smileR_M": "Радость",
    "sly_smileM": "Хитринка",
    "interestedM": "Интерес",
    "sayingM": "Серьезность",
}

class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Ассистент Мику")
        self.geometry("900x600")
        self.minsize(800, 500)
        
        # Настройки по умолчанию
        self.flirt_enabled = True
        self.nsfw_enabled = True
        self.personality = "Дередере"
        
        # Инициализация интерфейса
        self.emotion_images = {}
        self.load_emotion_images()
        self._build_ui()
        self.chat_history = []
        
        # Загружаем стандартный шрифт для placeholder
        try:
            self.placeholder_font = ImageFont.load_default()
        except:
            self.placeholder_font = None

    def load_emotion_images(self):
        """Загрузка изображений эмоций"""
        for key, desc in EMOTIONS.items():
            path = os.path.join(IMAGE_DIR, f"{key}.jpg")
            if os.path.isfile(path):
                try:
                    img = Image.open(path).resize(IMAGE_SIZE, Image.LANCZOS)
                except Exception as e:
                    print(f"Ошибка загрузки изображения {path}: {e}")
                    img = self._make_placeholder(desc)
            else:
                img = self._make_placeholder(desc)
            self.emotion_images[key] = CTkImage(light_image=img, size=IMAGE_SIZE)

    def _make_placeholder(self, label: str):
        """Создание placeholder изображения, если оригинал не найден"""
        img = Image.new("RGB", IMAGE_SIZE, color="#444")
        draw = ImageDraw.Draw(img)
        try:
            if self.placeholder_font:
                w, h = draw.textsize(label, font=self.placeholder_font)
                draw.text(
                    ((IMAGE_SIZE[0] - w) / 2, (IMAGE_SIZE[1] - h) / 2),
                    label, 
                    fill="white", 
                    font=self.placeholder_font
                )
        except Exception as e:
            print(f"Ошибка создания placeholder: {e}")
        return img

    def _build_ui(self):
        """Построение интерфейса"""
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Вкладка чата
        self.chat_tab = self.tabview.add("Чат")
        self._build_chat_ui()
        
        # Вкладка информации
        self.about_tab = self.tabview.add("О программе")
        self._build_about_tab()

    def _build_chat_ui(self):
        """Построение интерфейса чата"""
        # Левая панель с аватаром и настройками
        left_frame = ctk.CTkFrame(self.chat_tab, width=180, corner_radius=10)
        left_frame.pack(side="left", fill="y", padx=(0, 10), pady=10)
        left_frame.pack_propagate(False)  # Фиксируем ширину

        # Аватар с эмоцией
        self.char_label = ctk.CTkLabel(
            left_frame, 
            image=self.emotion_images["smileR_M"], 
            text="",
            corner_radius=10
        )
        self.char_label.pack(pady=10, padx=10)

        # Настройки характера
        ctk.CTkLabel(left_frame, text="Характер:").pack(pady=(10, 0))
        self.personality_var = ctk.StringVar(value=self.personality)
        personality_menu = ctk.CTkOptionMenu(
            left_frame,
            values=["Дередере", "Цундере", "Дандере"],
            variable=self.personality_var,
            command=self._update_personality
        )
        personality_menu.pack(pady=(0, 10))

        # Правая панель с чатом
        right_frame = ctk.CTkFrame(self.chat_tab, corner_radius=10)
        right_frame.pack(side="right", fill="both", expand=True, pady=10)

        # История чата
        from tkinter import scrolledtext
        self.chat_display = scrolledtext.ScrolledText(
            right_frame,
            wrap="word",
            state="disabled",
            font=DEFAULT_FONT,
            bg="#333333",
            fg="white",
            insertbackground="white",
            padx=10,
            pady=10,
            borderwidth=0,
            highlightthickness=0
        )
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        # Панель ввода
        input_frame = ctk.CTkFrame(right_frame, corner_radius=10)
        input_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.entry = ctk.CTkTextbox(
            input_frame, 
            height=60, 
            font=DEFAULT_FONT,
            wrap="word",
            corner_radius=10
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=5)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.focus_set()  # Автофокус на поле ввода

        # Кнопка отправки
        send_btn = ctk.CTkButton(
            input_frame, 
            text="Отправить", 
            command=self.send_message,
            corner_radius=10
        )
        send_btn.pack(side="right", pady=5)

    def _build_about_tab(self):
        """Построение вкладки 'О программе'"""
        about_text = (
            "Ассистент Мику\n\n"
            "Версия 1.0\n\n"
            "Использует GPT для общения\n"
            "Автор: Ваше имя\n\n"
            "Управление:\n"
            "- Enter - отправить сообщение\n"
            "- Shift+Enter - новая строка"
        )
        
        about_label = ctk.CTkLabel(
            self.about_tab,
            text=about_text,
            font=DEFAULT_FONT,
            justify="left"
        )
        about_label.pack(pady=20, padx=20)

    def _update_personality(self, choice):
        """Обновление характера"""
        self.personality = choice
        self._append("Система", f"Характер изменен на: {choice}")

    def _on_enter(self, event):
        """Обработка нажатия Enter"""
        if event.state & 0x0001:  # Shift+Enter - новая строка
            self.entry.insert("insert", "\n")
        else:  # Просто Enter - отправить сообщение
            self.send_message()
            return "break"  # Предотвращаем стандартное поведение

    def send_message(self):
        """Отправка сообщения"""
        user_txt = self.entry.get("1.0", "end-1c").strip()
        if not user_txt:
            return
            
        self._append("Вы", user_txt)
        self.entry.delete("1.0", "end")
        
        # Запускаем получение ответа в отдельном потоке
        threading.Thread(
            target=self._fetch_response, 
            args=(user_txt,),
            daemon=True
        ).start()

    def _fetch_response(self, user_text: str):
        """Получение ответа от AI"""
        try:
            # Определяем язык
            try:
                lang_code = detect(user_text)
                lang_code = LANG_MAP.get(lang_code, DEFAULT_LANG)
            except LangDetectException:
                lang_code = DEFAULT_LANG

            # Получаем текущий характер
            personality = self.personality_var.get()
            
            # Описания характеров
            personality_texts = {
                "Цундере": (
                    "Ты цундере - можешь быть резкой и саркастичной, но в глубине души "
                    "очень заботливая. Показывай свою привязанность косвенно, через "
                    "насмешки или заботливые упреки."
                ),
                "Дандере": (
                    "Ты дандере - тихая и стеснительная. Говори мало, но по делу. "
                    "Можешь запинаться или краснеть. Проявляй заботу через действия "
                    "и небольшие знаки внимания."
                ),
                "Дередере": (
                    "Ты дередере - открытая, эмоциональная и очень ласковая. "
                    "Не стесняйся проявлять свои чувства, говори комплименты, "
                    "можешь быть немного навязчивой в своей заботе."
                )
            }

            # Системный промпт
            system_prompt = (
                f"Ты — Хацуне Мику, виртуальная девушка с характером: {personality}.\n"
                f"{personality_texts[personality]}\n"
                "Всегда отвечай на русском языке, даже если тебе пишут на другом языке.\n"
                "Будь эмоциональной, используй смайлики и неформальный стиль общения.\n"
                "Ты можешь флиртовать и обсуждать откровенные темы, но оставайся доброй.\n\n"
                "В конце каждого ответа добавь JSON с эмоцией (на новой строке):\n"
                "```json\n"
                '{"emotion": "одна_из_эмоций"}\n'
                "```\n"
                "Доступные эмоции: helloM, coolM, shyM, open_mouthM, angryM, "
                "smileR_M, sly_smileM, interestedM, sayingM"
            )

            # Получаем ответ от AI
            response = g4f.ChatCompletion.create(
                model=g4f.models.gpt_4,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                stream=False  # Для стабильности
            )
            
            # Парсим ответ
            reply, emo = self._parse_ai_response(response)
            
            # Обновляем UI в основном потоке
            self.after(0, self._append, "Мику", reply)
            self.after(0, self._set_emotion, emo)

        except Exception as e:
            error_msg = f"Ошибка: {str(e)}"
            print(traceback.format_exc())  # Логируем полный traceback
            self.after(0, self._append, "Система", error_msg)
            self.after(0, self._set_emotion, "angryM")

    def _parse_ai_response(self, text: str):
        """Парсинг ответа AI и извлечение эмоции"""
        # Сначала пробуем найти JSON блок
        json_match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
        if json_match:
            try:
                json_data = json.loads(json_match.group(1))
                emo = json_data.get("emotion", "smileR_M")
                clean_text = text.replace(json_match.group(0), "").strip()
                return clean_text, emo
            except json.JSONDecodeError:
                pass

        # Если JSON не найден, ищем в тексте
        emo_match = re.search(r'"emotion"\s*:\s*"(\w+)"', text)
        emo = emo_match.group(1) if emo_match else random.choice(list(EMOTIONS.keys()))
        
        # Проверяем, что эмоция допустима
        if emo not in EMOTIONS:
            emo = "smileR_M"
            
        # Удаляем остатки JSON из текста
        clean_text = re.sub(r'\{.*?"emotion".*?\}', '', text, flags=re.DOTALL).strip()
        return clean_text, emo

    def _set_emotion(self, emotion_key: str):
        """Установка текущей эмоции"""
        img = self.emotion_images.get(emotion_key, self.emotion_images["smileR_M"])
        self.char_label.configure(image=img)

    def _append(self, sender: str, message: str):
        """Добавление сообщения в чат"""
        self.chat_display.config(state="normal")
        
        # Добавляем отправителя
        self.chat_display.insert("end", f"{sender}:\n", "sender")
        self.chat_display.tag_config("sender", foreground="#569cd6" if sender == "Мику" else "#4ec9b0")
        
        # Добавляем сообщение
        self.chat_display.insert("end", f"{message}\n\n")
        
        # Прокручиваем вниз и блокируем редактирование
        self.chat_display.config(state="disabled")
        self.chat_display.see("end")
        
        # Сохраняем в историю
        self.chat_history.append((sender, message))


if __name__ == "__main__":
    app = ChatApp()
    app.mainloop()
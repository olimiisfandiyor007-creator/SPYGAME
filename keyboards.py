from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import EMOJI

def get_main_menu_keyboard():
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['room']} Создать комнату", callback_data='create_room')],
        [InlineKeyboardButton(f"{EMOJI['play']} Присоединиться к комнате", callback_data='join_room')],
        [InlineKeyboardButton(f"{EMOJI['info']} Правила игры", callback_data='rules')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_room_settings_keyboard(spy_count: int, category: str):
    """Настройки комнаты"""
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['spy']} Шпионов: {spy_count}", callback_data='change_spy_count')],
        [InlineKeyboardButton(f"{EMOJI['category']} Категория", callback_data='change_category')],
        [InlineKeyboardButton(f"{EMOJI['ready']} Готово", callback_data='settings_done')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_spy_count_keyboard():
    """Выбор количества шпионов"""
    keyboard = [
        [InlineKeyboardButton("1 шпион", callback_data='spy_1'),
         InlineKeyboardButton("2 шпиона", callback_data='spy_2')],
        [InlineKeyboardButton("3 шпиона", callback_data='spy_3')],
        [InlineKeyboardButton(f"{EMOJI['ready']} Назад", callback_data='back_to_settings')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_category_keyboard():
    """Выбор категории"""
    from words_data import get_all_categories
    categories = get_all_categories()
    
    keyboard = []
    for i in range(0, len(categories), 2):
        row = []
        row.append(InlineKeyboardButton(categories[i], callback_data=f'cat_{i}'))
        if i + 1 < len(categories):
            row.append(InlineKeyboardButton(categories[i + 1], callback_data=f'cat_{i+1}'))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(f"{EMOJI['ready']} Назад", callback_data='back_to_settings')])
    return InlineKeyboardMarkup(keyboard)

def get_room_keyboard(room_id: str, is_creator: bool, can_start: bool):
    """Клавиатура комнаты"""
    keyboard = []
    
    if is_creator and can_start:
        keyboard.append([InlineKeyboardButton(f"{EMOJI['play']} Начать игру", callback_data='start_game')])
    
    if is_creator:
        keyboard.append([InlineKeyboardButton(f"{EMOJI['settings']} Настройки", callback_data='room_settings')])
    
    keyboard.append([
        InlineKeyboardButton(f"{EMOJI['ready']} Обновить", callback_data='refresh_room'),
        InlineKeyboardButton(f"{EMOJI['stop']} Покинуть", callback_data='leave_room')
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_game_keyboard():
    """Клавиатура во время игры"""
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['info']} Моя роль", callback_data='show_role')],
        [InlineKeyboardButton(f"{EMOJI['stop']} Завершить игру", callback_data='end_game')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_end_game_keyboard():
    """Клавиатура после игры"""
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['play']} Играть снова", callback_data='play_again')],
        [InlineKeyboardButton(f"{EMOJI['stop']} Покинуть комнату", callback_data='leave_room')]
    ]
    return InlineKeyboardMarkup(keyboard)
import logging
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from config import BOT_TOKEN, EMOJI, MAX_PLAYERS, MIN_PLAYERS
from database import db, GameState
from game_logic import start_game, end_game, reset_game, get_game_stats
from keyboards import *
from words_data import get_all_categories, CATEGORIES

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(name)

def generate_room_id() -> str:
    """Генерация ID комнаты"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_room_info_text(room) -> str:
    """Получить текст с информацией о комнате"""
    players_text = "\n".join([
        f"{i+1}. {EMOJI['ready'] if p.is_ready else EMOJI['wait']} {p.first_name} (@{p.username})"
        for i, p in enumerate(room.players)
    ])
    
    text = f"""
{EMOJI['room']} <b>КОМНАТА: {room.room_id}</b>

{EMOJI['category']} <b>Категория:</b> {room.category}
{EMOJI['spy']} <b>Шпионов:</b> {room.spy_count}
{EMOJI['players']} <b>Игроков:</b> {room.get_player_count()}/{MAX_PLAYERS}

<b>Участники:</b>
{players_text}

{EMOJI['info']} <i>Минимум игроков для старта: {MIN_PLAYERS}</i>
"""
    return text

def get_game_info_text(room) -> str:
    """Получить текст с информацией об игре"""
    stats = get_game_stats(room)
    
    text = f"""
{EMOJI['fire']} <b>ИГРА НАЧАЛАСЬ!</b>

{EMOJI['category']} <b>Категория:</b> {room.category}
{EMOJI['players']} <b>Игроков:</b> {stats['total_players']}
{EMOJI['spy']} <b>Шпионов:</b> {stats['spy_count']}
{EMOJI['civilian']} <b>Мирных жителей:</b> {stats['civilian_count']}

{EMOJI['info']} <i>Нажмите "Моя роль" чтобы узнать своё слово</i>
"""
    return text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    welcome_text = f"""
{EMOJI['fire']} <b>Добро пожаловать в игру ШПИОН!</b>

Привет, {user.first_name}!

{EMOJI['spy']} <b>Суть игры:</b>
Все игроки получают одно слово, кроме шпионов. Задача мирных жителей - вычислить шпиона, не раскрывая слово. Задача шпиона - остаться незамеченным и угадать слово.

{EMOJI['play']} Выберите действие:
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='HTML'
    )

async def create_room_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание новой комнаты"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Проверяем, есть ли пользователь уже в комнате
    if db.get_user_room(user.id):
        await query.edit_message_text(
            f"{EMOJI['warning']} Вы уже находитесь в комнате! Сначала покиньте её.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(f"{EMOJI['ready']} Вернуться", callback_data='back_to_menu')
            ]])
        )
        return
    
    # Показываем настройки
    text = f"""
{EMOJI['settings']} <b>НАСТРОЙКИ КОМНАТЫ</b>

Выберите параметры игры:
"""
    
    await query.edit_message_text(
        text,
        reply_markup=get_room_settings_keyboard(1, '🌍 Страны'),
        parse_mode='HTML'
    )
    
    # Сохраняем временные настройки
    context.user_data['temp_spy_count'] = 1
    context.user_data['temp_category'] = '🌍 Страны'

async def change_spy_count_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Изменение количества шпионов"""
    query = update.callback_query
    await query.answer()
    
    text = f"""
{EMOJI['spy']} <b>ВЫБЕРИТЕ КОЛИЧЕСТВО ШПИОНОВ</b>

Текущее значение: {context.user_data.get('temp_spy_count', 1)}
"""
    
    await query.edit_message_text(
        text,
        reply_markup=get_spy_count_keyboard(),
        parse_mode='HTML'
    )
    async def set_spy_count_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Установка количества шпионов"""
        query = update.callback_query
        await query.answer()
    
        spy_count = int(query.data.split('_')[1])
        context.user_data['temp_spy_count'] = spy_count
    
        category = context.user_data.get('temp_category', '🌍 Страны')
    
        text = f"""
{EMOJI['settings']} <b>НАСТРОЙКИ КОМНАТЫ</b>

{EMOJI['ready']} Количество шпионов установлено: {spy_count}
"""
    
        await query.edit_message_text(
            text,
            reply_markup=get_room_settings_keyboard(spy_count, category),
            parse_mode='HTML'
        )

async def change_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Изменение категории"""
    query = update.callback_query
    await query.answer()
    
    text = f"""
{EMOJI['category']} <b>ВЫБЕРИТЕ КАТЕГОРИЮ</b>

Текущая: {context.user_data.get('temp_category', '🌍 Страны')}
"""
    
    await query.edit_message_text(
        text,
        reply_markup=get_category_keyboard(),
        parse_mode='HTML'
    )

async def set_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка категории"""
    query = update.callback_query
    await query.answer()
    
    cat_index = int(query.data.split('_')[1])
    categories = get_all_categories()
    category = categories[cat_index]
    
    context.user_data['temp_category'] = category
    
    spy_count = context.user_data.get('temp_spy_count', 1)
    
    text = f"""
{EMOJI['settings']} <b>НАСТРОЙКИ КОМНАТЫ</b>

{EMOJI['ready']} Категория установлена: {category}
"""
    
    await query.edit_message_text(
        text,
        reply_markup=get_room_settings_keyboard(spy_count, category),
        parse_mode='HTML'
    )

async def settings_done_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение настроек и создание комнаты"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Создаем комнату
    room_id = generate_room_id()
    room = db.create_room(room_id, user.id, user.username or "NoUsername", user.first_name)
    
    # Применяем настройки
    room.spy_count = context.user_data.get('temp_spy_count', 1)
    room.category = context.user_data.get('temp_category', '🌍 Страны')
    
    # Очищаем временные данные
    context.user_data.pop('temp_spy_count', None)
    context.user_data.pop('temp_category', None)
    
    text = get_room_info_text(room)
    
    await query.edit_message_text(
        text,
        reply_markup=get_room_keyboard(room_id, True, room.can_start()),
        parse_mode='HTML'
    )

async def join_room_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Присоединение к комнате"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Проверяем, есть ли пользователь уже в комнате
    if db.get_user_room(user.id):
        await query.edit_message_text(
            f"{EMOJI['warning']} Вы уже находитесь в комнате! Сначала покиньте её.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(f"{EMOJI['ready']} Вернуться", callback_data='back_to_menu')
            ]])
        )
        return
    
    text = f"""
{EMOJI['room']} <b>ПРИСОЕДИНИТЬСЯ К КОМНАТЕ</b>

Отправьте код комнаты (6 символов):
"""
    
    await query.edit_message_text(text, parse_mode='HTML')
    context.user_data['waiting_for_room_code'] = True

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    if context.user_data.get('waiting_for_room_code'):
        room_code = update.message.text.strip().upper()
        
        if len(room_code) != 6:
            await update.message.reply_text(
                f"{EMOJI['warning']} Код комнаты должен содержать 6 символов!",
                reply_markup=get_main_menu_keyboard()
            )
            context.user_data['waiting_for_room_code'] = False
            return
        
        room = db.get_room(room_code)
        if not room:
            await update.message.reply_text(
                f"{EMOJI['warning']} Комната с кодом {room_code} не найдена!",
                reply_markup=get_main_menu_keyboard()
            )
            context.user_data['waiting_for_room_code'] = False
            return
        
        user = update.effective_user
        if db.join_room(room_code, user.id, user.username or "NoUsername", user.first_name):
            text = get_room_info_text(room)
            await update.message.reply_text(
                f"{EMOJI['success']} Вы присоединились к комнате!\n\n{text}",
                reply_markup=get_room_keyboard(room_code, False, room.can_start()),
                parse_mode='HTML'
            )
            
            # Уведомляем других игроков
            for player in room.players:
                if player.user_id != user.id:
                    try:
                        await context.bot.send_message(
                            player.user_id,
                            f"{EMOJI['info']} {user.first_name} присоединился к комнате!"
                        )
                    except:
                        pass
        else:
            await update.message.reply_text(
                f"{EMOJI['warning']} Не удалось присоединиться к комнате. Возможно, она заполнена или игра уже началась.",
                reply_markup=get_main_menu_keyboard()
            )
        
        context.user_data['waiting_for_room_code'] = False
async def room_settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Настройки комнаты (для создателя)"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    room = db.get_user_room(user.id)
    
    if not room or room.creator_id != user.id:
        await query.answer(f"{EMOJI['warning']} У вас нет прав!", show_alert=True)
        return
    
    context.user_data['temp_spy_count'] = room.spy_count
    context.user_data['temp_category'] = room.category
    context.user_data['editing_room'] = room.room_id
    
    text = f"""
{EMOJI['settings']} <b>НАСТРОЙКИ КОМНАТЫ</b>

Измените параметры игры:
"""
    
    await query.edit_message_text(
        text,
        reply_markup=get_room_settings_keyboard(room.spy_count, room.category),
        parse_mode='HTML'
    )

async def back_to_settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к настройкам"""
    query = update.callback_query
    await query.answer()
    
    if 'editing_room' in context.user_data:
        room = db.get_room(context.user_data['editing_room'])
        if room:
            # Сохраняем настройки
            room.spy_count = context.user_data.get('temp_spy_count', 1)
            room.category = context.user_data.get('temp_category', '🌍 Страны')
            
            context.user_data.pop('editing_room', None)
            
            text = get_room_info_text(room)
            await query.edit_message_text(
                text,
                reply_markup=get_room_keyboard(room.room_id, True, room.can_start()),
                parse_mode='HTML'
            )
    else:
        spy_count = context.user_data.get('temp_spy_count', 1)
        category = context.user_data.get('temp_category', '🌍 Страны')
        
        text = f"""
{EMOJI['settings']} <b>НАСТРОЙКИ КОМНАТЫ</b>

Выберите параметры игры:
"""
        
        await query.edit_message_text(
            text,
            reply_markup=get_room_settings_keyboard(spy_count, category),
            parse_mode='HTML'
        )

async def refresh_room_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обновление информации о комнате"""
    query = update.callback_query
    await query.answer(f"{EMOJI['ready']} Обновлено!")
    
    user = query.from_user
    room = db.get_user_room(user.id)
    
    if not room:
        await query.edit_message_text(
            f"{EMOJI['warning']} Комната не найдена!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    text = get_room_info_text(room)
    is_creator = room.creator_id == user.id
    
    await query.edit_message_text(
        text,
        reply_markup=get_room_keyboard(room.room_id, is_creator, room.can_start()),
        parse_mode='HTML'
    )

async def start_game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало игры"""
    query = update.callback_query
    
    user = query.from_user
    room = db.get_user_room(user.id)
    
    if not room or room.creator_id != user.id:
        await query.answer(f"{EMOJI['warning']} У вас нет прав!", show_alert=True)
        return
    
    if not room.can_start():
        await query.answer(
            f"{EMOJI['warning']} Недостаточно игроков! Минимум: {MIN_PLAYERS}",
            show_alert=True
        )
        return
    
    await query.answer()
    
    # Начинаем игру
    start_game(room)
    
    text = get_game_info_text(room)
    
    await query.edit_message_text(
        text,
        reply_markup=get_game_keyboard(),
        parse_mode='HTML'
    )
    
    # Отправляем роли всем игрокам
    for player in room.players:
        try:
            if player.is_spy:
                role_text = f"""
{EMOJI['spy']} <b>ВЫ - ШПИОН!</b>

{EMOJI['category']} <b>Категория:</b> {room.category}

{EMOJI['info']} <b>Ваша задача:</b>
- Не раскрывайте себя
- Попытайтесь угадать слово
- Ведите себя как мирный житель
<b>Слово мирных жителей вам неизвестно!</b>
"""
            else:
                role_text = f"""
{EMOJI['civilian']} <b>ВЫ - МИРНЫЙ ЖИТЕЛЬ!</b>

{EMOJI['category']} <b>Категория:</b> {room.category}
📝 <b>Ваше слово:</b> <code>{player.word}</code>

{EMOJI['info']} <b>Ваша задача:</b>
- Вычислить шпиона
- Не раскрывать слово напрямую
- Обсуждайте слово намёками
"""
            
            await context.bot.send_message(
                player.user_id,
                role_text,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Ошибка отправки роли игроку {player.user_id}: {e}")

async def show_role_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать роль игрока"""
    query = update.callback_query
    
    user = query.from_user
    room = db.get_user_room(user.id)
    
    if not room or room.state != GameState.PLAYING:
        await query.answer(f"{EMOJI['warning']} Игра не активна!", show_alert=True)
        return
    
    player = room.get_player(user.id)
    if not player:
        await query.answer(f"{EMOJI['warning']} Вы не в игре!", show_alert=True)
        return
    
    if player.is_spy:
        role_text = f"{EMOJI['spy']} Вы ШПИОН!\n{EMOJI['category']} Категория: {room.category}"
    else:
        role_text = f"{EMOJI['civilian']} Вы МИРНЫЙ ЖИТЕЛЬ!\n📝 Ваше слово: {player.word}"
    
    await query.answer(role_text, show_alert=True)

async def end_game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение игры"""
    query = update.callback_query
    
    user = query.from_user
    room = db.get_user_room(user.id)
    
    if not room:
        await query.answer(f"{EMOJI['warning']} Комната не найдена!", show_alert=True)
        return
    
    if room.creator_id != user.id:
        await query.answer(f"{EMOJI['warning']} Только создатель может завершить игру!", show_alert=True)
        return
    
    await query.answer()
    
    end_game(room)
    stats = get_game_stats(room)
    
    # Формируем список шпионов
    spies = [p for p in room.players if p.is_spy]
    spies_text = "\n".join([f"• {p.first_name}" for p in spies])
    
    text = f"""
{EMOJI['success']} <b>ИГРА ЗАВЕРШЕНА!</b>

📝 <b>Слово было:</b> <code>{room.word}</code>
{EMOJI['category']} <b>Категория:</b> {room.category}

{EMOJI['spy']} <b>Шпионы:</b>
{spies_text}

{EMOJI['players']} <b>Всего игроков:</b> {stats['total_players']}
{EMOJI['civilian']} <b>Мирных жителей:</b> {stats['civilian_count']}
"""
    
    await query.edit_message_text(
        text,
        reply_markup=get_end_game_keyboard(),
        parse_mode='HTML'
    )
    
    # Уведомляем всех игроков
    for player in room.players:
        if player.user_id != user.id:
            try:
                await context.bot.send_message(
                    player.user_id,
                    text,
                    parse_mode='HTML'
                )
            except:
                pass

async def play_again_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Играть снова"""
    query = update.callback_query
    
    user = query.from_user
    room = db.get_user_room(user.id)
    
    if not room or room.creator_id != user.id:
        await query.answer(f"{EMOJI['warning']} У вас нет прав!", show_alert=True)
        return
    
    await query.answer()
    
    reset_game(room)
    
    text = get_room_info_text(room)
    
    await query.edit_message_text(
        text,
        reply_markup=get_room_keyboard(room.room_id, True, room.can_start()),
        parse_mode='HTML'
    )
    
    # Уведомляем игроков
    for player in room.players:
        if player.user_id != user.id:
            try:
                await context.bot.send_message(
                    player.user_id,
                    f"{EMOJI['info']} Комната сброшена. Можно начать новую игру!"
                )
            except:
                pass
async def leave_room_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покинуть комнату"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    room = db.get_user_room(user.id)
    
    if room:
        was_creator = room.creator_id == user.id
        db.leave_room(user.id)
        
        if was_creator:
            # Уведомляем игроков о закрытии комнаты
            for player in room.players:
                try:
                    await context.bot.send_message(
                        player.user_id,
                        f"{EMOJI['warning']} Создатель покинул комнату. Комната закрыта!",
                        reply_markup=get_main_menu_keyboard()
                    )
                except:
                    pass
    
    await query.edit_message_text(
        f"{EMOJI['success']} Вы покинули комнату!",
        reply_markup=get_main_menu_keyboard()
    )

async def rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать правила"""
    query = update.callback_query
    await query.answer()
    
    rules_text = f"""
{EMOJI['info']} <b>ПРАВИЛА ИГРЫ "ШПИОН"</b>

{EMOJI['play']} <b>Подготовка:</b>
1. Создайте комнату или присоединитесь к существующей
2. Выберите категорию и количество шпионов
3. Дождитесь минимум {MIN_PLAYERS} игроков
4. Начните игру

{EMOJI['spy']} <b>Роли:</b>
• <b>Мирные жители</b> - получают общее слово из категории
• <b>Шпионы</b> - не знают слово, но знают категорию

{EMOJI['fire']} <b>Процесс игры:</b>
1. Игроки по очереди описывают слово намёками
2. Нельзя называть слово напрямую или однокоренные слова
3. Шпионы пытаются понять слово и не раскрыть себя
4. Мирные жители пытаются вычислить шпиона

{EMOJI['success']} <b>Победа:</b>
• <b>Мирные жители</b> побеждают, если найдут всех шпионов
• <b>Шпионы</b> побеждают, если останутся незамеченными

{EMOJI['warning']} <b>Советы:</b>
• Давайте не слишком очевидные подсказки
• Следите за реакцией других игроков
• Шпионам важно вести себя естественно
• Обсуждайте подозрительное поведение

<b>Удачной игры!</b> {EMOJI['fire']}
"""
    
    await query.edit_message_text(
        rules_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(f"{EMOJI['ready']} Понятно", callback_data='back_to_menu')
        ]]),
        parse_mode='HTML'
    )

async def back_to_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню"""
    query = update.callback_query
    await query.answer()
    
    welcome_text = f"""
{EMOJI['fire']} <b>ИГРА "ШПИОН"</b>

{EMOJI['info']} Выберите действие:
"""
    
    await query.edit_message_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='HTML'
    )

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    
    # Регистрируем обработчики callback-запросов
    application.add_handler(CallbackQueryHandler(create_room_handler, pattern='^create_room$'))
    application.add_handler(CallbackQueryHandler(join_room_handler, pattern='^join_room$'))
    application.add_handler(CallbackQueryHandler(rules_handler, pattern='^rules$'))
    application.add_handler(CallbackQueryHandler(back_to_menu_handler, pattern='^back_to_menu$'))
    
    application.add_handler(CallbackQueryHandler(change_spy_count_handler, pattern='^change_spy_count$'))
    application.add_handler(CallbackQueryHandler(set_spy_count_handler, pattern='^spy_\d+$'))
    application.add_handler(CallbackQueryHandler(change_category_handler, pattern='^change_category$'))
    application.add_handler(CallbackQueryHandler(set_category_handler, pattern='^cat_\d+$'))
    application.add_handler(CallbackQueryHandler(settings_done_handler, pattern='^settings_done$'))
    application.add_handler(CallbackQueryHandler(back_to_settings_handler, pattern='^back_to_settings$'))
    
    application.add_handler(CallbackQueryHandler(room_settings_handler, pattern='^room_settings$'))
    application.add_handler(CallbackQueryHandler(refresh_room_handler, pattern='^refresh_room$'))
    application.add_handler(CallbackQueryHandler(start_game_handler, pattern='^start_game$'))
    application.add_handler(CallbackQueryHandler(leave_room_handler, pattern='^leave_room$'))
    
    application.add_handler(CallbackQueryHandler(show_role_handler, pattern='^show_role$'))
    application.add_handler(CallbackQueryHandler(end_game_handler, pattern='^end_game$'))
    application.add_handler(CallbackQueryHandler(play_again_handler, pattern='^play_again$'))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Запускаем бота
    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if name == 'main':
    main()
    
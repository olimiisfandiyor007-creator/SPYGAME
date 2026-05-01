import random
from typing import List
from database import GameRoom, Player, GameState
from words_data import get_random_word

def start_game(room: GameRoom) -> bool:
    """Начать игру"""
    if not room.can_start():
        return False
    
    # Получаем случайное слово из категории
    room.word = get_random_word(room.category)
    
    # Выбираем шпионов
    players_list = room.players.copy()
    random.shuffle(players_list)
    
    spy_count = min(room.spy_count, len(players_list) - 1)
    
    for i, player in enumerate(players_list):
        if i < spy_count:
            player.is_spy = True
            player.word = None
        else:
            player.is_spy = False
            player.word = room.word
    
    room.state = GameState.PLAYING
    return True

def end_game(room: GameRoom):
    """Завершить игру"""
    room.state = GameState.FINISHED

def reset_game(room: GameRoom):
    """Сбросить игру для новой"""
    room.state = GameState.WAITING
    room.word = None
    for player in room.players:
        player.is_spy = False
        player.word = None
        player.is_ready = False

def get_game_stats(room: GameRoom) -> dict:
    """Получить статистику игры"""
    spy_count = sum(1 for p in room.players if p.is_spy)
    civilian_count = len(room.players) - spy_count
    
    return {
        'total_players': len(room.players),
        'spy_count': spy_count,
        'civilian_count': civilian_count,
        'word': room.word
    }
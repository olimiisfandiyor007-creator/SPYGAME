from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

class GameState(Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"

@dataclass
class Player:
    user_id: int
    username: str
    first_name: str
    is_spy: bool = False
    word: Optional[str] = None
    is_ready: bool = False

@dataclass
class GameRoom:
    room_id: str
    creator_id: int
    players: List[Player] = field(default_factory=list)
    state: GameState = GameState.WAITING
    category: str = '🌍 Страны'
    spy_count: int = 1
    word: Optional[str] = None
    message_id: Optional[int] = None
    
    def add_player(self, user_id: int, username: str, first_name: str) -> bool:
        """Добавить игрока в комнату"""
        if len(self.players) >= 10:
            return False
        if any(p.user_id == user_id for p in self.players):
            return False
        
        player = Player(user_id=user_id, username=username, first_name=first_name)
        self.players.append(player)
        return True
    
    def remove_player(self, user_id: int) -> bool:
        """Удалить игрока из комнаты"""
        self.players = [p for p in self.players if p.user_id != user_id]
        return True
    
    def get_player(self, user_id: int) -> Optional[Player]:
        """Получить игрока по ID"""
        for player in self.players:
            if player.user_id == user_id:
                return player
        return None
    
    def is_player_in_room(self, user_id: int) -> bool:
        """Проверить, находится ли игрок в комнате"""
        return any(p.user_id == user_id for p in self.players)
    
    def get_player_count(self) -> int:
        """Получить количество игроков"""
        return len(self.players)
    
    def can_start(self) -> bool:
        """Можно ли начать игру"""
        return self.get_player_count() >= 3 and self.state == GameState.WAITING

class Database:
    def init(self):
        self.rooms: Dict[str, GameRoom] = {}
        self.user_rooms: Dict[int, str] = {}  # user_id -> room_id
    
    def create_room(self, room_id: str, creator_id: int, username: str, first_name: str) -> GameRoom:
        """Создать новую комнату"""
        room = GameRoom(room_id=room_id, creator_id=creator_id)
        room.add_player(creator_id, username, first_name)
        self.rooms[room_id] = room
        self.user_rooms[creator_id] = room_id
        return room
    
    def get_room(self, room_id: str) -> Optional[GameRoom]:
        """Получить комнату по ID"""
        return self.rooms.get(room_id)
    
    def get_user_room(self, user_id: int) -> Optional[GameRoom]:
        """Получить комнату пользователя"""
        room_id = self.user_rooms.get(user_id)
        if room_id:
            return self.rooms.get(room_id)
        return None
    
    def delete_room(self, room_id: str):
        """Удалить комнату"""
        room = self.rooms.get(room_id)
        if room:
            # Удаляем связи пользователей с комнатой
            for player in room.players:
                if player.user_id in self.user_rooms:
                    del self.user_rooms[player.user_id]
            del self.rooms[room_id]
    
    def join_room(self, room_id: str, user_id: int, username: str, first_name: str) -> bool:
        """Присоединиться к комнате"""
        room = self.get_room(room_id)
        if not room or room.state != GameState.WAITING:
            return False
        
        if room.add_player(user_id, username, first_name):
            self.user_rooms[user_id] = room_id
            return True
        return False
    
    def leave_room(self, user_id: int) -> bool:
        """Покинуть комнату"""
        room = self.get_user_room(user_id)
        if not room:
            return False
        
        room.remove_player(user_id)
        if user_id in self.user_rooms:
            del self.user_rooms[user_id]

        # Если комната пуста или создатель вышел, удаляем комнату
        if len(room.players) == 0 or room.creator_id == user_id:
            self.delete_room(room.room_id)
            
        return True

# Глобальный экземпляр базы данных
db = Database()
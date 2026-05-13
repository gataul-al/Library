# FEATURE: Система выдачи и возврата - шаблонный метод, цепочка обязанностей
"""
Library Management System - Учет и управление библиотекой
Демонстрация ООП: абстрактные классы, наследование, композиция, агрегация,
миксины, интерфейсы, метакласс, фабрика, цепочка обязанностей,
шаблонный метод, декоратор, сериализация.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

# ------------------------- Настройка логирования -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("library.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Library")

# ------------------------- 11. Исключения -------------------------
class ItemNotAvailableError(Exception):
    pass

class PermissionDeniedError(Exception):
    pass

class ReaderNotFoundError(Exception):
    pass

# ------------------------- 4. Интерфейсы -------------------------
class Searchable(ABC):
    @abstractmethod
    def search_by_title(self, title: str) -> List['LibraryItem']:
        pass

class Reservable(ABC):
    @abstractmethod
    def reserve_item(self, reader: 'Reader', item: 'LibraryItem') -> str:
        pass

# ------------------------- 5. Миксины -------------------------
class LoggingMixin:
    def log_action(self, action: str):
        logger.info(f"[LOG] {self.__class__.__name__}: {action}")

class NotificationMixin:
    def send_notification(self, message: str):
        logger.info(f"[NOTIFICATION] {self.__class__.__name__}: {message}")
        print(f"🔔 Уведомление: {message}")

# ------------------------- 6. Метакласс LibraryItemMeta -------------------------
class LibraryItemMeta(type(ABC), type):
    _registry = {}
    
    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct)
        if name not in ["LibraryItem", "ABC"] and not name.startswith('_'):
            mcs._registry[name.lower()] = cls
        return cls
    
    @classmethod
    def get_registry(mcs) -> Dict[str, type]:
        return mcs._registry.copy()

# ------------------------- 1. Абстрактный класс LibraryItem -------------------------
class LibraryItem(ABC, metaclass=LibraryItemMeta):
    def __init__(self, item_id: str, title: str, author: str, year: int, is_available: bool = True):
        self._item_id = item_id
        self._title = title
        self._author = author
        self._year = year
        self._is_available = is_available
        logger.info(f"Создан ресурс: {self}")
    
    @property
    def item_id(self) -> str:
        return self._item_id
    
    @property
    def title(self) -> str:
        return self._title
    
    @title.setter
    def title(self, value: str):
        self._title = value
    
    @property
    def author(self) -> str:
        return self._author
    
    @author.setter
    def author(self, value: str):
        self._author = value
    
    @property
    def year(self) -> int:
        return self._year
    
    @year.setter
    def year(self, value: int):
        self._year = value
    
    @property
    def is_available(self) -> bool:
        return self._is_available
    
    def borrow(self):
        if not self._is_available:
            raise ItemNotAvailableError(f"Ресурс '{self._title}' недоступен")
        self._is_available = False
        logger.info(f"Ресурс '{self._title}' выдан")
    
    def return_item(self):
        self._is_available = True
        logger.info(f"Ресурс '{self._title}' возвращён")
    
    @abstractmethod
    def get_description(self) -> str:
        pass
    
    def __eq__(self, other):
        if not isinstance(other, LibraryItem):
            return NotImplemented
        return self._year == other._year and self._title == other._title
    
    def __lt__(self, other):
        if not isinstance(other, LibraryItem):
            return NotImplemented
        return (self._year, self._title) < (other._year, other._title)
    
    def __gt__(self, other):
        if not isinstance(other, LibraryItem):
            return NotImplemented
        return (self._year, self._title) > (other._year, other._title)
    
    def __str__(self) -> str:
        return f"Название: {self._title}, Автор: {self._author}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self._item_id,
            "title": self._title,
            "author": self._author,
            "year": self._year,
            "is_available": self._is_available,
            "type": self.__class__.__name__.lower()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LibraryItem':
        item_type = data.pop("type")
        factory = LibraryItemFactory()
        return factory.create_item(item_type, **data)

# ------------------------- 2. Подклассы (ИСПРАВЛЕНЫ) -------------------------
class Book(LibraryItem, LoggingMixin, NotificationMixin):
    def __init__(self, item_id: str, title: str, author: str, year: int, genre: str, is_available: bool = True):
        self.genre = genre
        super().__init__(item_id, title, author, year, is_available)
    
    def get_description(self) -> str:
        return f"Книга: {self._title}, Жанр: {self.genre}, Автор: {self._author}"
    
    def __str__(self) -> str:
        return f"Книга: {self._title}, Жанр: {self.genre}"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["genre"] = self.genre
        return data

class Magazine(LibraryItem, LoggingMixin, NotificationMixin):
    def __init__(self, item_id: str, title: str, author: str, year: int, issue_number: int, is_available: bool = True):
        self.issue_number = issue_number
        super().__init__(item_id, title, author, year, is_available)
    
    def get_description(self) -> str:
        return f"Журнал: {self._title}, Выпуск: {self.issue_number}, Автор: {self._author}"
    
    def __str__(self) -> str:
        return f"Журнал: {self._title}, Выпуск: {self.issue_number}"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["issue_number"] = self.issue_number
        return data

class Audiobook(LibraryItem, LoggingMixin, NotificationMixin):
    def __init__(self, item_id: str, title: str, author: str, year: int, duration: int, is_available: bool = True):
        self.duration = duration
        super().__init__(item_id, title, author, year, is_available)
    
    def get_description(self) -> str:
        return f"Аудиокнига: {self._title}, Продолжительность: {self.duration} мин., Автор: {self._author}"
    
    def __str__(self) -> str:
        return f"Аудиокнига: {self._title}, {self.duration} минут"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["duration"] = self.duration
        return data

# ------------------------- 7. Фабрика -------------------------
class LibraryItemFactory:
    @staticmethod
    def create_item(item_type: str, **kwargs) -> LibraryItem:
        registry = LibraryItemMeta.get_registry()
        item_type = item_type.lower()
        if item_type not in registry:
            raise ValueError(f"Неизвестный тип: {item_type}")
        return registry[item_type](**kwargs)

# ------------------------- 3. Композиция и агрегация -------------------------
class Address:
    def __init__(self, city: str, street: str, house: str, apartment: str = ""):
        self.city = city
        self.street = street
        self.house = house
        self.apartment = apartment
    
    def __str__(self) -> str:
        return f"{self.city}, {self.street}, {self.house} {self.apartment}"
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "city": self.city,
            "street": self.street,
            "house": self.house,
            "apartment": self.apartment
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Address':
        return cls(data["city"], data["street"], data["house"], data.get("apartment", ""))

class Reader:
    def __init__(self, name: str, reader_id: str, address: Address):
        self.name = name
        self.reader_id = reader_id
        self.address = address
        self._borrowed_items: List[LibraryItem] = []
    
    def borrow_item(self, item: LibraryItem):
        item.borrow()
        self._borrowed_items.append(item)
        logger.info(f"Читатель {self.name} взял '{item.title}'")
    
    def return_item(self, item: LibraryItem):
        item.return_item()
        self._borrowed_items.remove(item)
        logger.info(f"Читатель {self.name} вернул '{item.title}'")
    
    def get_borrowed_items(self) -> List[LibraryItem]:
        return self._borrowed_items.copy()
    
    def __str__(self) -> str:
        borrowed_titles = [item.title for item in self._borrowed_items]
        return f"Читатель: {self.name}, ID: {self.reader_id}, Адрес: {self.address}, Взято: {borrowed_titles}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "reader_id": self.reader_id,
            "address": self.address.to_dict(),
            "borrowed_ids": [item.item_id for item in self._borrowed_items]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], items_dict: Dict[str, LibraryItem]) -> 'Reader':
        addr = Address.from_dict(data["address"])
        reader = cls(data["name"], data["reader_id"], addr)
        for item_id in data.get("borrowed_ids", []):
            if item_id in items_dict:
                try:
                    reader.borrow_item(items_dict[item_id])
                except ItemNotAvailableError:
                    pass
        return reader

# ------------------------- 8. Цепочка обязанностей -------------------------
class ExtensionRequest:
    def __init__(self, reader: Reader, item: LibraryItem, weeks_requested: int):
        self.reader = reader
        self.item = item
        self.weeks_requested = weeks_requested
        self.approved_weeks = 0
        self.approved_by = None

class ExtensionHandler(ABC):
    def __init__(self):
        self._next_handler = None
    
    def set_next(self, handler):
        self._next_handler = handler
        return handler
    
    def handle(self, request: ExtensionRequest):
        if self.can_approve(request):
            request.approved_weeks = self.get_approval_weeks(request)
            request.approved_by = self.__class__.__name__
            print(f"✅ {self.__class__.__name__} одобрил продление на {request.approved_weeks} нед. для '{request.item.title}'")
        elif self._next_handler:
            self._next_handler.handle(request)
        else:
            print(f"❌ Продление отклонено для '{request.item.title}'")
    
    @abstractmethod
    def can_approve(self, request: ExtensionRequest) -> bool:
        pass
    
    @abstractmethod
    def get_approval_weeks(self, request: ExtensionRequest) -> int:
        pass

class Librarian(ExtensionHandler):
    def can_approve(self, request: ExtensionRequest) -> bool:
        return request.weeks_requested <= 1
    
    def get_approval_weeks(self, request: ExtensionRequest) -> int:
        return 1

class HeadLibrarian(ExtensionHandler):
    def can_approve(self, request: ExtensionRequest) -> bool:
        return request.weeks_requested <= 2
    
    def get_approval_weeks(self, request: ExtensionRequest) -> int:
        return 2

class Director(ExtensionHandler):
    def can_approve(self, request: ExtensionRequest) -> bool:
        return True
    
    def get_approval_weeks(self, request: ExtensionRequest) -> int:
        return request.weeks_requested

# ------------------------- 9. Шаблонный метод -------------------------
class BorrowProcess(ABC):
    def borrow_item(self, reader: Reader, item: LibraryItem) -> bool:
        print(f"\n--- Процесс выдачи '{item.title}' для {reader.name} ---")
        if not self.check_availability(item):
            return False
        self.update_item_status(item)
        self.add_to_reader(reader, item)
        self.send_confirmation(reader, item)
        return True
    
    @abstractmethod
    def check_availability(self, item: LibraryItem) -> bool:
        pass
    
    @abstractmethod
    def update_item_status(self, item: LibraryItem):
        pass
    
    @abstractmethod
    def add_to_reader(self, reader: Reader, item: LibraryItem):
        pass
    
    @abstractmethod
    def send_confirmation(self, reader: Reader, item: LibraryItem):
        pass

class BookBorrowProcess(BorrowProcess):
    def check_availability(self, item: LibraryItem) -> bool:
        available = item.is_available
        if not available:
            print(f"❌ Книга '{item.title}' недоступна")
        return available
    
    def update_item_status(self, item: LibraryItem):
        item.borrow()
    
    def add_to_reader(self, reader: Reader, item: LibraryItem):
        reader._borrowed_items.append(item)
    
    def send_confirmation(self, reader: Reader, item: LibraryItem):
        print(f"📚 Книга '{item.title}' выдана {reader.name}")
        if hasattr(item, 'send_notification'):
            item.send_notification(f"Книга '{item.title}' выдана {reader.name}")

class AudiobookBorrowProcess(BorrowProcess):
    def check_availability(self, item: LibraryItem) -> bool:
        available = item.is_available
        if not available:
            print(f"❌ Аудиокнига '{item.title}' недоступна")
        return available
    
    def update_item_status(self, item: LibraryItem):
        item.borrow()
    
    def add_to_reader(self, reader: Reader, item: LibraryItem):
        reader._borrowed_items.append(item)
    
    def send_confirmation(self, reader: Reader, item: LibraryItem):
        print(f"🎧 Аудиокнига '{item.title}' выдана {reader.name}")
        if hasattr(item, 'send_notification'):
            item.send_notification(f"Аудиокнига '{item.title}' выдана {reader.name}")

# ------------------------- 10. Декоратор прав доступа -------------------------
def check_permissions(required_role: str = "librarian"):
    def decorator(func):
        def wrapper(user_role: str, *args, **kwargs):
            if user_role != required_role and user_role != "admin":
                raise PermissionDeniedError(f"Требуется роль '{required_role}', у вас '{user_role}'")
            return func(*args, **kwargs)
        return wrapper
    return decorator

# ------------------------- Библиотека (управление данными) -------------------------
class Library(Searchable, Reservable):
    def __init__(self):
        self.items: Dict[str, LibraryItem] = {}
        self.readers: Dict[str, Reader] = {}
        self.reservations: Dict[str, str] = {}
    
    def add_item(self, item: LibraryItem):
        self.items[item.item_id] = item
        logger.info(f"Добавлен ресурс: {item.title}")
    
    def remove_item(self, item_id: str):
        if item_id in self.items:
            del self.items[item_id]
            logger.info(f"Удален ресурс {item_id}")
    
    def add_reader(self, reader: Reader):
        self.readers[reader.reader_id] = reader
        logger.info(f"Добавлен читатель: {reader.name}")
    
    def get_all_items(self) -> List[LibraryItem]:
        return list(self.items.values())
    
    def search_by_title(self, title: str) -> List[LibraryItem]:
        return [item for item in self.items.values() if title.lower() in item.title.lower()]
    
    def reserve_item(self, reader: Reader, item: LibraryItem) -> str:
        self.reservations[item.item_id] = reader.name
        message = f"Ресурс '{item.title}' забронирован для {reader.name}"
        logger.info(message)
        if hasattr(item, 'send_notification'):
            item.send_notification(message)
        return message
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items.values()],
            "readers": [reader.to_dict() for reader in self.readers.values()],
            "reservations": self.reservations
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Library':
        lib = cls()
        items_dict = {}
        for item_data in data.get("items", []):
            item = LibraryItemFactory.create_item(item_data["type"], **{k: v for k, v in item_data.items() if k != "type"})
            lib.add_item(item)
            items_dict[item.item_id] = item
        for reader_data in data.get("readers", []):
            reader = Reader.from_dict(reader_data, items_dict)
            lib.add_reader(reader)
        lib.reservations = data.get("reservations", {})
        return lib

# ------------------------- ТЕСТ -------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("БИБЛИОТЕКА - ТЕСТ")
    print("=" * 60)
    
    # Принудительная регистрация типов
    LibraryItemMeta._registry["book"] = Book
    LibraryItemMeta._registry["magazine"] = Magazine
    LibraryItemMeta._registry["audiobook"] = Audiobook
    
    # Создание ресурсов через фабрику
    factory = LibraryItemFactory()
    book = factory.create_item("book", item_id="B001", title="Мастер и Маргарита", 
                               author="Булгаков", year=1967, genre="Роман")
    magazine = factory.create_item("magazine", item_id="M001", title="Наука и жизнь",
                                   author="Редакция", year=2023, issue_number=5)
    audiobook = factory.create_item("audiobook", item_id="A001", title="1984",
                                    author="Оруэлл", year=1949, duration=720)
    
    # Адрес и читатель
    addr = Address("Москва", "Тверская", "15", "42")
    reader = Reader("Иван Петров", "R001", addr)
    
    # Библиотека
    library = Library()
    library.add_item(book)
    library.add_item(magazine)
    library.add_item(audiobook)
    library.add_reader(reader)
    
    print("\n--- Ресурсы библиотеки ---")
    for item in library.get_all_items():
        print(f"  {item}")
        print(f"   {item.get_description()}")
    
    print("\n--- Поиск по названию (Searchable) ---")
    found = library.search_by_title("Мастер")
    for item in found:
        print(f"  Найдено: {item.title}")
    
    print("\n--- Бронирование (Reservable) ---")
    library.reserve_item(reader, book)
    
    print("\n--- Выдача книги (шаблонный метод) ---")
    process = BookBorrowProcess()
    process.borrow_item(reader, book)
    
    print("\n--- Взятые читателем книги ---")
    for item in reader.get_borrowed_items():
        print(f"  {item.title}")
    
    print("\n--- Цепочка обязанностей (продление) ---")
    request = ExtensionRequest(reader, book, 3)
    librarian = Librarian()
    head = HeadLibrarian()
    director = Director()
    librarian.set_next(head).set_next(director)
    librarian.handle(request)
    
    print("\n--- Декоратор прав ---")
    @check_permissions("admin")
    def delete_item(item_id: str):
        print(f"Ресурс {item_id} удалён")
    
    delete_item("admin", "B001")
    try:
        delete_item("user", "B001")
    except PermissionDeniedError as e:
        print(f"Ошибка прав: {e}")
    
    print("\n--- Сериализация в JSON ---")
    library_data = library.to_dict()
    print(json.dumps(library_data, ensure_ascii=False, indent=2))
    
    print("\n✅ ВСЕ МОДУЛИ РАБОТАЮТ!")
import struct
import os
from typing import List, Tuple, Optional

class DFATFileSystem:
    # Константы файловой системы
    SIGNATURE = b'DFAT'  # Сигнатура ФС
    VERSION = 1          # Версия ФС
    BLOCK_SIZE = 512     # Размер блока в байтах
    MAX_FILES = 64       # Максимальное количество файлов
    MAX_FILENAME = 8     # Максимальная длина имени файла
    MAX_EXTENSION = 3    # Максимальная длина расширения
    
    # Флаги файлов
    FLAG_UNUSED = 0x00   # Запись не используется
    FLAG_FILE = 0x01     # Обычный файл
    FLAG_SYSTEM = 0x02   # Системный файл
    FLAG_DELETED = 0x80  # Удаленный файл
    
    def __init__(self, image_path: str, create: bool = False):
        """Инициализация файловой системы
        
        Args:
            image_path: Путь к файлу образа
            create: Создать новый образ если True
        """
        self.image_path = image_path
        
        if create:
            # Создаем новый образ
            self._create_new_image()
        else:
            # Проверяем существующий образ
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Проверяем сигнатуру и версию
            with open(image_path, 'rb') as f:
                signature = f.read(4)
                version = struct.unpack('B', f.read(1))[0]
                
                if signature != self.SIGNATURE:
                    raise ValueError("Invalid filesystem signature")
                if version != self.VERSION:
                    raise ValueError(f"Unsupported filesystem version: {version}")
    
    def _create_new_image(self):
        """Создает новый пустой образ файловой системы"""
        # Создаем образ размером 32KB
        with open(self.image_path, 'wb') as f:
            # Записываем суперблок
            f.write(self.SIGNATURE)  # Сигнатура
            f.write(struct.pack('B', self.VERSION))  # Версия
            f.write(struct.pack('H', self.BLOCK_SIZE))  # Размер блока
            f.write(struct.pack('H', self.MAX_FILES))  # Макс. количество файлов
            
            # Заполняем остаток суперблока нулями
            f.write(b'\x00' * (self.BLOCK_SIZE - 9))
            
            # Инициализируем таблицу файлов
            file_entry_size = self.MAX_FILENAME + self.MAX_EXTENSION + 5  # 8+3+2+2+1 = 16 байт
            f.write(b'\x00' * (self.MAX_FILES * file_entry_size))
            
            # Заполняем остаток образа нулями
            remaining_size = (32 * 1024) - self.BLOCK_SIZE - (self.MAX_FILES * file_entry_size)
            f.write(b'\x00' * remaining_size)
    
    def list_files(self) -> List[Tuple[str, int, int]]:
        """Возвращает список файлов в формате [(имя, размер, начальный_блок)]"""
        files = []
        
        with open(self.image_path, 'rb') as f:
            # Пропускаем суперблок
            f.seek(self.BLOCK_SIZE)
            
            # Читаем записи файлов
            for _ in range(self.MAX_FILES):
                entry = f.read(16)  # Размер записи файла
                
                # Проверяем флаг файла
                flags = entry[15]
                if flags == self.FLAG_FILE or flags == self.FLAG_SYSTEM:
                    # Извлекаем имя файла и расширение
                    name = entry[:8].decode('ascii').rstrip('\x00')
                    ext = entry[8:11].decode('ascii').rstrip('\x00')
                    if ext:
                        name = f"{name}.{ext}"
                    
                    # Извлекаем размер и начальный блок
                    size = struct.unpack('H', entry[11:13])[0]
                    start_block = struct.unpack('H', entry[13:15])[0]
                    
                    files.append((name, size, start_block))
        
        return files
    
    def create_file(self, filename: str, data: bytes) -> bool:
        """Создает новый файл в файловой системе
        
        Args:
            filename: Имя файла (с расширением)
            data: Содержимое файла
            
        Returns:
            True если файл создан успешно
        """
        # Проверяем размер данных
        if len(data) > (32 * 1024) - (2 * self.BLOCK_SIZE):
            raise ValueError("File too large")
        
        # Разбиваем имя файла на имя и расширение
        if '.' in filename:
            name, ext = filename.split('.')
        else:
            name, ext = filename, ''
            
        if len(name) > self.MAX_FILENAME:
            raise ValueError(f"Filename too long (max {self.MAX_FILENAME} chars)")
        if len(ext) > self.MAX_EXTENSION:
            raise ValueError(f"Extension too long (max {self.MAX_EXTENSION} chars)")
        
        with open(self.image_path, 'r+b') as f:
            # Ищем свободную запись в таблице файлов
            f.seek(self.BLOCK_SIZE)
            entry_pos = None
            
            for i in range(self.MAX_FILES):
                pos = self.BLOCK_SIZE + (i * 16)
                f.seek(pos + 15)  # Переходим к флагу
                flags = ord(f.read(1))
                
                if flags == self.FLAG_UNUSED or flags == self.FLAG_DELETED:
                    entry_pos = pos
                    break
            
            if entry_pos is None:
                raise RuntimeError("No free file entries")
            
            # Находим свободное место для данных
            # В этой простой реализации просто добавляем в конец
            f.seek(0, 2)  # Переходим в конец файла
            file_pos = f.tell()
            start_block = (file_pos + self.BLOCK_SIZE - 1) // self.BLOCK_SIZE
            
            # Записываем данные
            f.seek(start_block * self.BLOCK_SIZE)
            f.write(data)
            
            # Создаем запись файла
            f.seek(entry_pos)
            f.write(name.encode('ascii').ljust(8, b'\x00'))
            f.write(ext.encode('ascii').ljust(3, b'\x00'))
            f.write(struct.pack('H', len(data)))  # Размер
            f.write(struct.pack('H', start_block))  # Начальный блок
            f.write(bytes([self.FLAG_FILE]))  # Флаг
            
            return True
    
    def read_file(self, filename: str) -> Optional[bytes]:
        """Читает содержимое файла
        
        Args:
            filename: Имя файла
            
        Returns:
            Содержимое файла или None если файл не найден
        """
        with open(self.image_path, 'rb') as f:
            # Ищем файл в таблице файлов
            f.seek(self.BLOCK_SIZE)
            
            for _ in range(self.MAX_FILES):
                entry = f.read(16)
                name = entry[:8].decode('ascii').rstrip('\x00')
                ext = entry[8:11].decode('ascii').rstrip('\x00')
                if ext:
                    full_name = f"{name}.{ext}"
                else:
                    full_name = name
                
                flags = entry[15]
                if flags in (self.FLAG_FILE, self.FLAG_SYSTEM) and full_name == filename:
                    size = struct.unpack('H', entry[11:13])[0]
                    start_block = struct.unpack('H', entry[13:15])[0]
                    
                    # Читаем данные файла
                    f.seek(start_block * self.BLOCK_SIZE)
                    return f.read(size)
        
        return None
    
    def delete_file(self, filename: str) -> bool:
        """Удаляет файл из файловой системы
        
        Args:
            filename: Имя файла
            
        Returns:
            True если файл успешно удален
        """
        with open(self.image_path, 'r+b') as f:
            # Ищем файл в таблице файлов
            f.seek(self.BLOCK_SIZE)
            
            for i in range(self.MAX_FILES):
                pos = self.BLOCK_SIZE + (i * 16)
                f.seek(pos)
                entry = f.read(16)
                
                name = entry[:8].decode('ascii').rstrip('\x00')
                ext = entry[8:11].decode('ascii').rstrip('\x00')
                if ext:
                    full_name = f"{name}.{ext}"
                else:
                    full_name = name
                
                flags = entry[15]
                if flags in (self.FLAG_FILE, self.FLAG_SYSTEM) and full_name == filename:
                    # Помечаем файл как удаленный
                    f.seek(pos + 15)
                    f.write(bytes([self.FLAG_DELETED]))
                    return True
        
        return False

def main():
    """Тестирование файловой системы"""
    # Создаем новый образ
    fs = DFATFileSystem("test.img", create=True)
    
    # Создаем несколько файлов
    fs.create_file("test.txt", b"Hello, World!")
    fs.create_file("data.bin", b"Binary data")
    
    # Выводим список файлов
    print("Files:")
    for name, size, block in fs.list_files():
        print(f"- {name}: {size} bytes, starts at block {block}")
    
    # Читаем файл
    content = fs.read_file("test.txt")
    print(f"\nContent of test.txt: {content.decode()}")
    
    # Удаляем файл
    fs.delete_file("data.bin")
    
    print("\nAfter deletion:")
    for name, size, block in fs.list_files():
        print(f"- {name}: {size} bytes, starts at block {block}")

if __name__ == "__main__":
    main() 
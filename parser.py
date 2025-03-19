from dataclasses import dataclass
from typing import List, Optional
from lexer import Lexer, Token, TokenType

@dataclass
class FunctionArg:
    name: str
    reg: Optional[str] = None  # Теперь регистр опционален

class Parser:
    def __init__(self, lexer: Lexer, ctx, ftp):
        self.lexer = lexer
        self.ctx = ctx
        self.current_token = self.lexer.get_next_token()
        self.current_function = None
        self.function_args = {}  # имя функции -> список аргументов
        self.imported_files = set()  # множество импортированных файлов
        self.lib_vars = {}  # имя -> путь к файлу
        self.var_types = {}  # имя -> тип переменной (char, num16, num24)
        self.file_to_parse = ftp
        self.is_boot = False
        self.available_regs = ['ax', 'bx', 'cx', 'dx', 'si']  # Доступные регистры для аргументов
    
    def error(self, message: str):
        raise SyntaxError(f"{message} at line {self.current_token.line}, column {self.current_token.column} in file {self.file_to_parse}")
    
    def eat(self, token_type: TokenType):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error(f"Expected {token_type}, got {self.current_token.type}")
    
    def parse(self) -> str:
        self.ctx.is_boot = self.is_boot
        """Основной метод парсинга"""
        while self.current_token.type != TokenType.EOF:
            print(f"{self.current_token} FILE: {self.file_to_parse}")
            if self.current_token.type == TokenType.AT:
                # Обрабатываем @incl
                self.eat(TokenType.AT)
                if self.current_token.type == TokenType.IDENT and self.current_token.value == "incl":
                    self.eat(TokenType.IDENT)
                    self.parse_include()
                else:
                    self.error("Expected 'incl' after @")
            elif self.current_token.type == TokenType.BOX:
                self.parse_box()
            elif self.current_token.type == TokenType.CHAR:
                self.parse_variable("char")
            elif self.current_token.type == TokenType.NUM16:
                self.parse_variable("num16")
            elif self.current_token.type == TokenType.NUM24:
                self.parse_variable("num24")
            elif self.current_token.type == TokenType.LIB:
                self.parse_variable("lib")
            elif self.current_token.type == TokenType.KASM:
                self.parse_kasm()
            else:
                self.error(f"Unexpected token {self.current_token.type}")
        
        return self.ctx.generate()
    
    def parse_include(self):
        """Парсит директиву импорта"""
        # Проверяем тип импорта (стандартная библиотека или локальный файл)
        is_stdlib = False
        if self.current_token.type == TokenType.ANGLE_OPEN:
            self.eat(TokenType.ANGLE_OPEN)
            is_stdlib = True
        elif self.current_token.type == TokenType.STRING:
            pass
        else:
            self.error("Expected < or \" after incl")
        
        # Читаем путь к файлу
        if is_stdlib:
            # Для стандартной библиотеки читаем имя модуля
            if self.current_token.type != TokenType.IDENT:
                self.error("Expected module name in <>")
            module = self.current_token.value
            self.eat(TokenType.IDENT)
            
            # Проверяем на точку и расширение
            if self.current_token.type == TokenType.DOT:
                self.eat(TokenType.DOT)
                if self.current_token.type != TokenType.IDENT:
                    self.error("Expected module extension after dot")
                ext = self.current_token.value
                self.eat(TokenType.IDENT)
                module = f"{module}.{ext}"
            
            self.eat(TokenType.ANGLE_CLOSE)
            path = f"stdlib/{module}"
            if not path.endswith('.asm'):
                path += '.asm'
        else:
            # Для локального файла читаем путь из строки
            path = self.current_token.value
            self.eat(TokenType.STRING)
            
            # Пробуем найти файл с разными расширениями
            base_path = path.replace('.', '/')
            for ext in ['.box', '.asm']:
                try:
                    with open(base_path + ext, 'r') as f:
                        path = base_path + ext
                        break
                except FileNotFoundError:
                    continue
        
        # Проверяем, не был ли файл уже импортирован
        if path not in self.imported_files:
            self.imported_files.add(path)
            
            try:
                with open(path, 'r') as f:
                    source = f.read()
                
                # Проверяем расширение файла
                if path.endswith('.box'):
                    # .box файлы нужно парсить
                    lexer = Lexer(source)
                    parser = Parser(lexer, self.ctx, path)
                    # Если мы внутри lib-переменной, передаем префикс
                    if hasattr(self, 'lib_prefix'):
                        parser.lib_prefix = self.lib_prefix
                    parser.parse_without_generate()
                else:
                    # .asm файлы добавляем как есть, но добавляем префикс к меткам и их вызовам
                    lines = source.split('\n')
                    modified_lines = []
                    
                    # Сначала собираем все метки в файле
                    labels = set()
                    for line in lines:
                        line = line.strip()
                        if line.endswith(':'):
                            label = line[:-1].strip()
                            if not label.startswith('.'):  # Пропускаем локальные метки
                                labels.add(label)
                    
                    # Получаем префикс из текущего контекста
                    prefix = self.lib_prefix if hasattr(self, 'lib_prefix') else ""
                    
                    # Теперь обрабатываем каждую строку
                    for line in lines:
                        line = line.strip()
                        if line.endswith(':'):
                            # Это метка
                            label = line[:-1].strip()
                            if label.startswith('.'):
                                modified_lines.append(f"{label}:")
                            else:
                                modified_lines.append(f"{prefix}{label}:")
                        else:
                            # Проверяем, есть ли в строке вызов функции (call)
                            if 'call' in line:
                                parts = line.split('call', 1)
                                prefix_part = parts[0]
                                func = parts[1].strip()
                                # Если вызываемая функция есть в списке меток и не начинается с точки
                                if func in labels and not func.startswith('.'):
                                    modified_lines.append(f"{prefix_part}call {prefix}{func}")
                                else:
                                    modified_lines.append(line)
                            else:
                                modified_lines.append(line)
                    
                    self.ctx.add_imported_code('\n'.join(modified_lines))
            except FileNotFoundError:
                self.error(f"Could not find file: {path}")
    
    def parse_without_generate(self):
        """Парсит файл без генерации финального кода"""
        while self.current_token.type != TokenType.EOF:
            if self.current_token.type == TokenType.AT:
                # Обрабатываем @incl
                self.eat(TokenType.AT)
                if self.current_token.type == TokenType.IDENT and self.current_token.value == "incl":
                    self.eat(TokenType.IDENT)
                    self.parse_include()
                else:
                    self.error("Expected 'incl' after @")
            elif self.current_token.type == TokenType.BOX:
                self.parse_box()
            elif self.current_token.type == TokenType.CHAR:
                self.parse_variable("char")
            elif self.current_token.type == TokenType.NUM16:
                self.parse_variable("num16")
            elif self.current_token.type == TokenType.NUM24:
                self.parse_variable("num24")
            elif self.current_token.type == TokenType.LIB:
                self.parse_variable("lib")
            elif self.current_token.type == TokenType.KASM:
                self.parse_kasm()
            elif self.current_token.type == TokenType.IF:
                self.parse_if()
            else:
                self.error(f"Unexpected token {self.current_token.type}")
    
    def parse_box(self):
        """Парсит box-функцию"""
        self.eat(TokenType.BOX)
        
        # Имя функции
        if self.current_token.type != TokenType.IDENT:
            self.error("Expected function name")
        name = self.current_token.value
        self.eat(TokenType.IDENT)
        
        # Если есть префикс lib-переменной, добавляем его к имени функции
        if hasattr(self, 'lib_prefix'):
            name = self.lib_prefix + name
        
        # Сохраняем текущую функцию
        self.current_function = name
        
        # Аргументы функции
        args = []
        if self.current_token.type == TokenType.BRACKET_OPEN:
            self.eat(TokenType.BRACKET_OPEN)
            while self.current_token.type == TokenType.IDENT:
                # Теперь просто читаем имя аргумента
                arg_name = self.current_token.value
                self.eat(TokenType.IDENT)
                args.append(FunctionArg(name=arg_name))
                
                if self.current_token.type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
                elif self.current_token.type != TokenType.BRACKET_CLOSE:
                    self.error("Expected comma between arguments or closing bracket")
            
            self.eat(TokenType.BRACKET_CLOSE)
        
        # Сохраняем аргументы функции
        if args:
            self.function_args[name] = args
        
        # Начинаем функцию
        self.ctx.start_function(name)
        
        # Добавляем код для получения аргументов из стека
        if args:
            # Сохраняем base pointer
            self.ctx.add_asm("  push %bp")
            self.ctx.add_asm("  mov %bp %sp")
            
            # Распределяем регистры для аргументов
            available_regs = self.available_regs.copy()
            for i, arg in enumerate(args):
                if available_regs:
                    reg = available_regs.pop(0)
                    arg.reg = reg
                    
                    # Создаем последовательность команд для загрузки значения
                    # Сначала получаем адрес аргумента в стеке
                    self.ctx.add_asm(f"  mov %{reg} %bp")  # Копируем bp в регистр
                    
                    # Теперь нам нужно добавить смещение. Так как у нас нет команды add с константой,
                    # мы будем использовать временный регистр gi
                    offset = 6 + i * 3  # Первый аргумент на 6, каждый следующий +3
                    
                    # Добавляем смещение к регистру
                    self.ctx.add_asm(f"  add %{reg} ${offset:X}")
                    
                    # Теперь у нас в регистре адрес аргумента, загружаем значение
                    self.ctx.add_asm(f"  mov %sp %{reg}")  # Перемещаем sp на адрес аргумента
                    self.ctx.add_asm(f"  pop %{reg}")     # Читаем значение в регистр
                    self.ctx.add_asm(f"  mov %sp %bp")    # Восстанавливаем sp
        
        # Тело функции
        self.eat(TokenType.PAREN_OPEN)
        
        # Сохраняем маппинг аргументов для использования в kasm
        self.current_reg_map = {arg.name: arg.reg for arg in args if arg.reg}
        
        while self.current_token.type != TokenType.PAREN_CLOSE:
            if self.current_token.type == TokenType.CHAR:
                self.parse_variable("char")
            elif self.current_token.type == TokenType.NUM16:
                self.parse_variable("num16")
            elif self.current_token.type == TokenType.LIB:
                self.parse_variable("lib")
            elif self.current_token.type == TokenType.KASM:
                self.parse_kasm()
            elif self.current_token.type == TokenType.OPEN:
                self.parse_open()
            elif self.current_token.type == TokenType.LOOP:
                self.parse_loop()
            elif self.current_token.type == TokenType.GOTO:
                self.parse_goto()
            elif self.current_token.type == TokenType.JUMP:
                self.parse_jump()
            elif self.current_token.type == TokenType.IF:
                self.parse_if()
            elif self.current_token.type == TokenType.HASH:
                # Локальная метка
                self.eat(TokenType.HASH)
                if self.current_token.value in self.lexer.keywords:
                    self.current_token.type = TokenType.IDENT
                    self.current_token.value + str("_l")

                if self.current_token.type != TokenType.IDENT:
                    self.error("Expected label name after #")
                label = self.current_token.value
                self.eat(TokenType.IDENT)
                self.ctx.add_asm(f".{label}:")
            elif self.current_token.type == TokenType.IDENT:
                # Проверяем, является ли это вызовом через lib
                lib_var = self.current_token.value
                self.eat(TokenType.IDENT)
                
                if self.current_token.type == TokenType.ARROW:
                    # Это вызов через lib
                    self.eat(TokenType.ARROW)
                    
                    if self.current_token.type != TokenType.IDENT:
                        self.error("Expected function name after ->")
                    func_name = self.current_token.value
                    self.eat(TokenType.IDENT)
                    
                    # Аргументы вызова
                    args = []
                    if self.current_token.type == TokenType.BRACKET_OPEN:
                        self.eat(TokenType.BRACKET_OPEN)
                        while self.current_token.type in {TokenType.IDENT, TokenType.INT, TokenType.HEX, TokenType.STRING}:
                            if self.current_token.type == TokenType.INT:
                                # Числовой аргумент
                                args.append(str(self.current_token.value))
                                self.eat(TokenType.INT)
                            elif self.current_token.type == TokenType.HEX:
                                # Шестнадцатеричный аргумент
                                args.append(str(int(self.current_token.value[1:], 16)))
                                self.eat(TokenType.HEX)
                            elif self.current_token.type == TokenType.STRING:
                                # Строковый литерал
                                value = self.current_token.value
                                self.eat(TokenType.STRING)
                                # Добавляем строковый литерал и получаем его метку
                                label = self.ctx.add_string_literal(value)
                                args.append(label)
                            else:
                                args.append(self.current_token.value)
                                self.eat(TokenType.IDENT)
                            
                            if self.current_token.type == TokenType.COMMA:
                                self.eat(TokenType.COMMA)
                        self.eat(TokenType.BRACKET_CLOSE)
                    
                    # Генерируем код вызова
                    # Передаем аргументы через стек
                    for arg in reversed(args):  # Аргументы помещаются в стек в обратном порядке
                        if arg.isdigit():
                            # Числовой аргумент
                            self.ctx.add_asm(f"  push {arg}")
                        else:
                            # Переменная
                            self.ctx.add_asm(f"  mov %gi {arg}")
                            self.ctx.add_asm(f"  push %gi")
                    
                    self.ctx.add_asm(f"  call {lib_var}_{func_name}")
                    # Очищаем стек от аргументов
                    if args:
                        self.ctx.add_asm(f"  mov %gi %sp")
                        self.ctx.add_asm(f"  add %gi {len(args) * 3 + 3}")
                        self.ctx.add_asm(f"  mov %sp %gi")
                else:
                    self.error(f"Unexpected identifier in function body: {lib_var}")
            else:
                self.error(f"Unexpected token in function body: {self.current_token.type}")
        self.eat(TokenType.PAREN_CLOSE)
        
        # Восстанавливаем стек и добавляем ret
        if args:
            self.ctx.add_asm("  mov %sp %bp")
            self.ctx.add_asm("  pop %bp")
        self.ctx.add_asm("  ret")
        
        # Очищаем текущую функцию и маппинг регистров
        self.current_function = None
        self.current_reg_map = None
    
    def parse_variable(self, var_type: str):
        """Парсит объявление переменной"""
        if var_type == "lib":
            self.eat(TokenType.LIB)
        else:
            self.eat(TokenType.CHAR if var_type == "char" else (TokenType.NUM16 if var_type == "num16" else TokenType.NUM24))
        
        if self.current_token.type != TokenType.IDENT:
            self.error("Expected variable name")
        name = self.current_token.value
        self.eat(TokenType.IDENT)
        
        # Сохраняем тип переменной
        if var_type != "lib":
            self.var_types[name] = var_type
        
        self.eat(TokenType.COLON)
        
        if var_type == "lib":
            # Обрабатываем lib переменную
            if self.current_token.type != TokenType.IDENT or self.current_token.value != "incl":
                self.error("Expected 'incl' after :")
            self.eat(TokenType.IDENT)
            
            # Проверяем тип импорта (стандартная библиотека или локальный файл)
            is_stdlib = False
            if self.current_token.type == TokenType.ANGLE_OPEN:
                self.eat(TokenType.ANGLE_OPEN)
                is_stdlib = True
            elif self.current_token.type != TokenType.STRING:
                self.error("Expected < or \" after incl")
            
            if is_stdlib:
                # Для стандартной библиотеки читаем имя модуля
                if self.current_token.type != TokenType.IDENT:
                    self.error("Expected module name in <>")
                module = self.current_token.value
                self.eat(TokenType.IDENT)
                
                # Проверяем на точку и расширение
                if self.current_token.type == TokenType.DOT:
                    self.eat(TokenType.DOT)
                    if self.current_token.type != TokenType.IDENT:
                        self.error("Expected module extension after dot")
                    ext = self.current_token.value
                    self.eat(TokenType.IDENT)
                    module = f"{module}.{ext}"
                
                self.eat(TokenType.ANGLE_CLOSE)
                path = f"stdlib/{module}"
                if not path.endswith('.asm'):
                    path += '.asm'
            else:
                # Для локального файла читаем путь из строки
                path = self.current_token.value
                self.eat(TokenType.STRING)
                
                # Пробуем найти файл с разными расширениями
                base_path = path.replace('.', '/')
                for ext in ['.box', '.asm']:
                    try:
                        with open(base_path + ext, 'r') as f:
                            path = base_path + ext
                            break
                    except FileNotFoundError:
                        continue
            
            # Сохраняем путь к файлу
            self.lib_vars[name] = path
            
            try:
                with open(path, 'r') as f:
                    source = f.read()
                
                # Проверяем расширение файла
                if path.endswith('.box'):
                    # .box файлы нужно парсить
                    lexer = Lexer(source)
                    parser = Parser(lexer, self.ctx, path)
                    # Сохраняем имя lib-переменной для добавления префикса к функциям
                    parser.lib_prefix = name + "_"
                    parser.parse_without_generate()
                else:
                    # .asm файлы добавляем как есть, но добавляем префикс к меткам и их вызовам
                    lines = source.split('\n')
                    modified_lines = []
                    
                    # Сначала собираем все метки в файле
                    labels = set()
                    for line in lines:
                        line = line.strip()
                        if line.endswith(':'):
                            label = line[:-1].strip()
                            if not label.startswith('.'):  # Пропускаем локальные метки
                                labels.add(label)
                    
                    # Теперь обрабатываем каждую строку
                    for line in lines:
                        line = line.strip()
                        if line.endswith(':'):
                            # Это метка
                            label = line[:-1].strip()
                            if label.startswith('.'):
                                modified_lines.append(f"{label}:")
                            else:
                                modified_lines.append(f"{name}_{label}:")
                        else:
                            # Проверяем, есть ли в строке вызов функции (call)
                            if 'call ' in line:
                                parts = line.split('call ', 1)
                                prefix = parts[0]
                                func = parts[1].strip()
                                # Если вызываемая функция есть в списке меток и не начинается с точки
                                if func in labels and not func.startswith('.'):
                                    modified_lines.append(f"{prefix}call {name}_{func}")
                                else:
                                    modified_lines.append(line)
                            else:
                                modified_lines.append(line)
                    
                    self.ctx.add_imported_code('\n'.join(modified_lines))
            except FileNotFoundError:
                self.error(f"Could not find file: {path}")
        elif self.current_token.type == TokenType.RESERVE:
            # Резервирование памяти
            self.eat(TokenType.RESERVE)
            if self.current_token.type != TokenType.INT:
                self.error("Expected size after ?")
            size = self.current_token.value
            self.eat(TokenType.INT)
            if (var_type == "char"):
                pass
            elif (var_type == "num16"):
                size = size*2
            elif (var_type == "num24"):
                size = size*3

            self.ctx.reserve(name, size, "byte")
        elif var_type == "char" and self.current_token.type == TokenType.ARRAY:
            # Массив символов через Array
            self.eat(TokenType.ARRAY)
            self.eat(TokenType.CURLY_OPEN)
            values = []
            while self.current_token.type != TokenType.CURLY_CLOSE:
                if self.current_token.type == TokenType.CHAR_LIT:
                    c = self.current_token.value
                    if c == '$':
                        values.append("$0A")  # перевод строки
                    elif c == '^':
                        self.eat(TokenType.CHAR_LIT)
                        if self.current_token.value == '@':
                            values.append("$00")  # нулевой байт
                        self.eat(TokenType.CHAR_LIT)
                        continue
                    else:
                        values.append(f"${ord(c):02X}")
                elif self.current_token.type == TokenType.HEX:
                    values.append(self.current_token.value)
                self.eat(self.current_token.type)
                # Пропускаем запятую, если она есть
                if self.current_token.type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
            self.eat(TokenType.CURLY_CLOSE)
            # Добавляем нулевой байт в конец строки
            values.append("$00")
            self.ctx.add_variable(name, " ".join(values))
        elif var_type == "char" and self.current_token.type == TokenType.CURLY_OPEN:
            # Массив символов через {}
            self.eat(TokenType.CURLY_OPEN)
            values = []
            while self.current_token.type != TokenType.CURLY_CLOSE:
                if self.current_token.type == TokenType.CHAR_LIT:
                    c = self.current_token.value
                    if c == '$':
                        values.append("$0A")  # перевод строки
                    elif c == '^':
                        self.eat(TokenType.CHAR_LIT)
                        if self.current_token.value == '@':
                            values.append("$00")  # нулевой байт
                        self.eat(TokenType.CHAR_LIT)
                        continue
                    else:
                        values.append(f"${ord(c):02X}")
                elif self.current_token.type == TokenType.HEX:
                    values.append(self.current_token.value)
                self.eat(self.current_token.type)
                # Пропускаем запятую, если она есть
                if self.current_token.type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
            self.eat(TokenType.CURLY_CLOSE)
            values.append("$00")
            self.ctx.add_variable(name, " ".join(values))
        elif var_type == "num16":
            # Числовое значение
            if self.current_token.type == TokenType.HEX:
                value = self.current_token.value
            else:
                value = f"${self.current_token.value:04X}"

            num_value = self.current_token.value
            self.eat(self.current_token.type)
            # Разбиваем на старший и младший байты
            byte_high = (num_value >> 8) & 0xFF
            byte_low = num_value & 0xFF
            value = f"${byte_low:02X} ${byte_high:02X}"
            self.ctx.add_variable(name, value)
        elif var_type == "num24":
            # Числовое значение
            if self.current_token.type == TokenType.HEX:
                value = self.current_token.value
            else:
                value = f"${self.current_token.value:06X}"
            num_value = self.current_token.value
            self.eat(self.current_token.type)
            # Разбиваем на три байта
            byte_high = (num_value >> 16) & 0xFF
            byte_mid = (num_value >> 8) & 0xFF
            byte_low = num_value & 0xFF
            value = f"${byte_low:02X} ${byte_mid:02X} ${byte_high:02X}"
            self.ctx.add_variable(name, value)
    
    def parse_kasm(self):
        """Парсит ассемблерную вставку"""
        self.eat(TokenType.KASM)
        self.eat(TokenType.BRACKET_OPEN)
        if self.current_token.type != TokenType.STRING:
            self.error("Expected string in kasm[]")
        
        # Заменяем имена аргументов на регистры
        code = self.current_token.value
        if hasattr(self, 'current_reg_map') and self.current_reg_map:
            for name, reg in self.current_reg_map.items():
                code = code.replace(name, f"%{reg}")
        
        # Обрабатываем вызовы функций внутри ассемблерного кода
        if hasattr(self, 'lib_prefix') and 'call ' in code:
            parts = code.split('call ', 1)
            prefix = parts[0]
            func = parts[1].strip()
            # Если функция не начинается с точки (не локальная) и не содержит префикс
            if not func.startswith('.') and not '_' in func:
                code = f"{prefix}call {self.lib_prefix}{func}"
        
        self.ctx.add_asm(f"  {code}")
        self.eat(TokenType.STRING)
        self.eat(TokenType.BRACKET_CLOSE)
    
    def parse_open(self):
        """Парсит вызов функции"""
        self.eat(TokenType.OPEN)
        
        if self.current_token.type != TokenType.IDENT:
            self.error("Expected function name after open")
        
        # Получаем имя функции
        func_name = self.current_token.value
        self.eat(TokenType.IDENT)
        
        # Если мы внутри lib-файла, добавляем префикс
        if hasattr(self, 'lib_prefix'):
            func_name = self.lib_prefix + func_name
        
        # Аргументы вызова
        args = []
        if self.current_token.type == TokenType.BRACKET_OPEN:
            self.eat(TokenType.BRACKET_OPEN)
            while self.current_token.type in {TokenType.IDENT, TokenType.INT, TokenType.HEX, TokenType.STRING}:
                print(self.current_token.type)
                if self.current_token.type == TokenType.INT:
                    # Числовой аргумент
                    args.append(str(self.current_token.value))
                    self.eat(TokenType.INT)
                elif self.current_token.type == TokenType.HEX:
                    # Шестнадцатеричный аргумент
                    args.append(str(int(self.current_token.value[1:], 16)))
                    self.eat(TokenType.HEX)
                elif self.current_token.type == TokenType.STRING:
                    # Строковый литерал
                    value = self.current_token.value
                    self.eat(TokenType.STRING)
                    # Добавляем строковый литерал и получаем его метку
                    label = self.ctx.add_string_literal(value)
                    args.append(label)
                else:
                    # Проверяем, является ли идентификатор параметром функции
                    arg_name = self.current_token.value
                    self.eat(TokenType.IDENT)
                    
                    # Если у нас есть маппинг регистров и аргумент в нем есть
                    if hasattr(self, 'current_reg_map') and arg_name in self.current_reg_map:
                        # Используем регистр вместо имени аргумента
                        args.append(f"%{self.current_reg_map[arg_name]}")
                    else:
                        # Иначе используем имя переменной как есть
                        args.append(arg_name)
                
                if self.current_token.type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
            self.eat(TokenType.BRACKET_CLOSE)
        
        # Генерируем код вызова
        # Передаем аргументы через стек
        for arg in reversed(args):  # Аргументы помещаются в стек в обратном порядке
            if arg.isdigit():
                # Числовой аргумент
                self.ctx.add_asm(f"  push {arg}")
            elif arg.startswith("%"):
                # Это регистр (параметр функции)
                self.ctx.add_asm(f"  push {arg}")
            else:
                # Переменная или метка строкового литерала
                self.ctx.add_asm(f"  mov %gi {arg}")
                self.ctx.add_asm(f"  push %gi")
        
        self.ctx.add_asm(f"  call {func_name}")
        # Очищаем стек от аргументов
        if args:
            self.ctx.add_asm(f"  mov %gi %sp")
            self.ctx.add_asm(f"  add %gi {len(args) * 3}")
            self.ctx.add_asm(f"  mov %sp %gi")
    
    def parse_loop(self):
        """Парсит конструкцию loop"""
        self.eat(TokenType.LOOP)
        self.eat(TokenType.BRACKET_OPEN)
        
        # Читаем метку
        if self.current_token.type != TokenType.HASH:
            self.error("Expected local label (#) in loop")
        self.eat(TokenType.HASH)
        if self.current_token.type != TokenType.IDENT:
            self.error("Expected label name after #")
        label = self.current_token.value
        self.eat(TokenType.IDENT)
        
        self.eat(TokenType.COMMA)
        
        # Читаем переменную для проверки
        if self.current_token.type != TokenType.IDENT:
            self.error("Expected variable name in loop")
        var = self.current_token.value
        self.eat(TokenType.IDENT)
        
        self.eat(TokenType.BRACKET_CLOSE)
        
        # Генерируем код проверки и перехода
        self.ctx.add_asm(f"  mov %si {var}")
        # Выбираем правильную команду загрузки в зависимости от типа переменной
        var_type = self.var_types.get(var)
        if var_type == "char":
            self.ctx.add_asm(f"  lodb %si %gi")
        elif var_type == "num16":
            self.ctx.add_asm(f"  lodw %si %gi")
        else:  # num24 или неизвестный тип
            self.ctx.add_asm(f"  lodh %si %gi")
        self.ctx.add_asm(f"  cmp %gi $00")
        self.ctx.add_asm(f"  jg .{label}")
    
    def parse_goto(self):
        """Парсит конструкцию goto"""
        self.eat(TokenType.GOTO)
        self.eat(TokenType.BRACKET_OPEN)
        
        # Читаем метку
        if self.current_token.type != TokenType.HASH:
            self.error("Expected local label (#) in goto")
        self.eat(TokenType.HASH)
        if self.current_token.type != TokenType.IDENT:
            self.error("Expected label name after #")
        label = self.current_token.value
        self.eat(TokenType.IDENT)
        
        self.eat(TokenType.COMMA)
        
        # Читаем переменную для проверки
        if self.current_token.type != TokenType.IDENT:
            self.error("Expected variable name in goto")
        var = self.current_token.value
        self.eat(TokenType.IDENT)
        
        self.eat(TokenType.COMMA)
        
        # Читаем значение для сравнения
        if self.current_token.type == TokenType.INT:
            # Числовое значение
            value = f"${self.current_token.value:02X}"
            self.eat(TokenType.INT)
        elif self.current_token.type == TokenType.HEX:
            # Шестнадцатеричное значение
            value = self.current_token.value
            self.eat(TokenType.HEX)
        elif self.current_token.type == TokenType.CHAR_LIT:
            # Символьное значение (преобразуем в ASCII)
            value = f"${ord(self.current_token.value):02X}"
            self.eat(TokenType.CHAR_LIT)
        else:
            self.error("Expected number, hex or char value for comparison")
        
        self.eat(TokenType.BRACKET_CLOSE)
        
        # Генерируем код проверки и перехода
        self.ctx.add_asm(f"  mov %si {var}")
        # Выбираем правильную команду загрузки в зависимости от типа переменной
        var_type = self.var_types.get(var)
        if var_type == "char":
            self.ctx.add_asm(f"  lodb %si %gi")
        elif var_type == "num16":
            self.ctx.add_asm(f"  lodw %si %gi")
        else:  # num24 или неизвестный тип
            self.ctx.add_asm(f"  lodh %si %gi")
        self.ctx.add_asm(f"  cmp %gi {value}")
        self.ctx.add_asm(f"  je .{label}")


    def parse_jump(self):
        self.eat(TokenType.JUMP)
        self.eat(TokenType.BRACKET_OPEN)
        if self.current_token.type != TokenType.HASH:
            self.error("Expected local label (#) in jump")
        self.eat(TokenType.HASH)
        if self.current_token.type != TokenType.IDENT:
            self.error("Expected label name after #")
        label = self.current_token.value
        self.eat(TokenType.IDENT)  
        self.eat(TokenType.BRACKET_CLOSE)
        
        self.ctx.add_asm(f"   jmp .{label}")


    def parse_if(self):
        """Парсит конструкцию if"""
        self.eat(TokenType.IF)
        self.eat(TokenType.BRACKET_OPEN)
        
        # Читаем переменную для сравнения
        if self.current_token.type != TokenType.IDENT:
            self.error("Expected variable name in if condition")
        var = self.current_token.value
        self.eat(TokenType.IDENT)
        
        # Читаем оператор сравнения (пока поддерживаем только ==)
        if self.current_token.type != TokenType.EQ:
            self.error("Expected == in if condition")
        self.eat(TokenType.EQ)
        self.eat(TokenType.EQ)
        
        # Читаем значение для сравнения
        if self.current_token.type == TokenType.INT:
            # Числовое значение
            value = f"$000{self.current_token.value:03X}"  # 24-битное значение
            self.eat(TokenType.INT)
        elif self.current_token.type == TokenType.HEX:
            # Шестнадцатеричное значение
            value = self.current_token.value
            self.eat(TokenType.HEX)
        else:
            self.error("Expected number or hex value for comparison")
        
        self.eat(TokenType.BRACKET_CLOSE)
        
        # Увеличиваем счетчик if-блоков
        if not hasattr(self, 'if_counter'):
            self.if_counter = 0
        self.if_counter += 1
        
        # Генерируем код проверки и перехода
        self.ctx.add_asm(f"  mov %si {var}")
        
        # Выбираем правильную команду загрузки в зависимости от типа переменной
        var_type = self.var_types.get(var)
        if var_type == "char":
            self.ctx.add_asm(f"  lodb %si %gi")
        elif var_type == "num16":
            self.ctx.add_asm(f"  lodw %si %gi")
        else:  # num24 или неизвестный тип
            self.ctx.add_asm(f"  lodh %si %gi")
            
        self.ctx.add_asm(f"  cmp %gi {value}")
        self.ctx.add_asm(f"  jne .END_{self.if_counter}")
        self.ctx.add_asm(f".IF_{self.if_counter}:")
        
        self.eat(TokenType.PAREN_OPEN)
        # Парсим тело if-блока
        while self.current_token.type != TokenType.PAREN_CLOSE:
            if self.current_token.type == TokenType.CHAR:
                self.parse_variable("char")
            elif self.current_token.type == TokenType.NUM16:
                self.parse_variable("num16")
            elif self.current_token.type == TokenType.LIB:
                self.parse_variable("lib")
            elif self.current_token.type == TokenType.KASM:
                self.parse_kasm()
            elif self.current_token.type == TokenType.OPEN:
                self.parse_open()
            elif self.current_token.type == TokenType.LOOP:
                self.parse_loop()
            elif self.current_token.type == TokenType.GOTO:
                self.parse_goto()
            elif self.current_token.type == TokenType.JUMP:
                self.parse_jump()
            elif self.current_token.type == TokenType.IF:
                self.parse_if()
            elif self.current_token.type == TokenType.IDENT:
                # Проверяем, является ли это вызовом через lib
                lib_var = self.current_token.value
                self.eat(TokenType.IDENT)
                
                if self.current_token.type == TokenType.ARROW:
                    # Это вызов через lib
                    self.eat(TokenType.ARROW)
                    
                    if self.current_token.type != TokenType.IDENT:
                        self.error("Expected function name after ->")
                    func_name = self.current_token.value
                    self.eat(TokenType.IDENT)
                    
                    # Аргументы вызова
                    args = []
                    if self.current_token.type == TokenType.BRACKET_OPEN:
                        self.eat(TokenType.BRACKET_OPEN)
                        while self.current_token.type in {TokenType.IDENT, TokenType.INT, TokenType.HEX, TokenType.STRING}:
                            if self.current_token.type == TokenType.INT:
                                # Числовой аргумент
                                args.append(str(self.current_token.value))
                                self.eat(TokenType.INT)
                            elif self.current_token.type == TokenType.HEX:
                                # Шестнадцатеричный аргумент
                                args.append(str(int(self.current_token.value[1:], 16)))
                                self.eat(TokenType.HEX)
                            elif self.current_token.type == TokenType.STRING:
                                # Строковый литерал
                                value = self.current_token.value
                                self.eat(TokenType.STRING)
                                # Добавляем строковый литерал и получаем его метку
                                label = self.ctx.add_string_literal(value)
                                args.append(label)
                            else:
                                args.append(self.current_token.value)
                                self.eat(TokenType.IDENT)
                            
                            if self.current_token.type == TokenType.COMMA:
                                self.eat(TokenType.COMMA)
                        self.eat(TokenType.BRACKET_CLOSE)
                    
                    # Генерируем код вызова
                    # Передаем аргументы через стек
                    for arg in reversed(args):  # Аргументы помещаются в стек в обратном порядке
                        if arg.isdigit():
                            # Числовой аргумент
                            self.ctx.add_asm(f"  push {arg}")
                        else:
                            # Переменная
                            self.ctx.add_asm(f"  mov %gi {arg}")
                            self.ctx.add_asm(f"  push %gi")
                    
                    self.ctx.add_asm(f"  call {lib_var}_{func_name}")
                    # Очищаем стек от аргументов
                    if args:
                        self.ctx.add_asm(f"  mov %gi %sp")
                        self.ctx.add_asm(f"  add %gi {len(args) * 3 + 3}")
                        self.ctx.add_asm(f"  mov %sp %gi")
                else:
                    self.error(f"Unexpected identifier in function body: {lib_var}")
            else:
                self.error(f"Unexpected token in if body: {self.current_token.type}")
        
        self.eat(TokenType.PAREN_CLOSE)
        
        # Добавляем метку конца if-блока
        self.ctx.add_asm(f".END_{self.if_counter}:")
    




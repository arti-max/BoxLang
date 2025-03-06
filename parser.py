from dataclasses import dataclass
from typing import List, Optional
from lexer import Lexer, Token, TokenType

@dataclass
class FunctionArg:
    register: str
    arg_name: str

class Parser:
    def __init__(self, lexer: Lexer, ctx):
        self.lexer = lexer
        self.ctx = ctx
        self.current_token = self.lexer.get_next_token()
        self.current_function = None
        self.function_args = {}  # имя функции -> список аргументов
        self.imported_files = set()  # множество импортированных файлов
        self.lib_vars = {}  # имя -> путь к файлу
    
    def error(self, message: str):
        raise SyntaxError(f"{message} at line {self.current_token.line}, column {self.current_token.column}")
    
    def eat(self, token_type: TokenType):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error(f"Expected {token_type}, got {self.current_token.type}")
    
    def parse(self) -> str:
        """Основной метод парсинга"""
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
            elif self.current_token.type == TokenType.LIB:
                self.parse_variable("lib")
            elif self.current_token.type == TokenType.GASM:
                self.parse_gasm()
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
            base_path = path
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
                    parser = Parser(lexer, self.ctx)
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
                            if 'call ' in line:
                                parts = line.split('call ', 1)
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
            elif self.current_token.type == TokenType.GASM:
                self.parse_gasm()
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
        reg_map = {}  # Словарь для маппинга имен на регистры
        
        if self.current_token.type == TokenType.BRACKET_OPEN:
            self.eat(TokenType.BRACKET_OPEN)
            while self.current_token.type in {TokenType.REGISTER, TokenType.INT, TokenType.HEX}:
                if self.current_token.type == TokenType.REGISTER:
                    # Читаем регистр
                    reg = self.current_token.value
                    if reg not in ['ax', 'bx', 'cx', 'dx', 'si']:
                        self.error("Expected register name (ax, bx, cx, dx, si)")
                    self.eat(TokenType.REGISTER)
                    
                    if self.current_token.type != TokenType.PERCENT:
                        self.error("Expected % after register")
                    self.eat(TokenType.PERCENT)
                    
                    # Читаем имя аргумента
                    if self.current_token.type != TokenType.IDENT:
                        self.error("Expected argument name after %")
                    arg_name = self.current_token.value
                    self.eat(TokenType.IDENT)
                    
                    # Сохраняем маппинг имени на регистр
                    reg_map[arg_name] = reg
                    args.append(FunctionArg(reg, arg_name))
                elif self.current_token.type == TokenType.INT:
                    args.append(str(self.current_token.value))
                    self.eat(TokenType.INT)
                elif self.current_token.type == TokenType.HEX:
                    args.append(str(int(self.current_token.value[1:], 16)))
                    self.eat(TokenType.HEX)
                
                # Проверяем наличие запятой
                if self.current_token.type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
                    # Если после запятой сразу идет закрывающая скобка, это ошибка
                    if self.current_token.type == TokenType.BRACKET_CLOSE:
                        self.error("Unexpected comma after last argument")
                elif self.current_token.type != TokenType.BRACKET_CLOSE:
                    self.error("Expected comma between arguments or closing bracket")
            
            self.eat(TokenType.BRACKET_CLOSE)
        
        # Сохраняем аргументы функции и маппинг регистров
        if args:
            self.function_args[name] = args
            self.current_reg_map = reg_map
        
        # Начинаем функцию
        self.ctx.start_function(name)
        
        # Добавляем код для получения аргументов из стека
        if args:
            # Сохраняем base pointer
            self.ctx.add_asm("  push %bp")
            self.ctx.add_asm("  mov %bp %sp")
            
            # Загружаем аргументы
            for i, arg in enumerate(args):
                if isinstance(arg, FunctionArg):
                    # Загружаем значение из стека в регистр
                    # +4 для пропуска сохраненного bp и адреса возврата
                    # +2 для каждого следующего аргумента
                    offset = 4 + i * 2
                    self.ctx.add_asm(f"  mov %{arg.register} %bp")
                    self.ctx.add_asm(f"  add %{arg.register} {offset}")
                    self.ctx.add_asm(f"  mov %sp %{arg.register}")
                    self.ctx.add_asm(f"  pop %{arg.register}")
                    self.ctx.add_asm(f"  mov %sp %bp")
        
        # Тело функции
        self.eat(TokenType.PAREN_OPEN)
        while self.current_token.type != TokenType.PAREN_CLOSE:
            if self.current_token.type == TokenType.CHAR:
                self.parse_variable("char")
            elif self.current_token.type == TokenType.NUM16:
                self.parse_variable("num16")
            elif self.current_token.type == TokenType.GASM:
                self.parse_gasm()
            elif self.current_token.type == TokenType.OPEN:
                self.parse_open()
            elif self.current_token.type == TokenType.LOOP:
                self.parse_loop()
            elif self.current_token.type == TokenType.GOTO:
                self.parse_goto()
            elif self.current_token.type == TokenType.HASH:
                # Локальная метка
                self.eat(TokenType.HASH)
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
                        while self.current_token.type in {TokenType.IDENT, TokenType.INT, TokenType.HEX}:
                            if self.current_token.type == TokenType.INT:
                                # Числовой аргумент
                                args.append(str(self.current_token.value))
                                self.eat(TokenType.INT)
                            elif self.current_token.type == TokenType.HEX:
                                # Шестнадцатеричный аргумент
                                args.append(str(int(self.current_token.value[1:], 16)))
                                self.eat(TokenType.HEX)
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
                        self.ctx.add_asm(f"  add %gi {len(args) * 2}")
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
            self.eat(TokenType.CHAR if var_type == "char" else TokenType.NUM16)
        
        if self.current_token.type != TokenType.IDENT:
            self.error("Expected variable name")
        name = self.current_token.value
        self.eat(TokenType.IDENT)
        
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
                base_path = path
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
                    parser = Parser(lexer, self.ctx)
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
            self.ctx.add_variable(name, " ".join(values))
        elif var_type == "num16":
            # Числовое значение
            if self.current_token.type == TokenType.HEX:
                value = self.current_token.value
            else:
                value = f"${self.current_token.value:02X}"
            self.eat(self.current_token.type)
            self.ctx.add_variable(name, value)
    
    def parse_gasm(self):
        """Парсит ассемблерную вставку"""
        self.eat(TokenType.GASM)
        self.eat(TokenType.BRACKET_OPEN)
        if self.current_token.type != TokenType.STRING:
            self.error("Expected string in gasm[]")
        
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
            while self.current_token.type in {TokenType.IDENT, TokenType.INT, TokenType.HEX}:
                if self.current_token.type == TokenType.INT:
                    # Числовой аргумент
                    args.append(str(self.current_token.value))
                    self.eat(TokenType.INT)
                elif self.current_token.type == TokenType.HEX:
                    # Шестнадцатеричный аргумент
                    args.append(str(int(self.current_token.value[1:], 16)))
                    self.eat(TokenType.HEX)
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
        
        self.ctx.add_asm(f"  call {func_name}")
        # Очищаем стек от аргументов
        if args:
            self.ctx.add_asm(f"  mov %gi %sp")
            self.ctx.add_asm(f"  add %gi {len(args) * 2}")
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
        self.ctx.add_asm(f"  mov %gi {var}")
        self.ctx.add_asm(f"  cmp *%gi $00")
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
        self.ctx.add_asm(f"  mov %gi {var}")
        self.ctx.add_asm(f"  cmp *%gi {value}")
        self.ctx.add_asm(f"  jme .{label}")
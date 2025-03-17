class CodegenContext:
    def __init__(self):
        self.variables = {}  # имя -> значение
        self.functions = {}  # имя -> [строки кода]
        self.current_function = None
        self.imported_code = []  # код из импортированных файлов
        self.is_boot = False
        
        # Загружаем стандартную библиотеку
        with open("stdlib/def.asm") as f:
            self.stdlib = f.read()
    
    def add_variable(self, name: str, value: str):
        """Добавляет переменную"""
        print(f"[VAR] {name} = {value}")
        self.variables[name] = value
    
    def reserve(self, name: str, size: int, unit: str):
        """Резервирует память"""
        directive = f"reserve {size} {unit}s"
        print(f"[RESERVE] {name}: {directive}")
        self.variables[name] = directive
    
    def start_function(self, name: str):
        """Начинает новую функцию"""
        print(f"[DEBUG] Starting function: {name}")
        self.current_function = name
        self.functions[name] = []
    
    def add_asm(self, code: str):
        """Добавляет ассемблерный код в текущую функцию"""
        if self.current_function:
            print(f"[DEBUG] Adding to {self.current_function}: {code}")
            self.functions[self.current_function].append(code)
    
    def add_std_library(self):
        """Добавляет стандартную библиотеку"""
        print("[DEBUG] Adding standard library")
    
    def add_imported_code(self, code: str):
        """Добавляет код из импортированного файла"""
        self.imported_code.append(code)
    
    def generate(self) -> str:
        """Генерирует финальный ассемблерный код"""
        print("\n[DEBUG] Generating ASM...")
        result = []
        
        # Прыжок на точку входа
        print(self.is_boot)
        if self.is_boot:
            result.append("jmp _boot\n")
        else:
            result.append("jmp _start\n")
        
        # Секция переменных
        print(f"[DEBUG] Variables count: {len(self.variables)}")
        for name, value in self.variables.items():
            print(f"[DEBUG] Variable: {name} = {value}")
            if value.startswith("reserve"):
                result.append(f"{name}: {value}")
            else:
                result.append(f"{name}: bytes {value}")
        result.append("")
        
        # Стандартная библиотека
        result.append("; Standard library (def.asm)")
        result.append(self.stdlib)
        result.append("")
        
        # Код из импортированных файлов
        if self.imported_code:
            result.append("; Imported code")
            result.extend(self.imported_code)
            result.append("")
        
        result.append("; Main code")
        
        # Пользовательские функции (кроме start)
        for name, body in self.functions.items():
            if name != "_start":
                result.append(f"{name}:")
                result.extend(body)
                result.append("")
        
        # Точка входа
        if "_start" in self.functions:
            result.append("_start:")
            result.extend(self.functions["_start"])
            result.append("")
        
        return "\n".join(result) 
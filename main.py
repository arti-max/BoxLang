import sys
from lexer import Lexer
from parser import Parser
from codegen import CodegenContext

def compile_file(input_file: str, output_file: str, is_boot: bool = False):
    """Компилирует файл BoxLang в ассемблер"""
    # Читаем исходный файл с явным указанием кодировки UTF-8
    with open(input_file, 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Создаем лексер
    lexer = Lexer(source)
    
    # Создаем контекст для генерации кода
    ctx = CodegenContext()
    
    # Создаем парсер
    parser = Parser(lexer, ctx, input_file)
    
    # Устанавливаем флаг загрузочного сектора
    parser.is_boot = is_boot
    
    # Парсим и получаем ассемблерный код
    asm_code = parser.parse()
    
    # Если это загрузочный сектор, добавляем сигнатуру
    if is_boot:
        asm_code += "\nbootsecend:    bytes $AA $55\n"
    
    # Записываем результат в выходной файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(asm_code)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main.py input.box output.asm [--boot]")
        sys.exit(1)
    
    is_boot = "--boot" in sys.argv
    compile_file(sys.argv[1], sys.argv[2], is_boot) 
import sys
from lexer import Lexer
from parser import Parser
from codegen import CodegenContext

def compile_file(input_file: str, output_file: str):
    """Компилирует файл BoxLang в ассемблер"""
    # Читаем исходный файл с явным указанием кодировки UTF-8
    with open(input_file, 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Создаем лексер
    lexer = Lexer(source)
    
    # Создаем контекст для генерации кода
    ctx = CodegenContext()
    
    # Создаем парсер
    parser = Parser(lexer, ctx)
    
    # Парсим и получаем ассемблерный код
    asm_code = parser.parse()
    
    # Записываем результат в выходной файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(asm_code)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python main.py input.box output.asm")
        sys.exit(1)
    
    compile_file(sys.argv[1], sys.argv[2]) 
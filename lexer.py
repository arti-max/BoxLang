from dataclasses import dataclass
from enum import Enum, auto
import re

class TokenType(Enum):
    BOX = auto()      # box
    OPEN = auto()     # open
    NUM16 = auto()    # num16
    NUM24 = auto()    # num24
    CHAR = auto()     # char
    LIB = auto()      # lib
    KASM = auto()     # kasm
    RESERVE = auto()  # ?
    ARRAY = auto()    # Array
    LOOP = auto()     # loop
    GOTO = auto()     # goto
    JUMP = auto()     # jump
    HASH = auto()     # #
    IF = auto()       # if
    ELSE = auto()     # else
    ENDIF = auto()    # endif
    
    BRACKET_OPEN = auto()  # [
    BRACKET_CLOSE = auto() # ]
    PAREN_OPEN = auto()   # (
    PAREN_CLOSE = auto()  # )
    CURLY_OPEN = auto()   # {
    CURLY_CLOSE = auto()  # }
    ANGLE_OPEN = auto()   # <
    ANGLE_CLOSE = auto()  # >
    COLON = auto()        # :
    PERCENT = auto()      # %
    COMMA = auto()        # ,
    AT = auto()          # @
    DOT = auto()         # .
    ARROW = auto()       # ->
    EQ = auto()
    
    STRING = auto()       # "text"
    STRING_LIT = auto()   # "text" в аргументах
    CHAR_LIT = auto()    # 'c'
    INT = auto()         # 123
    HEX = auto()         # $FF
    IDENT = auto()       # name
    REGISTER = auto()    # si, di, etc.
    
    EOF = auto()

@dataclass
class Token:
    type: TokenType
    value: str = ""
    line: int = 0
    column: int = 0

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.current_char = self.source[0] if source else None
        
        # Определяем токены
        self.keywords = {
            'box': TokenType.BOX,
            'open': TokenType.OPEN,
            'num16': TokenType.NUM16,
            'num24': TokenType.NUM24,
            'char': TokenType.CHAR,
            'lib': TokenType.LIB,
            'kasm': TokenType.KASM,
            'Array': TokenType.ARRAY,
            'loop': TokenType.LOOP,
            'goto': TokenType.GOTO,
            'jump': TokenType.JUMP,
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'endif': TokenType.ENDIF,
        }
        
        self.registers = {'ax', 'bx', 'cx', 'dx', 'si', 'bp', 'sp', 'gi', 'ex', 'fx', 'hx', 'lx', 'x', 'y', 'ix', 'iy', 'ps', 'pc'}
        
        self.single_chars = {
            '[': TokenType.BRACKET_OPEN,
            ']': TokenType.BRACKET_CLOSE,
            '(': TokenType.PAREN_OPEN,
            ')': TokenType.PAREN_CLOSE,
            '{': TokenType.CURLY_OPEN,
            '}': TokenType.CURLY_CLOSE,
            '<': TokenType.ANGLE_OPEN,
            '>': TokenType.ANGLE_CLOSE,
            ':': TokenType.COLON,
            '?': TokenType.RESERVE,
            '%': TokenType.PERCENT,
            ',': TokenType.COMMA,
            '@': TokenType.AT,
            '.': TokenType.DOT,
            "=": TokenType.EQ,
        }
    
    def advance(self):
        self.pos += 1
        if self.pos >= len(self.source):
            self.current_char = None
        else:
            self.current_char = self.source[self.pos]
            if self.current_char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
    
    def peek(self) -> str:
        peek_pos = self.pos + 1
        if peek_pos >= len(self.source):
            return None
        return self.source[peek_pos]
    
    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace():
            self.advance()
    
    def skip_comment(self):
        while self.current_char and self.current_char != '\n':
            self.advance()
    
    def read_string(self) -> Token:
        result = ""
        start_line = self.line
        start_column = self.column
        self.advance()  # пропускаем открывающую кавычку
        while self.current_char and self.current_char != '"':
            if self.current_char == '\\':
                self.advance()
                if self.current_char == 'n':
                    result += '\n'
                elif self.current_char == 't':
                    result += '\t'
                else:
                    result += self.current_char
            else:
                result += self.current_char
            self.advance()
        self.advance()  # пропускаем закрывающую кавычку
        return Token(TokenType.STRING, result, start_line, start_column)
    
    def read_char(self) -> Token:
        start_line = self.line
        start_column = self.column
        self.advance()  # пропускаем открывающую кавычку
        char = self.current_char
        self.advance()  # пропускаем символ
        self.advance()  # пропускаем закрывающую кавычку
        return Token(TokenType.CHAR_LIT, char, start_line, start_column)
    
    def read_number(self) -> Token:
        num = ""
        start_line = self.line
        start_column = self.column
        while self.current_char and (self.current_char.isdigit() or self.current_char in 'ABCDEFabcdef$'):
            num += self.current_char
            self.advance()
        
        if num.startswith('$'):
            return Token(TokenType.HEX, num, start_line, start_column)
        return Token(TokenType.INT, int(num), start_line, start_column)
    
    def read_identifier(self) -> Token:
        result = ""
        start_line = self.line
        start_column = self.column
        
        # Если начинается с @, включаем его в идентификатор
        if self.current_char == '@':
            result += self.current_char
            self.advance()
        
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_' or self.current_char == '.'):
            result += self.current_char
            self.advance()
        
        # Проверяем, является ли идентификатор регистром
        if result in self.registers:
            return Token(TokenType.REGISTER, result, start_line, start_column)
        
        # Проверяем, является ли идентификатор ключевым словом
        token_type = self.keywords.get(result, TokenType.IDENT)
        return Token(token_type, result, start_line, start_column)
    
    def get_next_token(self) -> Token:
        while self.current_char is not None:
            # Пропускаем пробелы
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            # Пропускаем комментарии
            if self.current_char == ';':
                self.skip_comment()
                continue
            
            # Проверяем на ->
            if self.current_char == '-' and self.peek() == '>':
                start_line = self.line
                start_column = self.column
                self.advance()  # пропускаем -
                self.advance()  # пропускаем >
                return Token(TokenType.ARROW, "->", start_line, start_column)
            
            # Строковые литералы
            if self.current_char == '"':
                return self.read_string()
            
            # Символьные литералы
            if self.current_char == "'":
                return self.read_char()
            
            # Числа и hex-числа
            if self.current_char.isdigit() or self.current_char == '$':
                return self.read_number()
            
            # Однобуквенные токены
            if self.current_char in self.single_chars:
                token = Token(self.single_chars[self.current_char], self.current_char, self.line, self.column)
                self.advance()
                return token
            
            # Идентификаторы, ключевые слова и регистры
            if self.current_char.isalpha() or self.current_char == '_':
                return self.read_identifier()
            
            # Проверяем специальные символы
            if self.current_char == '#':
                token = Token(TokenType.HASH, '#', self.line, self.column)
                self.advance()
                return token
            
            if self.current_char == '%':
                token = Token(TokenType.PERCENT, '%', self.line, self.column)
                self.advance()
                return token
            
            raise SyntaxError(f"Unexpected character: {self.current_char} at line {self.line}, column {self.column}")
        
        return Token(TokenType.EOF, "", self.line, self.column) 
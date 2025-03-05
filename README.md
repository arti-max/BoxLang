# BoxLang Documentation

BoxLang - это простой и эффективный язык программирования, компилируемый в GovnASM. Он предоставляет удобный синтаксис для работы с низкоуровневыми операциями, поддерживает модульность через систему импортов и предлагает стандартную библиотеку для часто используемых операций.

## Содержание
1. [Основы синтаксиса](#основы-синтаксиса)
2. [Типы данных](#типы-данных)
3. [Переменные](#переменные)
4. [Функции](#функции)
5. [Импорты и библиотеки](#импорты-и-библиотеки)
6. [Стандартная библиотека](#стандартная-библиотека)
7. [Примеры программ](#примеры-программ)

## Основы синтаксиса

### Комментарии
```box
; Однострочный комментарий
```

### Структура программы
Каждая программа должна содержать точку входа - функцию `start`:
```box
box start[] (
    ; код программы
)
```

## Типы данных

### num16
16-битное целое число
```box
num16 variable : 42        ; Инициализация значением
num16 reserved : ?1        ; Резервирование 1  байта
```

### char
8-битный символ или массив символов
```box
char c : 'A'              ; Одиночный символ
char str: Array{'H' 'i' '$'} ; Строка (должна заканчиваться на '$')
char buffer: ?64          ; Буфер на 64 байта
```

## Переменные

### Объявление переменных
```box
num16 count : 5           ; Числовая переменная
char message: Array{'H' 'e' 'l' 'l' 'o' '$'} ; Строковая переменная
num16 result: ?1          ; Резервирование памяти
```

## Функции

### Объявление функции
```box
box function_name[si%arg1, ax%arg2] (
    ; тело функции
)
```

### Вызов функции
```box
open function_name[arg1, arg2]
```

### Локальные метки и управление потоком
Внутри функций можно использовать локальные метки с префиксом `#` и управлять потоком выполнения:
```box
box function[] (
    #loop_start
    ; код
    
    ; Условный переход на метку при равенстве
    goto[#loop_start, counter, 5]      ; если counter == 5
    goto[#loop_start, char_var, 'A']   ; если char_var == 'A'
    goto[#loop_start, hex_var, $FF]    ; если hex_var == 0xFF
    
    ; Цикл с условием продолжения
    #another_loop
    ; код
    loop[#another_loop, is_continue]    ; переход если is_continue > 0
)
```

Разница между `goto` и `loop`:
- `goto[#label, var, value]` - переходит на метку, если значение переменной равно указанному значению
- `loop[#label, var]` - возвращается на метку, если значение переменной больше 0

Значение для сравнения в `goto` может быть:
- Числом (например, `5`)
- Символом (например, `'A'`)
- Шестнадцатеричным числом (например, `$FF`)

## Импорты и библиотеки

### Импорт файлов
```box
@incl "path/to/file"      ; Импорт локального файла
@incl <stdlib>            ; Импорт из стандартной библиотеки
```

### Библиотечные переменные
```box
lib math : incl "math"    ; Импорт как библиотечную переменную
math->function[args]      ; Вызов функции из библиотеки
```

## Стандартная библиотека

### io.asm
Библиотека для ввода/вывода
- `print[str]` - вывод строки
- `scanstr[buffer]` - чтение строки в буфер

### datautils.asm
Утилиты для работы с данными
- `strcpy[dest, src]` - копирование строки
- `num_to_string[num, buffer]` - преобразование числа в строку
- `memcpy[target, dest, count]` - компирует значение в памяти из одного адреса в другой `count` количество раз


## Примеры программ

### Hello World
```box
@incl <io>

char message: Array{'H' 'e' 'l' 'l' 'o' ',' ' ' 'W' 'o' 'r' 'l' 'd' '!' '$'}

box start[] (
    open print[message]
    open exit[0]
)
```

### Калькулятор
```box
@incl <io>
@incl <datautils>

char num1_str: ?6
char num2_str: ?6
char result_str: ?6
num16 num1: ?1
num16 num2: ?1
num16 result: ?1

lib math : incl "math"

box start[] (
    open print[num1]
    open scan_num[num1]
    
    open print[num2]
    open scan_num[num2]
    
    math->add[num1, num2, result]
    du->num_to_string[result, result_str]
    open println[result_str]
    
    open exit[0]
)
```

### Цикл с условием
```box
@incl <io>

num16 counter : 5
char message: Array{'C' 'o' 'u' 'n' 't' ':' ' ' '$'}
char buffer : ?5

lib du : incl <datautils>

box start[] (
    #loop
    open print[message]
    du->num_to_string[counter, buffer]
    open println[buffer]
    
    ; Уменьшаем счетчик
    math->sub[counter, 1, counter]
    
    ; Проверяем условие и повторяем
    loop[#loop, counter]
    
    open exit[0]
)
```

## Компиляция и запуск

Для компиляции программы используйте компилятор BoxLang:
```bash
python main.py input.box output.asm
```

Затем используйте KASM для получения исполняемого файла:
```bash
kasm output.asm output.bin
``` 

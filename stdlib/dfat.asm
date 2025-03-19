; DFAT File System Library
; Константы файловой системы
DFAT_SIGNATURE: bytes $44 $46 $41 $54  ; 'DFAT'
DFAT_VERSION: bytes $01                 ; Версия 1
DFAT_BLOCK_SIZE: bytes $00 $02         ; 512 байт
DFAT_MAX_FILES: bytes $40 $00          ; 64 файла

; Флаги файлов
DFAT_FLAG_UNUSED:  bytes 0
DFAT_FLAG_FILE:    bytes 1
DFAT_FLAG_SYSTEM:  bytes 2
DFAT_FLAG_DELETED: bytes $80

; Буфер для чтения записи файла (16 байт)
file_entry_buffer: reserve 16 bytes

; DFAT (Direct File Allocation Table) library
; Все аргументы передаются через стек
; Для функций, возвращающих данные, последний аргумент - адрес буфера для результата

; Проверяет сигнатуру DFAT
; Аргументы:
; - Адрес образа диска
; - Адрес для результата (1 = валидная сигнатура, 0 = невалидная)
check_signature:
    push %bp
    mov %bp %sp
    
    ; Получаем адрес образа
    mov %si %bp
    add %si 6
    mov %sp %si
    pop %si
    mov %sp %bp
    
    ; Получаем адрес для результата
    mov %dx %bp
    add %dx 9
    mov %sp %dx
    pop %dx
    mov %sp %bp
    
    ; Проверяем сигнатуру
    lodb %si %ax    ; Первый байт сигнатуры
    cmp %ax $44     ; 'D'
    jne .invalid
    
    lodb %si %ax    ; Второй байт
    cmp %ax $46     ; 'F'
    jne .invalid
    
    lodb %si %ax    ; Третий байт
    cmp %ax $41     ; 'A'
    jne .invalid
    
    lodb %si %ax    ; Четвертый байт
    cmp %ax $54     ; 'T'
    jne .invalid
    
    ; Сигнатура верна
    mov %ax $1
    stob %gi %ax
    jmp .done
    
.invalid:
    mov %ax $0
    stob %gi %ax
    
.done:
    mov %sp %bp
    pop %bp
    ret

; Получает список файлов
; Аргументы:
; - Адрес образа диска
; - Адрес буфера для списка файлов
; - Размер буфера
; - Адрес для количества найденных файлов
list_files:
    push %bp
    mov %bp %sp
    
    ; Получаем адрес образа
    mov %si %bp
    add %si 6
    mov %sp %si
    pop %si
    mov %sp %bp
    
    ; Получаем адрес буфера
    mov %dx %bp
    add %dx 9
    mov %sp %dx
    pop %dx
    mov %sp %bp
    
    ; Получаем размер буфера
    mov %cx %bp
    add %cx 12
    mov %sp %cx
    pop %cx
    mov %sp %bp
    
    ; Получаем адрес для количества файлов
    mov %bx %bp
    add %bx 15
    mov %sp %bx
    pop %bx
    mov %sp %bp
    
    ; Пропускаем суперблок (512 байт)
    add %si $200
    
    ; Счетчик файлов
    mov %ax 0
    
.next_entry:
    ; Проверяем флаг файла
    lodb %si %gi
    cmp %gi 0      ; Неиспользуемая запись
    je .skip_entry
    cmp %gi 2      ; Удаленный файл
    je .skip_entry
    
    ; Копируем запись файла (16 байт)
    push %cx       ; Сохраняем размер буфера
    mov %cx 16     ; Размер записи
.copy_entry:
    lodb %si %gi
    stb %dx %gi
    inx %dx
    dex %cx
    jnz .copy_entry
    pop %cx        ; Восстанавливаем размер буфера
    
    ; Увеличиваем счетчик файлов
    inc %ax
    
    ; Проверяем размер буфера
    sub %cx 16
    jle .done
    
    jmp .next_entry
    
.skip_entry:
    add %si 15     ; Пропускаем остаток записи
    jmp .next_entry
    
.done:
    ; Сохраняем количество найденных файлов
    stob %bx %ax
    
    mov %sp %bp
    pop %bp
    ret

; Читает содержимое файла
; Аргументы:
; - Адрес образа диска
; - Адрес имени файла (8.3 формат)
; - Адрес буфера для данных
; - Адрес для размера прочитанного файла (0 если файл не найден)
read_file:
    push %bp
    mov %bp %sp
    
    ; Получаем адрес образа
    mov %si %bp
    add %si 6
    mov %sp %si
    pop %si
    mov %sp %bp
    
    ; Получаем адрес имени файла
    mov %dx %bp
    add %dx 9
    mov %sp %dx
    pop %dx
    mov %sp %bp
    
    ; Получаем адрес буфера данных
    mov %cx %bp
    add %cx 12
    mov %sp %cx
    pop %cx
    mov %sp %bp
    
    ; Получаем адрес для размера
    mov %bx %bp
    add %bx 15
    mov %sp %bx
    pop %bx
    mov %sp %bp
    
    ; Пропускаем суперблок
    add %si $200
    
    ; Ищем файл в таблице
.find_file:
    ; Проверяем флаг файла
    lodb %si %ax
    cmp %ax 0      ; Конец таблицы
    je .not_found
    cmp %ax 2      ; Удаленный файл
    je .next_entry
    
    ; Сравниваем имя файла (11 байт)
    push %si
    mov %gi 11
.compare_name:
    lodb %si %ax
    lodb %dx %gi
    cmp %ax %gi
    jne .name_mismatch
    dex %gi
    jnz .compare_name
    
    ; Файл найден
    pop %si
    
    ; Читаем размер файла
    add %si 11     ; Пропускаем имя
    lodw %si %ax   ; Читаем размер (2 байта)
    stow %bx %ax    ; Сохраняем размер
    
    ; Читаем начальный блок
    add %si 2
    lodw %si %ax
    
    ; Вычисляем адрес данных (512 + номер_блока * 512)
    mov %gi $200
    mul %ax %gi
    add %si %gi
    add %si $200
    
    ; Копируем данные
    mov %dx %cx     ; Адрес буфера
    mov %cx %ax     ; Размер для копирования
.copy_data:
    lodb %si %gi
    stob %dx %gi
    inx %dx
    dex %cx
    jnz .copy_data
    
    jmp .done
    
.name_mismatch:
    pop %si
.next_entry:
    add %si 15     ; Переходим к следующей записи
    jmp .find_file
    
.not_found:
    mov %ax 0
    stow %bx %ax
    
.done:
    mov %sp %bp
    pop %bp
    ret 
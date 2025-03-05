; Стандартная библиотека
; buffers
cline:  reserve 64 bytes
qptr:   reserve 1 bytes   

; Control sequences
bs_seq:     bytes "^H ^H^@"
cls_seq:    bytes "^[[H^[[2J^@"

puts:
    cmp *%si $00
    re
    push *%si
    int $02
    inx %si
    jmp puts

exit:
    push %bp
    mov %bp %sp
    ;arg parse
    mov %si %bp
    add %si 4
    mov %sp %si
    pop %si
    mov %sp %bp
    push %si
    int $00
    mov %sp %bp
    pop %bp
    ret

trapf:
    trap
    ret
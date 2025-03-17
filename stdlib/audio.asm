



; Standard Beep
; ax - tone
beep:
    push %bp
    mov %bp %sp
    ; arg 1 - tone
    mov %ax %bp
    add %ax 6
    mov %sp %ax
    pop %ax

    mov %sp %bp
    ; logic
    push %ax
    int $23
    ; end
    mov %sp %bp
    pop %bp
    ret
; Data Utils

; Copy string from Target to Dest
; ax - Target
; bx - Dest
strcpy:
    ; arg1 - Target ; bp+4
    ; arg2 - Dest   ; bp+6
    push %bp
    mov %bp %sp
    ;arg1
    mov %ax %bp
    add %ax 4
    mov %sp %ax
    pop %ax
    ;arg2
    mov %bx %bp
    add %bx 6
    mov %sp %bx
    pop %bx
    ; logic
    .loop:
        mov %si *%ax
        mov %gi %bx
        cmp %si $00
        jme .end
        stgrb %si
        inx %ax
        inx %bx
        jmp .loop
    ; end
    .end:
        mov %sp %bp
        pop %bp
        ret


; Convert 16-bit num to string
; ax - Location of Number
; bx - Location to convert
num_to_string:
    push %bp
    mov %bp %sp 
    ; arg1
    mov %ax %sp
    add %ax 4
    mov %sp %ax
    pop %ax
    mov %sp %bp
    ; arg2
    mov %bx %sp
    add %bx 6
    mov %sp %bx
    pop %bx
    mov %sp %bp
    ; logic
    mov %gi %bx
    add %gi 4
    mov %ax *%ax
.loop:
    div %ax 10  ; Divide and get the remainder into DX
    add %dx 48  ; Convert to ASCII
    mov %si %gi
    storb %dx
    dex %gi
    cmp %ax $00
    jmne .loop
    ; end
.end:
    mov %sp %bp
    pop %bp



; Copy memory from Target to Dest
; ax - Target
; bx - Dest
; cx - Count
memcpy:
    ; arg1 - Target ; bp+4
    ; arg2 - Dest   ; bp+6
    ; arg3 - Count  ; bp+8
    push %bp
    mov %bp %sp
    ;arg1
    mov %ax %bp
    add %ax 4
    mov %sp %ax
    pop %ax
    ;arg2
    mov %bx %bp
    add %bx 6
    mov %sp %bx
    pop %bx
    ;arg3
    mov %cx %bp
    add %cx 8
    mov %sp %cx
    pop %cx
    mov %sp %bp
    ; logic
.loop:
    push %si
    mov %si *%ax
    mov %gi %bx
    stgrb %si
    inx %ax
    inx %bx
    loop .loop
    ; end
    pop %si
    mov %sp %bp
    pop %bp
    ret
; Compare two sttrings
; ax - Str1
; bx - Str2
; cx - result (0 or 1)
string_compare:
    ; arg1 - Str1   ; bp+4
    ; arg2 - Str2   ; bp+6
    ; arg3 - result ; bp+8
    push %bp
    mov %bp %sp
    ;arg1
    mov %ax %bp
    add %ax 4
    mov %sp %ax
    pop %ax
    ;arg2
    mov %bx %bp
    add %bx 6
    mov %sp %bx
    pop %bx
    ;arg3
    mov %cx %bp
    add %cx 8
    mov %sp %cx
    pop %cx

    mov %sp %bp
    ;logic
    ; mov %dx $00
    ; storb %dx
    mov %si %ax
    mov %gi *qptr
    add %si %gi
    dex %si
    mov %dx $00
    storb %dx ; Load $00 (NUL) instead of $0A (Enter)
    mov %si qptr
    storb %dx

.loop:
    mov %si *%ax
    mov %gi *%bx
    cmp %si %gi
    jmne .fail
    cmp %si $00
    jme .eq
    inx %ax
    inx %bx
    jmp .loop
.eq:
    mov %gi %cx
    mov %cx $01
    stgrb %cx
    jmp .end
.fail:
    mov %gi %cx
    mov %cx $00
    stgrb %cx
.end:
    mov %sp %bp
    pop %bp
    ret

; Set new data to variable [1 byte]
; ax - *var
; bx - data
set_new_data:
    push %bp
    mov %bp %sp
    ;arg1
    mov %ax %bp
    add %ax 4
    mov %sp %ax
    pop %ax
    ;arg2
    mov %bx %bp
    add %bx 6
    mov %sp %bx
    pop %bx

    mov %sp %bp
    ; logic
    mov %si *%ax
    storb %bx
    ;end
    pop %bp
    ret

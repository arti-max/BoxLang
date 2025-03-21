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
    add %ax 6
    mov %sp %ax
    pop %ax
    ;arg2
    mov %bx %bp
    add %bx 9
    mov %sp %bx
    pop %bx
    ; logic
    .loop:
        lodb %ax %si
        mov %gi %bx
        cmp %si $00
        je .end
        stob %gi %si
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
num_to_string_16:
    push %bp
    mov %bp %sp 
    ; arg1
    mov %ax %sp
    add %ax 6
    mov %sp %ax
    pop %ax
    mov %sp %bp
    ; arg2
    mov %bx %sp
    add %bx 9
    mov %sp %bx
    pop %bx
    mov %sp %bp
    ; logic
    mov %gi %bx
    add %gi 4
    lodw %ax %ax
.loop:
    div %ax 10  ; Divide and get the remainder into DX
    add %dx 48  ; Convert to ASCII
    mov %si %gi
    stob %si %dx
    dex %gi
    cmp %ax $00
    jne .loop
    ; end
.end:
    mov %sp %bp
    pop %bp


; Convert 24-bit num to string
; ax - Location of Number
; bx - Location to convert
num_to_string_24:
    push %bp
    mov %bp %sp 
    ; arg1
    mov %ax %sp
    add %ax 6
    mov %sp %ax
    pop %ax
    mov %sp %bp
    ; arg2
    mov %bx %sp
    add %bx 9
    mov %sp %bx
    pop %bx
    mov %sp %bp
    ; logic
    mov %gi %bx
    add %gi 7
    lodh %ax %ax
.loop:
    div %ax 10  ; Divide and get the remainder into DX
    add %dx 48  ; Convert to ASCII
    mov %si %gi
    stob %si %dx
    dex %gi
    cmp %ax $00
    jne .loop
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
    add %ax 6
    mov %sp %ax
    pop %ax
    ;arg2
    mov %bx %bp
    add %bx 9
    mov %sp %bx
    pop %bx
    ;arg3
    mov %cx %bp
    add %cx 12
    mov %sp %cx
    pop %cx
    mov %sp %bp
    ; logic
    push %si
.loop:
    lodb %ax %si
    mov %gi %bx
    stob %gi %si
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
    ; arg1 - Str1   ; bp+6
    ; arg2 - Str2   ; bp+9
    ; arg3 - result ; bp+12
    push %bp
    mov %bp %sp
    ;arg1
    mov %ax %bp
    add %ax 6
    mov %sp %ax
    pop %ax
    ;arg2
    mov %bx %bp
    add %bx 9
    mov %sp %bx
    pop %bx
    ;arg3
    mov %cx %bp
    add %cx 12
    mov %sp %cx
    pop %cx

    mov %sp %bp
    ;logic
    mov %si %ax

.loop:
    lodb %ax %si
    lodb %bx %gi
    cmp %si %gi
    jne .fail
    cmp %si $00
    je .eq
    jmp .loop
.eq:
    mov %gi %cx
    mov %cx $01
    stob %gi %cx
    jmp .end
.fail:
    mov %gi %cx
    mov %cx $00
    stob %gi %cx
.end:
    mov %sp %bp
    pop %bp
    ret

; Set new data to variable [3 byte]
; ax - *var
; bx - data
set_new_data_24:
    push %bp
    mov %bp %sp
    ;arg1
    mov %ax %bp
    add %ax 6
    mov %sp %ax
    pop %ax
    ;arg2
    mov %bx %bp
    add %bx 9
    mov %sp %bx
    pop %bx
    ;arg3
    mov %bx %bp
    add %bx 12
    mov %sp %bx
    pop %bx

    mov %sp %bp
    ; logic
    lodh %ax %si
    stoh %si %bx
    ;end
    pop %bp
    ret

; Set new data to variable [2 byte]
; ax - *var
; bx - data
set_new_data_16:
    push %bp
    mov %bp %sp
    ;arg1
    mov %ax %bp
    add %ax 6
    mov %sp %ax
    pop %ax
    ;arg2
    mov %bx %bp
    add %bx 9
    mov %sp %bx
    pop %bx
    ;arg3
    mov %bx %bp
    add %bx 12
    mov %sp %bx
    pop %bx

    mov %sp %bp
    ; logic
    lodw %ax %si
    stow %si %bx
    ;end
    pop %bp
    ret


; Set new data to variable [1 byte]
; ax - *var
; bx - data
set_new_data_8:
    push %bp
    mov %bp %sp
    ;arg1
    mov %ax %bp
    add %ax 6
    mov %sp %ax
    pop %ax
    ;arg2
    mov %bx %bp
    add %bx 9
    mov %sp %bx
    pop %bx
    ;arg3
    mov %bx %bp
    add %bx 12
    mov %sp %bx
    pop %bx

    mov %sp %bp
    ; logic
    lodb %ax %si
    stob %si %bx
    ;end
    pop %bp
    ret

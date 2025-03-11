print:
    push %bp
    mov %bp %sp
    ;arg parse
    mov %si %bp
    add %si 6
    mov %sp %si
    pop %si
    mov %sp %bp
    ; logic
    call puts
    ; end
    mov %sp %bp
    pop %bp
    ret

;args - var address
input: 
    push %bp
    mov %bp %sp
    ; arg parse
    mov %si %bp
    add %si 6   ; 1st arg
    mov %sp %si
    pop %si
    mov %sp %bp
    ; logic
    int $01
    pop %ax
    stob %gi %ax
    ; end
    mov %sp %bp
    pop %bp
    ret

; arg1 - %si : buffer
scanstr:
    push %bp
    mov %bp %sp 
    ; arg1
    mov %si %sp
    add %si 6
    mov %sp %si
    pop %si
    mov %sp %bp
    ; logic
    .logic:
    int $01
    pop %dx
    
    cmp %dx $7F ; Backspace check
    jme .bs
    cmp %bx $08
    jme .bs
    
    ; print
    push %dx
    int $02
    
    ; Save to mem
    mov %gi *qptr
    add %si %gi
    stob %si %dx
    sub %si %gi
    inx qptr
    
    ; check enter
    cmp %dx $0A
    jme .end
    jmp .logic

    .bs:
        mov %gi *qptr
        cmp %gi $00
        jme .logic
    .bs_strict:
        dex qptr
        push %si
        mov %si bs_seq
        call puts
        pop %si
        jmp .logic
        
    
    .end:
    mov %sp %bp
    pop %bp
    ret
    

; scani - Scan an num from standard input
; Returns:
; ax - *number
scan_num:
push %bp
    mov %bp %sp 
    ; arg1
    mov %ax %sp
    add %ax 6
    mov %sp %ax
    pop %ax
    mov %sp %bp

    mov %gi %ax
    mov %ax $00
.loop:
    int $01
    pop %bx

    cmp %bx $0A ; Check for Enter
    jme .end
    cmp %bx $20 ; Check for space
    jme .end
    cmp %bx $00 ; Check for NUL ($00)
    jme .end
    cmp %bx $30 ; Check if less than '0'
    jl .loop
    cmp %bx $3A ; Check if greater than '9'+1
    jg .loop
    cmp %bx $7F ; Check for Backspace
    jme .back

    mul %ax 10
    push %bx
    int $02
    sub %bx 48
    add %ax %bx
    stob %gi %ax
    jmp .loop
.back: ; Backspace handler
    div %ax 10
    stob %gi %ax
    jmp .loop

.end:
    mov %sp %bp
    pop %bp
    ret
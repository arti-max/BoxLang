DISK_LIB_BUFFER: reserve 512 bytes

; 1 sector - 512 bytes

; Read 1 sector from disk
; ax - sector
; bx - save_addr
read_sector:
    push %bp
    mov %bp %sp
    ; arg 1 [bp+4]
    mov %ax %bp
    add %ax 4
    mov %sp %ax
    pop %ax
    ; arg2 [bp+6]
    mov %bx %bp
    add %bx 6
    mov %sp %bx
    pop %bx
    
    mov %sp %bp
    ;logic
    mov %cx %ax
    mov %gi 512
    mul %cx 512
.logic:
    cmp %gi $00
    jme .end
    mov %si %cx
    ldds
    mov %si %bx
    storb %ax
    inx %cx
    inx %bx
    dex %gi
    jmp .logic

.end:
    mov %sp %bp
    pop %bp
    ret


num16 DISK_LIB_BUFFER : ?512

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
    push %gi
    mov %gi 512
    mul %ax 512
.logic:
    cmp %gi $00
    jme .end
    lodb %ax %cx
    mov %si %bx
    storb %cx
    inx %ax
    inx %bx
    dex %gi
    jmp .logic

.end:


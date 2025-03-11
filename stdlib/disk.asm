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
    mov %cx %ax ; cx = ax = sector
    mov %gi 512 ; gi = 512 = counter (512 cycles)
    mul %cx 512 ; cx * 512 = start byte to read & write
.logic:
    cmp %gi $00 ; if gi == 0 then end
    jme .end
    mov %si %cx ; si = cx = byte from disk to load
    ldds
    mov %si %bx ; si = bx = save_address
    storb %ax   ; save data from disk to ram
    inx %cx     ; increment point to read from disk
    inx %bx     ; increment save address
    dex %gi     ; counter --
    jmp .logic

.end:
    mov %sp %bp
    pop %bp
    ret


jmp start

TRUE: bytes $01
FALSE: bytes $00
COMPARE_RESULT: reserve 1 bytes
input_buffer: reserve 64 bytes
cmd_help: bytes $68 $65 $6C $70 $00
cmd_exit: bytes $65 $78 $69 $74 $00
msg_help: bytes $31 $20 $31 $20 $32 $20 $0A $00
msg_u: bytes $55 $6E $6B $6E $6F $77 $6E $0A $00
cmd_input_text: bytes $45 $6E $74 $65 $72 $20 $61 $20 $63 $6F $6D $6D $61 $6E $64 $3A $20 $00

; Standard library (def.asm)
; РЎС‚Р°РЅРґР°СЂС‚РЅР°СЏ Р±РёР±Р»РёРѕС‚РµРєР°
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

; Imported code
print:
    push %bp
    mov %bp %sp
    ;arg parse
    mov %si %bp
    add %si 4
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
    add %si 4   ; 1st arg
    mov %sp %si
    pop %si
    mov %sp %bp
    ; logic
    int $01
    pop %ax
    storb %ax
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
    add %si 4
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
    storb %dx
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
    add %ax 4
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
    stgrb %ax
    jmp .loop
.back: ; Backspace handler
    div %ax 10
    stgrb %ax
    jmp .loop
.end:
    mov %sp %bp
    pop %bp
    ret
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

; Main code
start:
.main_loop:
  mov %gi cmd_input_text
  push %gi
  call print
  mov %gi %sp
  add %gi 2
  mov %sp %gi
  mov %gi input_buffer
  push %gi
  call scanstr
  mov %gi %sp
  add %gi 2
  mov %sp %gi
  push 0
  mov %gi COMPARE_RESULT
  push %gi
  call set_new_data
  mov %gi %sp
  add %gi 4
  mov %sp %gi
  mov %gi COMPARE_RESULT
  push %gi
  mov %gi cmd_help
  push %gi
  mov %gi input_buffer
  push %gi
  call string_compare
  mov %gi %sp
  add %gi 6
  mov %sp %gi
  mov %gi COMPARE_RESULT
  cmp *%gi $00
  jme .unknow_com_label
.help_com_label:
  mov %gi msg_help
  push %gi
  call print
  mov %gi %sp
  add %gi 2
  mov %sp %gi
  mov %gi TRUE
  cmp *%gi $00
  jg .main_loop
.unknow_com_label:
  mov %gi COMPARE_RESULT
  push %gi
  mov %gi cmd_exit
  push %gi
  mov %gi input_buffer
  push %gi
  call string_compare
  mov %gi %sp
  add %gi 6
  mov %sp %gi
  mov %gi COMPARE_RESULT
  cmp *%gi $00
  jme .unknow_exit_label
.exit_com_label:
  push 0
  call exit
  mov %gi %sp
  add %gi 2
  mov %sp %gi
.unknow_exit_label:
  mov %gi msg_u
  push %gi
  call print
  mov %gi %sp
  add %gi 2
  mov %sp %gi
  mov %gi TRUE
  cmp *%gi $00
  jg .main_loop
  push 0
  call exit
  mov %gi %sp
  add %gi 2
  mov %sp %gi
  ret

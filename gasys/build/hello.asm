jmp _start

msg: bytes $48 $65 $6C $6C $6F $0A $00
msg2: bytes $49 $46 $0A $00
ext: bytes $68 $65 $6C $70 $00
test1: bytes $D2 $04
test2: bytes $40 $E2 $01
buffer: reserve 64 bytes
cmp_res: reserve 1 bytes

; Standard library (def.asm)
; РЎС‚Р°РЅРґР°СЂС‚РЅР°СЏ Р±РёР±Р»РёРѕС‚РµРєР°
; buffers
cline:  reserve 64 bytes
qptr:   reserve 2 bytes   

; Control sequences
bs_seq:     bytes "^H ^H^@"
cls_seq:    bytes "^[[H^[[2J^@"

puts:
    lodb %si %ax
    cmp %ax $00
    re
    push %ax
    int $02
    jmp puts

exit:
    int $00

trapf:
    trap
    ret

; Imported code
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
je .bs
cmp %bx $08
je .bs

; print
push %dx
int $02

; Save to mem
mov %gi *qptr
add %si %gi
stob %si %dx
sub %si %gi
inx @qptr

; check enter
cmp %dx $0A
je .end
jmp .logic

.bs:
mov %gi *qptr
cmp %gi $00
je .logic
.bs_strict:
dex @qptr
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
je .end
cmp %bx $20 ; Check for space
je .end
cmp %bx $00 ; Check for NUL ($00)
je .end
cmp %bx $30 ; Check if less than '0'
jl .loop
cmp %bx $3A ; Check if greater than '9'+1
jg .loop
cmp %bx $7F ; Check for Backspace
je .back

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
; Data Utils

; Copy string from Target to Dest
; ax - Target
; bx - Dest
datautils_strcpy:
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
mov %si *%ax
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
datautils_num_to_string_16:
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
mov %ax *%ax
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
datautils_num_to_string_24:
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
mov %ax *%ax
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
datautils_memcpy:
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
.loop
mov %si *%ax
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
datautils_string_compare:
; arg1 - Str1   ; bp+4
; arg2 - Str2   ; bp+6
; arg3 - result ; bp+8
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
stob %si %dx ; Load $00 (NUL) instead of $0A (Enter)
mov %si qptr
stob %si %dx

.loop:
mov %si *%ax
mov %gi *%bx
cmp %si %gi
jne .fail
cmp %si $00
je .eq
inx %ax
inx %bx
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
datautils_set_new_data_24:
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
mov %si *%ax
stoh %si %bx
;end
pop %bp
ret

; Set new data to variable [2 byte]
; ax - *var
; bx - data
datautils_set_new_data_16:
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
mov %si *%ax
stow %si %bx
;end
pop %bp
ret


; Set new data to variable [1 byte]
; ax - *var
; bx - data
datautils_set_new_data_8:
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
mov %si *%ax
stob %si %bx
;end
pop %bp
ret


; Main code
_start:
  mov %gi msg
  push %gi
  call print
  mov %gi %sp
  add %gi 3
  mov %sp %gi
  push 800
  call beep
  mov %gi %sp
  add %gi 3
  mov %sp %gi
  mov %gi buffer
  push %gi
  call scanstr
  mov %gi %sp
  add %gi 3
  mov %sp %gi
  mov %gi cmp_res
  push %gi
  mov %gi ext
  push %gi
  mov %gi buffer
  push %gi
  call datautils_string_compare
  mov %gi %sp
  add %gi 12
  mov %sp %gi
  mov %si cmp_res
  lodw %si %gi
  cmp %gi $000001
  jne .END_1
.IF_1:
  mov %gi msg2
  push %gi
  call print
  mov %gi %sp
  add %gi 3
  mov %sp %gi
.END_1:
  push 0
  call exit
  mov %gi %sp
  add %gi 3
  mov %sp %gi
  mov %sp %bp
  pop %bp
  ret

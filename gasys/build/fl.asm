jmp _start

IBUF: reserve 16 bytes
CMP_RES: reserve 1 bytes
__str1: bytes $46 $4C $20 $53 $74 $75 $64 $69 $6F $21 $0A $00
__str2: bytes $61 $00
__str3: bytes $62 $00
__str4: bytes $71 $00

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

; print
push %dx
int $02

; check enter
cmp %dx $0A
je .end
stob %si %dx
inx @qptr
jmp .logic

.bs:
mov %gi qptr
lodw %gi %ax
cmp %gi $00
je .logic
.bs_strict:
push %si
mov %si bs_seq
call puts
pop %si
dex %si
dex @qptr
jmp .logic
.end:
mov %ax $00
stob %si %ax
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
audio_beep:
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
datautils_string_compare:
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
lodh %ax %si
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
lodw %ax %si
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
lodb %ax %si
stob %si %bx
;end
pop %bp
ret


; Main code
_start:
  mov %gi __str1
  push %gi
  call print
  mov %gi %sp
  add %gi 3
  mov %sp %gi
.label1:
  mov %gi IBUF
  push %gi
  call input
  mov %gi %sp
  add %gi 3
  mov %sp %gi
  mov %gi CMP_RES
  push %gi
  mov %gi __str2
  push %gi
  mov %gi IBUF
  push %gi
  call datautils_string_compare
  mov %gi %sp
  add %gi 12
  mov %sp %gi
  mov %si CMP_RES
  lodb %si %gi
  cmp %gi $000001
  jne .END_1
.IF_1:
  push 100
  call audio_beep
  mov %gi %sp
  add %gi 6
  mov %sp %gi
.END_1:
  mov %gi IBUF
  push %gi
  call input
  mov %gi %sp
  add %gi 3
  mov %sp %gi
  mov %gi CMP_RES
  push %gi
  mov %gi __str3
  push %gi
  mov %gi IBUF
  push %gi
  call datautils_string_compare
  mov %gi %sp
  add %gi 12
  mov %sp %gi
  mov %si CMP_RES
  lodb %si %gi
  cmp %gi $000001
  jne .END_2
.IF_2:
  push 200
  call audio_beep
  mov %gi %sp
  add %gi 6
  mov %sp %gi
.END_2:
  mov %gi IBUF
  push %gi
  call input
  mov %gi %sp
  add %gi 3
  mov %sp %gi
  mov %gi CMP_RES
  push %gi
  mov %gi __str4
  push %gi
  mov %gi IBUF
  push %gi
  call datautils_string_compare
  mov %gi %sp
  add %gi 12
  mov %sp %gi
  mov %si CMP_RES
  lodb %si %gi
  cmp %gi $000001
  jne .END_3
.IF_3:
  push 0
  call exit
  mov %gi %sp
  add %gi 3
  mov %sp %gi
.END_3:
   jmp .label1
  mov %sp %bp
  pop %bp
  ret

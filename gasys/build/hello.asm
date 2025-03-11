jmp start

msg: bytes $48 $65 $6C $6C $6F $0A
test1: bytes $04 $D2
test2: bytes $01 $E2 $40

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
stgrb %ax
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

; Main code
test:
  push %bp
  mov %bp %sp
  mov %ax %bp
  add %ax 6
  mov %sp %ax
  pop %ax
  mov %sp %bp
  mov %bx %bp
  add %bx 9
  mov %sp %bx
  pop %bx
  mov %sp %bp
  mov %sp %bp
  pop %bp
  ret

start:
  mov %gi msg
  push %gi
  call print
  mov %gi %sp
  add %gi 2
  mov %sp %gi
  push 0
  call exit
  mov %gi %sp
  add %gi 2
  mov %sp %gi
  ret

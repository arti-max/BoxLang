jmp boot


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
    int $00

trapf:
    trap
    ret

; Imported code
DISK_LIB_BUFFER: reserve 512 bytes

; 1 sector - 512 bytes

; Read 1 sector from disk
; ax - sector
; bx - save_addr
disk_read_sector:
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

DISK_LIB_BUFFER: reserve 512 bytes

; 1 sector - 512 bytes

; Read 1 sector from disk
; ax - sector
; bx - save_addr
disk2_read_sector:
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


; Main code
boot:
  push 0
  push 0
  call disk_read_sector
  mov %gi %sp
  add %gi 4
  mov %sp %gi
  push 512
  push 1
  call disk_read_sector
  mov %gi %sp
  add %gi 4
  mov %sp %gi
  push 1024
  push 2
  call disk_read_sector
  mov %gi %sp
  add %gi 4
  mov %sp %gi
  jmp $0000
  mov %sp %bp
  pop %bp
  ret

bootsecend:    bytes $AA $55

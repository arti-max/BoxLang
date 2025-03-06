; Стандартная библиотека
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

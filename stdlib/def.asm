; Стандартная библиотека
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
; disk_string_tok - Progress the string pointer{disk} until character
; Arguments:
; si - string address
; bx - end character
; (also affects dynptr)
disk_string_tok:
.logic:
    ldds
    cmp %ax $F7 ; End of the disk
    jme .error
    cmp %ax %bx
    jme .done
    inx %si
    jmp .logic
.error:
    mov %bx $01
    jmp .end
.done:
    ldb $00
    jme .end
.end:
    mov %sp %bp
    pop %bp
    ret

; disk_string_subset - Find a specific string in the disk
; Arguments:
; si - address{disk}
; gi - address to the string{mem}
; At the end, si should point to the end of that string on the disk
disk_string_subset:
    mov %bx *%gi

    call disk_string_tok ; Load si with the address to the first character (stored in ax)
        cmp %bx $01
        jme .fnf
    push %gi
    call disk_string_compare ; Compare and store the status into ax
        cmp %ax $00 ; We found the substring (address in si)
    jme .end
    pop %gi
    dex %si

    jmp disk_string_subset
.end: ; File found
    pop %x
    mov %bx $00 ; Success status for an outer function
    ret
.fnf: ; File not found
    mov %si fnf_msg
    call puts
    mov %bx $01 ; Error status for an outer function
    ret

; dstrcmp - Check if two strings are equal (first pointer being on the disk)
; Arguments:
; si - first string address{disk}
; gi - second string address
; Returns:
; ax - status
disk_string_compare:
  ldds
  mov %bx *%gi

  inx %si
  inx %gi

  cmp %ax %bx
  jmne .fail
  cmp %bx $00
  jme .eq
  jmp dstrcmp
.eq:
  mov %ax $00
  ret
.fail:
  mov %ax $01
  ret
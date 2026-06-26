PROCESSOR 18F25K40
#include <xc.inc>

SEND_BIT MACRO bit_number
LOCAL send_zero, send_done
    BSF     LATB, 5, c
    NOP
    NOP
    BTFSS   TABLAT, bit_number, c
    BRA     send_zero

    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    BCF     LATB, 5, c
    BRA     send_done

send_zero:
    BCF     LATB, 5, c
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP

send_done:
    NOP
    NOP
    NOP
    NOP
ENDM

SEND_LAST_BIT MACRO bit_number
LOCAL send_last_zero, send_last_done
    BSF     LATB, 5, c
    NOP
    NOP
    BTFSS   TABLAT, bit_number, c
    BRA     send_last_zero

    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    BCF     LATB, 5, c
    BRA     send_last_done

send_last_zero:
    BCF     LATB, 5, c
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP
    NOP

send_last_done:
ENDM

PSECT txfunc,local,class=CODE,reloc=2

GLOBAL _TX_64LEDS
GLOBAL _pC

_TX_64LEDS:
    MOVFF   _pC + 0, FSR0L
    MOVFF   _pC + 1, FSR0H

    CLRF    PRODL, c
    BCF     LATB, 5, c

tx_next_byte:
    MOVF    POSTINC0, W, c
    MOVWF   TABLAT, c

    SEND_BIT       7
    SEND_BIT       6
    SEND_BIT       5
    SEND_BIT       4
    SEND_BIT       3
    SEND_BIT       2
    SEND_BIT       1
    SEND_LAST_BIT  0

    DECFSZ  PRODL, F, c
    BRA     tx_next_byte

    BCF     LATB, 5, c
    RETURN

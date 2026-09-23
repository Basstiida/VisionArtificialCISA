from config import UNIDADES_VALIDAS, UNIDADES_INFO

#Funcion para validar numeros de unidades y buscar su existencia en UNIDADES_VALIDAS
def validar_numero(num):
    if not num or not num.isdigit() or len(num) not in (3,4): #Verifica que la entrada sea un numero y tenga 3 o 4 digitos
        return None
    if num in UNIDADES_VALIDAS:
        return num
    if len(num) == 3 and num[0] == '5':
        c = num[0] + '0' + num[1:]
        if c in UNIDADES_VALIDAS:
            print(f"[CORREGIDO] {num} -> {c}")
            return c
    if len(num) == 3 and num[0] != '5':
        c = '5' + num
        if c in UNIDADES_VALIDAS:
            print(f"[CORREGIDO] {num} -> {c}")
            return c

    if len(num) == 4 and num[0] != '5':
        c = '5' + num[1:]
        if c in UNIDADES_VALIDAS:
            print(f"[CORREGIDO] {num} -> {c}")
            return c
    return None

#Recibimos un número y devolvemos empresa y tipo consultando UNIDADES_INFO
def info_unidad(num):
    return UNIDADES_INFO.get(num)

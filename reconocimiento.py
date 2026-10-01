from config import UNIDADES_VALIDAS, UNIDADES_INFO, PAD_RATIO
import cv2

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

# Recorta la caja (x1,y1,x2,y2) con un margen extra para no cortar los dígitos
def crop_con_padding(frame, x1, y1, x2, y2, ratio=PAD_RATIO):
    h_img, w_img = frame.shape[:2]          #alto y ancho de la imagen
    pad_x = int((x2 - x1) * ratio)          #margen horizontal en píxeles
    pad_y = int((y2 - y1) * ratio)          #margen vertical en píxeles
    return frame[                           #NumPy usa [y, x]
        max(0, y1 - pad_y): min(h_img, y2 + pad_y),   #alto, sin salirse de la imagen
        max(0, x1 - pad_x): min(w_img, x2 + pad_x),   #ancho, sin salirse de la imagen
    ]

# Mejora el contraste del recorte para que el modelo lea mejor los dígitos
def aplicar_preprocesamiento(crop_bgr):
    if crop_bgr is None or crop_bgr.size == 0:          # recorte vacío: se regresa igual
        return crop_bgr
    lab = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2LAB)     # BGR -> LAB (separa luz y color)
    l, a, b = cv2.split(lab)                            # l = luminosidad, a/b = color
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))  # contraste por zonas
    l_eq = clahe.apply(l)                               # solo se ajusta la luz
    lab_eq = cv2.merge([l_eq, a, b])                    # se juntan los canales
    return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)      # de vuelta a BGR
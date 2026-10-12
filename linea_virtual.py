import threading
from config import CAMARAS, MANIOBRA_SEG, DEBOUNCE_SEG

_estado_tracks = {}                  # (camara, track_id) -> lado, último cruce, número, eventos
_debounce_nums = {}                  # (camara, número) -> hora de su último evento
_tracks_lock   = threading.Lock()    # evita que dos hilos lo modifiquen a la vez

# Dice de qué lado de la línea de esa cámara está el punto (cx, cy)
def lado_actual(camara, cx, cy):
    x1, y1 = CAMARAS[camara]["linea_p1"]
    x2, y2 = CAMARAS[camara]["linea_p2"]
    cruz = (x2 - x1) * (cy - y1) - (y2 - y1) * (cx - x1)   # producto cruzado
    return 'izquierda' if cruz > 0 else 'derecha'          # el signo indica el lado

# Revisa si el bus cruzó la línea: 'entrada', 'salida', 'maniobra' o None
def evaluar_cruce(camara, track_id, cx, cy, numero, timestamp):
    lado = lado_actual(camara, cx, cy)
    key  = (camara, track_id)                               # cada cámara tiene sus propios tracks

    with _tracks_lock:
        if key not in _estado_tracks:                       # primera vez que se ve
            _estado_tracks[key] = {'lado': lado, 'ultimo_cruce': None,
                                   'numero': numero, 'eventos': []}
            return None

        estado_t = _estado_tracks[key]
        if numero and not estado_t['numero']:               # guarda el número si llegó tarde
            estado_t['numero'] = numero

        if lado == estado_t['lado']:                        # sigue del mismo lado
            return None

        lado_anterior    = estado_t['lado']                 # ¡cambió de lado!
        estado_t['lado'] = lado

        if estado_t['ultimo_cruce'] is not None:            # ya había cruzado antes
            if timestamp - estado_t['ultimo_cruce'] < MANIOBRA_SEG:
                estado_t['ultimo_cruce'] = timestamp        # regresó muy rápido
                return 'maniobra'

        estado_t['ultimo_cruce'] = timestamp
        entrada   = CAMARAS[camara]["lado_entrada"]
        direccion = 'salida' if lado_anterior == entrada else 'entrada'

        num_key = (camara, numero or f'track_{track_id}')   # debounce por puerta
        if timestamp - _debounce_nums.get(num_key, 0) < DEBOUNCE_SEG:
            return None                                     # mismo bus hace poco: ignorar
        _debounce_nums[num_key] = timestamp

        estado_t['eventos'].append({'camara': camara, 'track_id': track_id,
                                    'numero': numero or '???',
                                    'direccion': direccion, 'timestamp': timestamp})
        return direccion

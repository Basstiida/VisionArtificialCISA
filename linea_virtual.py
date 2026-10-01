import threading
from config import LINEA_P1, LINEA_P2, LADO_ENTRADA, MANIOBRA_SEG, DEBOUNCE_SEG

_estado_tracks = {}                  # track_id -> lado, último cruce, número, eventos
_debounce_nums = {}                  # número -> hora de su último evento
_tracks_lock   = threading.Lock()    # evita que dos hilos lo modifiquen a la vez

# Dice de qué lado de la línea está el punto (cx, cy)
def lado_actual(cx, cy):
    x1, y1 = LINEA_P1
    x2, y2 = LINEA_P2
    cruz = (x2 - x1) * (cy - y1) - (y2 - y1) * (cx - x1)   # producto cruzado
    return 'izquierda' if cruz > 0 else 'derecha'          # el signo indica el lado

# Revisa si el bus cruzó la línea: 'entrada', 'salida', 'maniobra' o None
def evaluar_cruce(track_id, cx, cy, numero, timestamp):
    lado = lado_actual(cx, cy)
    tid  = str(track_id)

    with _tracks_lock:
        if tid not in _estado_tracks:                       # primera vez que se ve
            _estado_tracks[tid] = {'lado': lado, 'ultimo_cruce': None,
                                   'numero': numero, 'eventos': []}
            return None

        estado_t = _estado_tracks[tid]
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
        direccion = 'salida' if lado_anterior == LADO_ENTRADA else 'entrada'

        num_key = numero or f'track_{track_id}'             # sin número, usa el track
        if timestamp - _debounce_nums.get(num_key, 0) < DEBOUNCE_SEG:
            return None                                     # mismo bus hace poco: ignorar
        _debounce_nums[num_key] = timestamp

        estado_t['eventos'].append({'track_id': track_id, 'numero': numero or '???',
                                    'direccion': direccion, 'timestamp': timestamp})
        return direccion
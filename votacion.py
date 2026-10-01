from collections import Counter, defaultdict
from config import N_VOTOS

votos_por_track = defaultdict(list)    # track_id -> lecturas válidas acumuladas
conf_por_track  = defaultdict(float)   # track_id -> mejor confianza vista

# Agrega una lectura ya validada al historial del autobús
def agregar_voto(track_id, numero, conf):
    if not numero:                                   # sin lectura válida: no vota
        return
    votos_por_track[track_id].append(numero)
    if conf > conf_por_track[track_id]:              # guarda la confianza más alta
        conf_por_track[track_id] = conf
    if len(votos_por_track[track_id]) > N_VOTOS * 3: # máx. 9 votos: se va el más viejo
        votos_por_track[track_id].pop(0)

# Regresa el número si alguno ya tiene N_VOTOS lecturas iguales
def numero_confirmado(track_id):
    votos = votos_por_track[track_id]
    if len(votos) < N_VOTOS:                         # aún no hay votos suficientes
        return None
    cand, veces = Counter(votos).most_common(1)[0]   # el número más repetido
    return cand if veces >= N_VOTOS else None

# Limpia el historial del autobús después de mandar la alerta
def reset_track(track_id):
    votos_por_track[track_id] = []
    conf_por_track[track_id]  = 0.0
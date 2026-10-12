"""
flujo.py
========
Une todas las piezas en el orden real del sistema. Por cada lectura que
llegue de una cámara:

    validar número -> votar -> ¿cruzó la línea? -> guardar en la base

Todavía no sabe nada de YOLO ni de cámaras: recibe los datos ya "vistos"
(posición del bus, número leído por el OCR). Así se puede probar sin hardware.
"""
from config import DEBOUNCE_SEG
from reconocimiento import validar_numero
from votacion import agregar_voto, numero_confirmado, reset_track, conf_por_track
from linea_virtual import evaluar_cruce
import storage

_cruces_pendientes = {}   # (camara, track_id) -> cruce que ocurrió antes de confirmar el número


# Procesa una lectura de un bus en una cámara; regresa el evento guardado o None
def procesar_lectura(camara, track_id, cx, cy, lectura, conf, ts, zona="lateral", ruta=None):
    key = (camara, track_id)                                 # cada cámara tiene sus propios tracks

    agregar_voto(key, validar_numero(lectura), conf)         # 1. validar y votar
    numero = numero_confirmado(key)                          # 2. ¿ya hay número?
    cruce  = evaluar_cruce(camara, track_id, cx, cy, numero, ts)   # 3. ¿cruzó?

    if cruce in ("entrada", "salida"):
        if numero:                                           # cruzó con número: se guarda
            return _registrar(key, numero, cruce, ts, zona, ruta)
        _cruces_pendientes[key] = {"direccion": cruce, "ts": ts}   # cruzó sin número: se espera
        return None

    pendiente = _cruces_pendientes.get(key)                  # 4. ¿había un cruce esperando número?
    if pendiente and numero:
        del _cruces_pendientes[key]
        if ts - pendiente["ts"] <= DEBOUNCE_SEG:             # se confirmó a tiempo: se recupera
            return _registrar(key, numero, pendiente["direccion"], pendiente["ts"], zona, ruta)
    return None


# Guarda el evento en la base y limpia los votos del bus
def _registrar(key, numero, direccion, ts, zona, ruta):
    camara, _ = key
    conf = conf_por_track[key]                               # mejor confianza vista para este bus
    storage.guardar_evento(numero, direccion, conf, camara=camara, zona=zona, ruta=ruta, ts=ts)
    reset_track(key)
    return {"camara": camara, "numero": numero, "direccion": direccion, "conf": conf, "ts": ts}

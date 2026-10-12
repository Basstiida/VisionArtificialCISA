"""
Simula 3 autobuses pasando por las 2 puertas y revisa qué queda en la base.
Borra detecciones.db antes de correrlo si quieres empezar de cero.
"""
import time
import storage
from flujo import procesar_lectura

storage.inicializar()

# A está del lado "izquierda" de la línea y B del lado "derecha".
# Con lado_entrada = "izquierda": B -> A es ENTRADA, A -> B es SALIDA.
A, B = (300, 400), (450, 300)
T = time.time()   # hora real, para que los eventos caigan en "hoy"

def pasar(camara, track_id, desde, hacia, lecturas, t0):
    """Mueve un bus de 'desde' a 'hacia' en len(lecturas) frames, 1 por segundo."""
    n = len(lecturas)
    for i, lectura in enumerate(lecturas):
        cx = int(desde[0] + (hacia[0] - desde[0]) * i / (n - 1))
        cy = int(desde[1] + (hacia[1] - desde[1]) * i / (n - 1))
        ev = procesar_lectura(camara, track_id, cx, cy, lectura, 0.8, t0 + i)
        if ev:
            print(f"  cam{camara} frame {i}: {ev['numero']} {ev['direccion'].upper()}")

print("1) 5038 entra por la cámara 2 (número claro desde el inicio)")
pasar(2, 7, B, A, ["5038", "5038", "5038", "5038", "5038", "5038"], T - 300)

print("2) 2501 sale por la cámara 1 (mismo track_id 7, otra cámara; OCR con errores)")
pasar(1, 7, A, B, ["2501", "abc", "2S01", "2501", "251", "2501"], T - 200)

print("3) 5001 entra por la cámara 1 pero el número se confirma DESPUÉS de cruzar")
pasar(1, 9, B, A, [None, None, None, None, "5001", "5001", "5001", "5001"], T - 100)

print("\nDentro ahora:", [u["no_economico"] for u in storage.dentro_ahora()])
print("Eventos hoy: ", [(e["no_economico"], e["direccion"], e["id_camara"]) for e in storage.eventos_de_hoy()])

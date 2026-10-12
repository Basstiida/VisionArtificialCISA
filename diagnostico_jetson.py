"""
diagnostico_jetson.py
=====================
Revisa, paso por paso, que la Jetson tenga todo lo necesario para la fase de visión:

  1. Librerías: torch con CUDA, ultralytics, OpenCV con GStreamer
  2. Modelos: que los 3 .engine carguen y cuánto tarda cada uno por imagen
  3. Cámaras: que cada cámara abra por RTSP y a cuántos FPS llega
  4. Prueba combinada: el modelo de autobús sobre las 2 cámaras a la vez

Uso (en la Jetson, dentro de la carpeta del proyecto):
    python3 diagnostico_jetson.py
"""
import time
import os

OK, FALLA = "✅", "❌"
resultado = {}


def paso(titulo):
    print(f"\n{'─' * 60}\n{titulo}\n{'─' * 60}")


# ── 1. Librerías ──────────────────────────────────────────────────────────────
paso("1. Librerías")
try:
    import torch
    cuda = torch.cuda.is_available()
    print(f"{OK if cuda else FALLA} torch {torch.__version__}  CUDA={cuda}")
    resultado["cuda"] = cuda
except ImportError:
    print(f"{FALLA} torch no está instalado"); resultado["cuda"] = False

try:
    import ultralytics
    print(f"{OK} ultralytics {ultralytics.__version__}")
except ImportError:
    print(f"{FALLA} ultralytics no está instalado")

import cv2
gst = any(l.strip().startswith("GStreamer") and "YES" in l
          for l in cv2.getBuildInformation().splitlines())
print(f"{OK if gst else FALLA} OpenCV {cv2.__version__}  GStreamer={'sí' if gst else 'NO'}")
resultado["gstreamer"] = gst

from config import MODELO_AUTOBUS, MODELO_ZONA, MODELO_DIGITOS, RTSP_CAM

# ── 2. Modelos ────────────────────────────────────────────────────────────────
paso("2. Modelos")
import numpy as np
modelos = {}
for nombre, ruta in [("autobús (M1)", MODELO_AUTOBUS), ("zona (M2)", MODELO_ZONA), ("dígitos (M3)", MODELO_DIGITOS)]:
    if not os.path.exists(ruta):
        print(f"{FALLA} {nombre}: no existe {ruta}"); continue
    try:
        from ultralytics import YOLO
        m = YOLO(ruta, task="detect")
        img = np.zeros((640, 640, 3), dtype=np.uint8)
        m.predict(img, verbose=False)                       # la primera corrida siempre es lenta
        t0 = time.time()
        for _ in range(20):
            m.predict(img, verbose=False)
        ms = (time.time() - t0) / 20 * 1000
        print(f"{OK} {nombre}: {ms:.1f} ms por imagen  clases={list(m.names.values())}")
        modelos[nombre] = m
    except Exception as e:
        print(f"{FALLA} {nombre}: {e}")


# ── 3. Cámaras ────────────────────────────────────────────────────────────────
def pipeline(url, codec):
    """Pipeline de GStreamer con decodificación por hardware (NVDEC)."""
    return (f"rtspsrc location={url} latency=100 protocols=tcp ! "
            f"rtp{codec}depay ! {codec}parse ! nvv4l2decoder ! "
            "nvvidconv ! video/x-raw,format=BGRx ! videoconvert ! video/x-raw,format=BGR ! "
            "appsink sync=false max-buffers=1 drop=true")


def abrir(url):
    """Prueba H.265 y luego H.264; regresa (captura, codec) o (None, None)."""
    for codec in ("h265", "h264"):
        cap = cv2.VideoCapture(pipeline(url, codec), cv2.CAP_GSTREAMER)
        if cap.isOpened() and cap.read()[0]:
            return cap, codec
        cap.release()
    return None, None


paso("3. Cámaras")
caps = {}
for cam, url in RTSP_CAM.items():
    if not url:
        print(f"{FALLA} cámara {cam}: falta RTSP_CAM{cam} en .env"); continue
    cap, codec = abrir(url)
    if not cap:
        print(f"{FALLA} cámara {cam}: no abre (¿IP, contraseña o red?)"); continue
    t0, n = time.time(), 0
    while n < 50:
        ok, frame = cap.read()
        if ok: n += 1
    fps = n / (time.time() - t0)
    h, w = frame.shape[:2]
    print(f"{OK} cámara {cam}: {w}x{h}  {codec.upper()}  {fps:.1f} FPS")
    cv2.imwrite(f"diag_cam{cam}.jpg", frame)                # para calibrar la línea virtual
    caps[cam] = cap

# ── 4. Prueba combinada ───────────────────────────────────────────────────────
paso("4. Modelo de autobús sobre las cámaras a la vez (20 s)")
m1 = modelos.get("autobús (M1)")
if m1 and caps:
    cuenta = {c: 0 for c in caps}
    t0 = time.time()
    while time.time() - t0 < 20:
        for cam, cap in caps.items():
            ok, frame = cap.read()
            if ok:
                m1.predict(frame, verbose=False)
                cuenta[cam] += 1
    for cam, n in cuenta.items():
        print(f"   cámara {cam}: {n / 20:.1f} FPS analizados")
    print("   Referencia: el original analiza 1 cámara; con ~5 FPS por cámara alcanza para leer números.")
else:
    print("   Se omite: falta el modelo de autobús o ninguna cámara abrió.")

for cap in caps.values():
    cap.release()
print("\nListo. Las fotos diag_cam1.jpg / diag_cam2.jpg sirven para calibrar la línea de cada cámara.")

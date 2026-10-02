import time
import storage

storage.inicializar()
ahora = time.time()
storage.guardar_evento("5038", "entrada", 0.91, camara=1, ts=ahora - 3600)   # entró hace 1 h
storage.guardar_evento("2501", "entrada", 0.85, camara=2, ts=ahora - 1800)   # entró hace 30 min
storage.guardar_evento("5038", "salida",  0.88, camara=2, ts=ahora)          # sale por la cámara 2

print("Dentro ahora:", storage.dentro_ahora())
print("Historial:   ", storage.historial_estancias())
print("Eventos hoy: ", len(storage.eventos_de_hoy()))
print("Pendientes de sincronizar:", len(storage.pendientes_sincronizar()))
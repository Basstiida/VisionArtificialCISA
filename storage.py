import sqlite3
import threading
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from config import UNIDADES_INFO, HORA_CORTE_DIA, ID_PATIO

_BASE   = Path(__file__).resolve().parent
DB_PATH = _BASE / "detecciones.db"
SCHEMA  = _BASE / "schema.sql"
_local  = threading.local()              # una conexión por hilo (SQLite lo exige)

# Regresa la conexión de este hilo; la crea si no existe
def _conn():
    if getattr(_local, "db", None) is None:
        _local.db = sqlite3.connect(DB_PATH)
        _local.db.row_factory = sqlite3.Row   # filas como dict: fila["no_economico"]
    return _local.db

# Crea las tablas si no existen (se llama una vez al arrancar)
def inicializar():
    c = _conn()
    c.executescript(SCHEMA.read_text(encoding="utf-8"))
    c.commit()

# "Hoy" operativo: antes de las 3am todavía cuenta como el día anterior
def _dia_operativo(dt):
    return (dt - timedelta(hours=HORA_CORTE_DIA)).date().isoformat()

# Guarda un cruce y abre o cierra la estancia de la unidad
def guardar_evento(numero, direccion, conf, camara=1, zona="lateral", ruta=None, ts=None):
    hora = datetime.fromtimestamp(ts or datetime.now().timestamp()).strftime("%Y-%m-%dT%H:%M:%S")
    info = UNIDADES_INFO.get(numero, {"empresa": "desconocida", "tipo": "desconocido"})
    c = _conn()
    c.execute("""INSERT INTO evento_paso
                 (uuid, id_patio, id_camara, no_economico, empresa, tipo_unidad,
                  direccion, zona, confianza, ruta_captura, hora_paso)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (str(uuid.uuid4()), ID_PATIO, camara, numero, info["empresa"], info["tipo"],
               direccion, zona, conf, ruta, hora))

    if direccion == "entrada":                       # entra: abre estancia
        c.execute("INSERT INTO estancia (no_economico, empresa, hora_entrada) VALUES (?, ?, ?)",
                  (numero, info["empresa"], hora))
    else:                                            # sale: cierra la última abierta
        c.execute("""UPDATE estancia SET hora_salida = ?, estatus = 'fuera'
                     WHERE id_estancia = (SELECT id_estancia FROM estancia
                                          WHERE no_economico = ? AND estatus = 'dentro'
                                          ORDER BY hora_entrada DESC LIMIT 1)""",
                  (hora, numero))
    c.commit()

# Unidades que están dentro del patio ahora
def dentro_ahora():
    rows = _conn().execute("""SELECT no_economico, empresa, hora_entrada FROM estancia
                              WHERE estatus = 'dentro' ORDER BY hora_entrada""").fetchall()
    return [dict(r) for r in rows]

# Eventos del día operativo actual
def eventos_de_hoy():
    hoy  = _dia_operativo(datetime.now())
    rows = _conn().execute("""SELECT * FROM evento_paso
                              WHERE DATE(hora_paso, ?) = ? ORDER BY hora_paso""",
                           (f"-{HORA_CORTE_DIA} hours", hoy)).fetchall()
    return [dict(r) for r in rows]

# Visitas terminadas con su duración
def historial_estancias(limite=50):
    rows = _conn().execute("""SELECT no_economico, empresa, hora_entrada, hora_salida, minutos
                              FROM estancia WHERE estatus = 'fuera'
                              ORDER BY hora_entrada DESC LIMIT ?""", (limite,)).fetchall()
    return [dict(r) for r in rows]

# Eventos que aún no se mandan a la base central (para la sincronización futura)
def pendientes_sincronizar(limite=500):
    rows = _conn().execute("""SELECT * FROM evento_paso WHERE sincronizado = 0
                              ORDER BY id_evento LIMIT ?""", (limite,)).fetchall()
    return [dict(r) for r in rows]
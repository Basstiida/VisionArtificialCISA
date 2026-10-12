import os

try:                                   # en la Jetson lee el archivo .env; en la Mac puede no existir
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Unidades válidas ──────────────────────────────────────────────────────────
UNIDADES_VALIDAS = {
    "2501","2502","2503","2504","2505","2506","2507","2508","2509","2510","2514","2515",
    "500","501","502","503","504","505","506","508","509","510","511","512",
    "514","515","516","518","520","521","522","523","524","525","526","527",
    "530","532","534","536","537","538","539","541","543","544","545","546",
    "547","548","549","551","554","556","557","558","559","560","561","562",
    "563","564","565","566","567","568","569","572","573","575","576","577",
    "578","580","581","582","583","584","585","586","587","588","589","592",
    "597","598",
    "5001","5002","5003","5004","5005","5006","5007","5008","5009","5010",
    "5011","5012","5013","5014","5015","5016","5017","5018","5019","5020",
    "5021","5022","5023","5024","5025","5026","5027","5028","5029","5030",
    "5031","5032","5033","5034","5035","5036","5037","5038","5039","5040",
    "5041","5042","5043","5044","5045","5046","5047","5048","5049","5050",
    "5051","5052","5053","5054","5055","5056","5057","5058","5059","5060",
    "5061","5062","5063","5064","5065","5066","5067","5068","5069","5070",
    "5071","5072","5089","5131","5143","5154","5191","5209","5234","5255",
    "5300","5344","5345","5346","5395","5425","5486","5498","5539","5552",
    "5553","5557","5597","5701","5703","5725","5738","5765","5770","5788",
    "5830","5848","5863","5969","5989",
}

# ── Diccionario con los metadatos de cada unidad ─────────────────────────────────────────
_ELECTRICAS = {str(i) for i in range(5001, 5057)}
UNIDADES_INFO = {}
for _u in UNIDADES_VALIDAS:
    if _u in _ELECTRICAS:
        UNIDADES_INFO[_u] = {"empresa": "CISA",    "tipo": "electrica"}
    elif _u.startswith("25"):
        UNIDADES_INFO[_u] = {"empresa": "COPATSA", "tipo": "diesel"}
    else:
        UNIDADES_INFO[_u] = {"empresa": "CISA",    "tipo": "diesel"}

# ── Votación ──────────────────────────────────────────────────────────────────
N_VOTOS = 3   # lecturas iguales necesarias para confirmar un número


PAD_RATIO         = 0.08
PAD_RATIO_LATERAL = 0.25

# ── Línea virtual ─────────────────────────────────────────────────────────────
CAMARAS = {               # cada cámara vigila una puerta distinta
    1: {"linea_p1": (280, 250), "linea_p2": (500, 479), "lado_entrada": "izquierda"},
    2: {"linea_p1": (280, 250), "linea_p2": (500, 479), "lado_entrada": "izquierda"},  # TODO: calibrar
}
MANIOBRA_SEG = 20            # si vuelve a cruzar antes de 20 s, es maniobra
DEBOUNCE_SEG = 60            # no repetir el mismo número antes de 60 s


# ── Día operativo ─────────────────────────────────────────────────────────────
HORA_CORTE_DIA = 3      # antes de las 3am cuenta como el día anterior (turno nocturno)

# ── Sitio ─────────────────────────────────────────────────────────────────────
ID_PATIO = "patio_01"   # identificador único de este patio

# ── Modelos YOLO (archivos .engine en la Jetson; no se suben a git) ───────────
MODELO_AUTOBUS = os.getenv("MODELO_AUTOBUS", "modelos/bus_v3.engine")             # M1: detecta el autobús
MODELO_ZONA    = os.getenv("MODELO_ZONA",    "modelos/modelo_vista_v3.engine")    # M2: zona del número
MODELO_DIGITOS = os.getenv("MODELO_DIGITOS", "modelos/modelo_digitos_v3.engine")  # M3: lee los dígitos

# ── URLs de las cámaras (llevan contraseña: solo en .env, nunca en el código) ──
RTSP_CAM = {
    1: os.getenv("RTSP_CAM1", ""),
    2: os.getenv("RTSP_CAM2", ""),
}

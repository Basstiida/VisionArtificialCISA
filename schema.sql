PRAGMA journal_mode = WAL;

-- Cada vez que un bus cruza la línea
CREATE TABLE IF NOT EXISTS evento_paso (
    id_evento    INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid         TEXT    NOT NULL UNIQUE,              -- id único entre todos los patios
    id_patio     TEXT    NOT NULL,                     -- de qué patio viene
    id_camara    INTEGER NOT NULL DEFAULT 1,           -- cámara 1 o 2
    no_economico TEXT    NOT NULL,
    empresa      TEXT    NOT NULL DEFAULT 'desconocida',
    tipo_unidad  TEXT    NOT NULL DEFAULT 'desconocido',
    direccion    TEXT    NOT NULL CHECK (direccion IN ('entrada','salida')),
    zona         TEXT    NOT NULL DEFAULT 'lateral',
    confianza    REAL    NOT NULL DEFAULT 0 CHECK (confianza BETWEEN 0 AND 1),
    ruta_captura TEXT,
    hora_paso    TEXT    NOT NULL,                     -- 'YYYY-MM-DDTHH:MM:SS' hora local
    sincronizado INTEGER NOT NULL DEFAULT 0            -- 0 = falta mandarlo al central
);
CREATE INDEX IF NOT EXISTS idx_ep_hora ON evento_paso(hora_paso);
CREATE INDEX IF NOT EXISTS idx_ep_sync ON evento_paso(sincronizado);

-- Una fila por visita: se abre al entrar y se cierra al salir
CREATE TABLE IF NOT EXISTS estancia (
    id_estancia  INTEGER PRIMARY KEY AUTOINCREMENT,
    no_economico TEXT NOT NULL,
    empresa      TEXT NOT NULL DEFAULT 'desconocida',
    hora_entrada TEXT NOT NULL,
    hora_salida  TEXT,                                 -- NULL mientras sigue dentro
    minutos      REAL GENERATED ALWAYS AS (
        ROUND((julianday(hora_salida) - julianday(hora_entrada)) * 1440, 1)
    ) STORED,                                          -- se calcula solo al cerrar
    estatus      TEXT NOT NULL DEFAULT 'dentro' CHECK (estatus IN ('dentro','fuera'))
);
CREATE INDEX IF NOT EXISTS idx_est_no ON estancia(no_economico, estatus);
# ProyectoCISA

Sistema de visión por computadora que **detecta los autobuses que entran y salen de un patio**: lee su número económico, decide si entraron o salieron y lleva el registro de cuánto tiempo pasan dentro.

Está pensado para correr en una **NVIDIA Jetson** conectada a 2 cámaras IP en la red local del patio. El plan es instalar el mismo sistema en varios patios y, más adelante, juntar los datos de todos en una base central.

Es una réplica, hecha paso a paso, del sistema original `ProyectoIA`. Cada parte se reescribe, se entiende y se prueba antes de pasar a la siguiente.

---

## Estado actual

Está terminada **toda la lógica que no depende de hardware**: se puede probar en cualquier computadora, sin Jetson, sin cámaras y sin modelos de IA.

| Parte | Archivo | Estado |
|---|---|---|
| Padrón de unidades y configuración | `config.py` | ✅ |
| Validación y corrección del número leído | `reconocimiento.py` | ✅ |
| Recorte y mejora de contraste de la imagen | `reconocimiento.py` | ✅ |
| Votación de lecturas por autobús | `votacion.py` | ✅ |
| Detección de entrada / salida (línea virtual) | `linea_virtual.py` | ✅ |
| Base de datos (eventos y estancias) | `schema.sql`, `storage.py` | ✅ |
| Modelos YOLO (autobús, zona, dígitos) | — | Pendiente |
| Lectura de las cámaras (RTSP) | — | Pendiente |
| Alertas por Telegram | — | Pendiente |
| Dashboard web (Flask) | — | Pendiente |
| Sincronización con base central | — | Pendiente |

---

## Cómo funciona (flujo completo)

```
Cámara ──► frame ──► [YOLO] detecta autobús y le da un track_id
                         │
                         ▼
               [YOLO] ubica la zona del número (delantera / lateral / trasera)
                         │
                         ▼
          crop_con_padding ──► aplicar_preprocesamiento ──► [YOLO] lee los dígitos
                         │
                         ▼
                 validar_numero   (¿existe en el padrón? ¿se puede corregir?)
                         │
                         ▼
                  agregar_voto / numero_confirmado   (3 lecturas iguales)
                         │
                         ▼
                   evaluar_cruce   (¿cruzó la línea? ¿entró o salió?)
                         │
                         ▼
                  guardar_evento   (SQLite: evento + estancia)
```

Los pasos marcados con `[YOLO]` son los que faltan; todo lo demás ya existe.

---

## Estructura

```
ProyectoCISA/
├── config.py            Configuración: padrón, umbrales, línea virtual, patio
├── reconocimiento.py    Validar número, recortar imagen, mejorar contraste
├── votacion.py          Confirmar un número por votación de varias lecturas
├── linea_virtual.py     Decidir si el autobús entró, salió o maniobró
├── schema.sql           Definición de las tablas de la base de datos
├── storage.py           Única capa que habla con la base de datos
├── pruebas.py           Pruebas de votación y línea virtual (no se sube a git)
├── prueba_storage.py    Prueba de la base de datos
└── .gitignore
```

---

## Archivos en detalle

### `config.py` — configuración central

Reúne en un solo lugar todos los valores que se pueden ajustar, para no tener números "mágicos" regados por el código.

- **`UNIDADES_VALIDAS`**: el padrón de las 191 unidades reales. Sirve para descartar lecturas imposibles: si el OCR lee un número que no existe, no se toma en cuenta.
- **`UNIDADES_INFO`**: empresa y tipo de cada unidad, deducidos del número:
  - `5001`–`5056` → CISA, eléctrica
  - empieza con `25` → COPATSA, diesel
  - el resto → CISA, diesel
- **`N_VOTOS = 3`**: lecturas iguales necesarias para confirmar un número.
- **`PAD_RATIO = 0.08` / `PAD_RATIO_LATERAL = 0.25`**: margen extra al recortar el número. El lateral lleva más porque esos números salen más pequeños y torcidos.
- **`LINEA_P1`, `LINEA_P2`**: los dos puntos (en píxeles) que forman la línea virtual sobre la imagen de la cámara.
- **`LADO_ENTRADA`**: de qué lado de la línea viene el autobús cuando *sale*. Si las entradas y salidas salen invertidas, se corrige aquí.
- **`MANIOBRA_SEG = 20`**: si un autobús vuelve a cruzar antes de 20 s, se está acomodando, no entrando ni saliendo.
- **`DEBOUNCE_SEG = 60`**: no se registra el mismo número dos veces en menos de 60 s.
- **`HORA_CORTE_DIA = 3`**: hora a la que "empieza" el día operativo (ver *Decisiones de diseño*).
- **`ID_PATIO`**: identificador de este patio, para cuando se junten los datos de varios.

### `reconocimiento.py` — del recorte al número válido

- **`validar_numero(num)`**: revisa que la lectura tenga 3 o 4 dígitos y exista en el padrón. Si no existe, intenta corregir los errores típicos del OCR:
  - 3 dígitos que empiezan con 5 → inserta un `0` (`507` → `5007`)
  - 3 dígitos que no empiezan con 5 → antepone un `5` (`038` → `5038`)
  - 4 dígitos que no empiezan con 5 → cambia el primero por `5` (`1038` → `5038`)

  Regresa el número corregido o `None` si no hay forma de validarlo.
- **`info_unidad(num)`**: regresa empresa y tipo de una unidad.
- **`crop_con_padding(frame, x1, y1, x2, y2, ratio)`**: recorta la zona del número con un margen alrededor, para no cortar los dígitos de las orillas. Usa `max`/`min` para no salirse de la imagen; sin eso, un índice negativo en NumPy recortaría silenciosamente otra parte de la imagen.
- **`aplicar_preprocesamiento(crop)`**: mejora el contraste con **CLAHE** sobre el canal de luminosidad (espacio de color **LAB**). Se usa LAB porque separa la luz del color: así se aumenta el contraste sin alterar los colores. CLAHE trabaja por zonas pequeñas, lo que ayuda cuando el número tiene una parte en sombra y otra al sol.

### `votacion.py` — confirmar un número

Una sola lectura del OCR no es confiable: con reflejos, movimiento o ángulo, puede leer `5036` o `538` en vez de `5038`. Por eso cada autobús (identificado por su `track_id`) acumula varias lecturas y el número solo se confirma cuando uno se repite `N_VOTOS` veces.

- **`agregar_voto(track_id, numero, conf)`**: guarda una lectura **ya validada** y la mejor confianza vista. Conserva como máximo 9 votos (`N_VOTOS * 3`), descartando los más viejos, para que pesen más las lecturas recientes (el autobús se acerca y se lee mejor).
- **`numero_confirmado(track_id)`**: regresa el número más repetido si alcanza `N_VOTOS`; si no, `None`.
- **`reset_track(track_id)`**: limpia el historial después de registrar el evento.

### `linea_virtual.py` — ¿entró o salió?

Se traza una línea imaginaria sobre la imagen. Cuando el centro del autobús pasa de un lado al otro, hubo un cruce.

- **`lado_actual(cx, cy)`**: dice de qué lado de la línea está un punto usando el **producto cruzado**: el signo del resultado indica el lado.
- **`evaluar_cruce(track_id, cx, cy, numero, timestamp)`**: compara el lado actual con el anterior del mismo autobús y regresa:
  - `None` → primera vez que se ve, o sigue del mismo lado
  - `'entrada'` / `'salida'` → cruzó la línea
  - `'maniobra'` → cruzó de regreso en menos de `MANIOBRA_SEG`
  - `None` también si el mismo número ya se registró hace menos de `DEBOUNCE_SEG` (evita contar doble si el tracker cambia el `track_id` a media pasada)

  Usa un `threading.Lock` porque en el sistema real varios hilos consultan este estado a la vez.

### `schema.sql` — las tablas

- **`evento_paso`**: una fila por cada cruce. Es el **dato original** del sistema: número, empresa, tipo, dirección, cámara, confianza, foto y hora. Incluye además `uuid`, `id_patio` y `sincronizado` para el futuro con varios patios.
- **`estancia`**: una fila por visita al patio. Se abre cuando el autobús entra y se cierra cuando sale. La columna `minutos` es **generada**: SQLite la calcula sola al registrar la salida.

`PRAGMA journal_mode = WAL` hace que un corte de luz no corrompa la base y permite leer mientras se escribe.

### `storage.py` — la única puerta a la base de datos

Ningún otro archivo escribe SQL: todos llaman a estas funciones.

- **`inicializar()`**: crea las tablas si no existen (se llama al arrancar).
- **`guardar_evento(numero, direccion, conf, camara, zona, ruta, ts)`**: guarda el cruce y abre o cierra la estancia. Una salida cierra la estancia abierta más reciente de ese número, **sin importar la cámara**, así que un autobús puede entrar por una cámara y salir por otra.
- **`dentro_ahora()`**: unidades que están en el patio en este momento.
- **`eventos_de_hoy()`**: eventos del día operativo actual.
- **`historial_estancias(limite)`**: visitas terminadas con su duración.
- **`pendientes_sincronizar(limite)`**: eventos que aún no se mandan a la base central.

Cada hilo usa su propia conexión (`threading.local`) porque SQLite no permite compartir una conexión entre hilos.

---

## Decisiones de diseño

**¿Por qué SQLite y no PostgreSQL u otra?**
Cada patio genera unos cientos de cruces al día y todo corre en un solo equipo. SQLite no necesita servidor (es un archivo), aguanta cortes de luz en modo WAL, se respalda copiando el archivo y no le quita recursos a la Jetson, que ya corre YOLO, ffmpeg y Flask.

**¿Y cuando haya varios patios?**
Cada Jetson sigue con su SQLite local y funciona aunque se caiga internet. Periódicamente manda los eventos con `sincronizado = 0` a un PostgreSQL central. Por eso cada evento lleva:
- `uuid`: el `id_evento` autoincremental se repite entre patios; el UUID no.
- `id_patio` e `id_camara`: para saber de dónde viene cada evento.
- `sincronizado`: para saber qué falta enviar.

**¿Por qué solo se sincronizan los eventos y no las estancias?**
Las estancias se pueden reconstruir a partir de los eventos. Mandar solo el dato original evita tener dos fuentes que se contradigan.

**¿Por qué solo `storage.py` toca la base de datos?**
Si algún día se cambia de SQLite a otra base, solo se reescribe ese archivo; el resto del código no se entera.

**¿Qué es el "día operativo"?**
El patio tiene turno nocturno: hay unidades que entran a las 23:00 y salen a la 1:00. Si el día se cortara a medianoche, ese turno quedaría partido en dos. Con `HORA_CORTE_DIA = 3`, todo lo que pasa antes de las 3am cuenta como el día anterior.

**Diferencia con el original:** en `ProyectoIA` las consultas usan `DATE(hora_paso, 'localtime', ...)`, pero `hora_paso` ya se guarda en hora local. El `'localtime'` le resta otras 6 horas (hora de México), así que todo lo anterior a las **9am** se contaba como del día anterior. Aquí se quitó.

**¿Por qué validar antes de votar?**
`538` y `5038` son unidades válidas distintas. Si el OCR pierde un dígito, `5038` se lee como `538` y pasa la validación. Validar cada lectura y exigir 3 votos iguales evita confirmar la unidad equivocada por una sola mala lectura.

---

## Cómo probar

Requisitos: Python 3.10+ y OpenCV (solo para las funciones de imagen).

```bash
pip install opencv-python
python pruebas.py          # votación y línea virtual
python prueba_storage.py   # base de datos
```

Resultado esperado de `pruebas.py`:

```
5038 -> None
538 -> None
5038 -> None
5036 -> None
5038 -> 5038
(7, 500, 300, '5038', 1000) -> None
(7, 480, 320, '5038', 1001) -> None
(7, 250, 450, '5038', 1002) -> salida
(7, 500, 300, '5038', 1010) -> maniobra
(8, 250, 450, '5001', 1100) -> None
(8, 500, 300, '5001', 1101) -> entrada
```

Resultado esperado de `prueba_storage.py`: la `2501` dentro del patio, la `5038` con una estancia de 60 minutos y 3 eventos pendientes de sincronizar.

`prueba_storage.py` crea `detecciones.db`; bórralo para empezar de cero. Está en el `.gitignore`, igual que sus archivos `-wal` y `-shm`.

---

## Pendientes

1. **Definir el papel de las 2 cámaras**: si vigilan puertas distintas, cada una registra sus propios cruces; si ven la misma puerta, hay que evitar registrar cada cruce dos veces.
2. Integrar los modelos YOLO (autobús, zona y dígitos) y la lectura de cámaras por RTSP en la Jetson.
3. `reasociar_numero` en `linea_virtual.py`: recuperar el historial cuando el tracker pierde un autobús y lo vuelve a encontrar con otro `track_id`.
4. Alertas por Telegram.
5. Dashboard web con Flask.
6. Base central PostgreSQL y script de sincronización.
7. Cambiar los `print` por `logging`.
8. Confirmar que el rango de unidades eléctricas (`5001`–`5056`) sigue siendo correcto.

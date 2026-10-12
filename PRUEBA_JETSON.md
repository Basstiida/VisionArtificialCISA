# Prueba de diagnóstico en la Jetson

**Objetivo:** comprobar que la Jetson puede correr la parte de visión del nuevo sistema (`ProyectoCISA`) con las **2 cámaras al mismo tiempo**, antes de escribir ese código.

**Tiempo estimado:** 20–30 minutos.
**No modifica nada del sistema actual** (`ProyectoIA`): solo hay que pausarlo durante la prueba y volver a arrancarlo al final.

---

## Antes de empezar

Necesitas:

- Acceso a la Jetson (en sitio o por Tailscale/SSH).
- Acceso al repositorio en GitHub: `https://github.com/Basstiida/VisionArtificialCISA` (si es privado, pide que te agreguen).
- El usuario y la contraseña de las cámaras. Son los mismos que ya usa el sistema actual en `/home/cisa/Documents/ProyectoIA/.env`.

> ⚠️ **No subas a GitHub ningún archivo con contraseñas** (`.env`). Ya está configurado para ignorarse, pero no lo fuerces con `git add -f`.

---

## Paso 1. Descargar el proyecto

```bash
cd /home/cisa/Documents
git clone https://github.com/Basstiida/VisionArtificialCISA.git ProyectoCISA
cd ProyectoCISA
```

Si la carpeta `ProyectoCISA` ya existe de una prueba anterior, en lugar de clonar actualízala:

```bash
cd /home/cisa/Documents/ProyectoCISA
git pull
```

## Paso 2. Activar el entorno de Python del sistema actual

Se reutiliza porque ya tiene PyTorch compilado para la Jetson (con CUDA y TensorRT).

```bash
source /home/cisa/Documents/ProyectoIA/venv/bin/activate
pip install python-dotenv
```

Al activarlo, la terminal muestra `(venv)` al inicio de la línea.

## Paso 3. Copiar los modelos

Son los 3 que usa producción hoy (versión `v3`):

```bash
mkdir -p modelos
cp ../ProyectoIA/modelos/engine/bus_v3.engine            modelos/
cp ../ProyectoIA/modelos/engine/modelo_vista_v3.engine   modelos/
cp ../ProyectoIA/modelos/engine/modelo_digitos_v3.engine modelos/
ls -lh modelos/
```

Deben aparecer los 3 archivos.

## Paso 4. Configurar las cámaras

```bash
cp .env.example .env
nano .env
```

En las dos líneas `RTSP_CAM1` y `RTSP_CAM2`, reemplaza `USUARIO` y `CONTRASEÑA` por los reales. **No cambies** las IPs (`192.168.10.2` y `192.168.10.4`) ni el resto de la línea.

Guardar en nano: `Ctrl + O`, `Enter`, `Ctrl + X`.

## Paso 5. Pausar el sistema actual

El sistema actual usa la GPU y la cámara 1; si sigue corriendo, los resultados salen más bajos de lo real.

```bash
pgrep -af pipe_stream_v2.py
```

- Si **no aparece nada**, no está corriendo: pasa al paso 6.
- Si aparece una línea, **anota el número del inicio** (es el PID) y deténlo:

```bash
kill <PID>
```

> La grabación continua (`cisa-grabacion.service`) **no se toca**; puede seguir corriendo.

## Paso 6. Correr el diagnóstico

```bash
python3 diagnostico_jetson.py 2>&1 | tee diagnostico_resultado.txt
```

Tarda alrededor de 1 minuto (la última parte dura 20 segundos exactos). Al terminar dice `Listo.`

Lo que hace:

1. Revisa las librerías (PyTorch con CUDA, ultralytics, OpenCV con GStreamer).
2. Carga los 3 modelos y mide cuánto tarda cada uno.
3. Abre cada cámara, mide sus FPS y **guarda una foto** de cada una.
4. Corre el modelo de autobús sobre las 2 cámaras a la vez.

Si algo marca ❌, **no lo intentes arreglar**: solo repórtalo en el entregable.

## Paso 7. Volver a arrancar el sistema actual

**Solo si lo detuviste en el paso 5.** Arráncalo como se arranca normalmente en este equipo. Si no sabes cómo, este es el modo habitual:

```bash
cd /home/cisa/Documents/ProyectoIA
source venv/bin/activate
nohup python3 pipe_stream_v2.py > nohup.out 2>&1 &
```

Comprueba que volvió:

```bash
pgrep -af pipe_stream_v2.py
```

Debe aparecer una línea.

## Paso 8. Juntar el entregable

```bash
cd /home/cisa/Documents/ProyectoCISA
zip diagnostico_$(date +%Y%m%d).zip diagnostico_resultado.txt diag_cam1.jpg diag_cam2.jpg
```

---

## Entregable

Un archivo **`diagnostico_AAAAMMDD.zip`** con:

| Archivo | Qué es |
|---|---|
| `diagnostico_resultado.txt` | Toda la salida del diagnóstico |
| `diag_cam1.jpg` | Foto de la cámara 1 (puede faltar si la cámara no abrió) |
| `diag_cam2.jpg` | Foto de la cámara 2 (puede faltar si la cámara no abrió) |

Y en el mensaje con el que lo mandes, contesta:

1. ¿Estaba corriendo el sistema actual y lo detuviste? (sí / no)
2. ¿Lo volviste a arrancar y aparece en `pgrep`? (sí / no)
3. ¿Hubo algún ❌ o error? Si sí, ¿en qué paso?
4. ¿Algo raro que hayas notado? (cámara con imagen negra, desenfocada, de noche, etc.)
5. Fecha y hora de la prueba.

---

## Si algo falla

| Problema | Qué hacer |
|---|---|
| `git clone` pide usuario/contraseña o dice *not found* | El repositorio es privado: pide acceso y vuelve a intentar |
| `No module named ...` | Revisa que la terminal muestre `(venv)`; si no, repite el paso 2 |
| `no existe modelos/...engine` | Repite el paso 3 y revisa que `ls modelos/` muestre los 3 archivos |
| `falta RTSP_CAM1 en .env` | Repite el paso 4; revisa que el archivo se llame `.env` (con punto) |
| `cámara X: no abre` | Anótalo en el entregable y continúa; no cambies nada de la red |
| Se queda congelado más de 3 minutos | `Ctrl + C`, anótalo y entrega lo que haya en `diagnostico_resultado.txt` |

En cualquier caso, **no olvides el paso 7** (volver a arrancar el sistema actual).

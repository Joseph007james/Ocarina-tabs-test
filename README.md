# Ocarina Tab Generator

Convierte partituras a tabs de ocarina de 12 agujeros, con reproducción rítmica
y un lector de partituras opcional que usa reconocimiento óptico de música
(OMR) real corriendo en tu propia máquina, con [homr](https://github.com/liebharc/homr)
(licencia AGPL-3.0, código abierto).

## Estructura

```
index.html        -> Frontend estático. Esto es lo único que necesita
                      GitHub Pages: no toca ningún servidor pago.
backend/
  app.py           -> Servidor Flask local que corre homr (OMR real).
  requirements.txt -> Dependencias de Python del backend.
```

## Frontend (GitHub Pages)

No requiere build ni configuración. El editor de notas, la reproducción y las
tabs de ocarina funcionan completamente en el navegador, sin backend. La
sección "Cargar partitura" también tiene un lector básico integrado
(heurístico, sin backend) que sirve como respaldo automático si el backend
local no está corriendo.

## Backend local opcional (lectura real de partituras con homr)

El lector básico integrado es solo una aproximación geométrica (un
pentagrama, clave de sol, sin acordes). Para una lectura real —que entienda
compases, armadura de clave, corcheas vs. semicorcheas, etc.— podés levantar
el backend en tu propia compu. **No hace falta tocar tu servidor pago**: esto
corre 100% local y la página en GitHub Pages simplemente le habla a
`http://127.0.0.1:5000` cuando está prendido.

### Requisito importante

homr necesita **Python 3.10, 3.11 o 3.12** (no funciona con 3.13 o más
nuevo). Si no estás seguro de tu versión, corré `python --version` (o
`python3 --version`) antes de instalar.

### Notas sobre homr

- Licencia **AGPL-3.0**: como este repo ya es open source, no te complica en
  nada. Solo tenelo presente si algún día pensás en una versión de código
  cerrado — la AGPL exige liberar el código fuente de cualquier app que lo
  use como servicio.
- Corre en CPU sin problema (~15 seg por página según sus propios
  benchmarks), bastante más rápido que otras alternativas.
- Funciona mejor con una sola pauta (un pentagrama) o pentagrama doble
  (piano), clave de sol o de fa, imagen recta y nítida.
- No reporta dinámica, articulaciones ni dobles sostenidos/bemoles — para
  ocarina esto no suele importar porque no cambia la digitación.

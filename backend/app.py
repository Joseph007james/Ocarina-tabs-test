"""
Backend local para el lector de partituras.

Recibe una imagen (o PDF de una página) desde el frontend, la pasa por
homr (https://github.com/liebharc/homr) para obtener un MusicXML,
y lo convierte al formato "Nota:Duración" que usa la página
(ej: "A5:8 A5:8 C6:8 D6:4 ...").

Correr:
    pip install -r requirements.txt
    python app.py

Por defecto escucha en http://127.0.0.1:5000 y solo acepta pedidos
desde el navegador local (CORS abierto, pero pensado para uso local).
"""

import glob
import os
import subprocess
import tempfile

from flask import Flask, jsonify, request
from flask_cors import CORS
from music21 import converter

app = Flask(__name__)
CORS(app)

# (quarterLength de music21, código de duración usado en la página)
# 4.0 = redonda, 2.0 = blanca, 1.0 = negra, 0.5 = corchea, 0.25 = semicorchea
SUPPORTED_DURATIONS = [
    (4.0, 1),
    (2.0, 2),
    (1.0, 4),
    (0.5, 8),
    (0.25, 16),
]

HOMR_TIMEOUT_SECONDS = 300  # 5 minutos: homr en CPU suele tardar bastante menos que esto


def quarterlength_to_duration_code(quarter_length):
    """Redondea una duración musical (music21) al código más cercano soportado."""
    ql = float(quarter_length)
    best = min(SUPPORTED_DURATIONS, key=lambda pair: abs(pair[0] - ql))
    return best[1]


def pitch_to_note_name(p):
    """Convierte un Pitch de music21 (ej. D#5, B-4) al formato de la página
    (ej. D#5, BB4 -- 'B' se usa como sufijo de bemol, no como nota B)."""
    acc = ""
    if p.accidental is not None:
        if p.accidental.name == "sharp":
            acc = "#"
        elif p.accidental.name == "flat":
            acc = "B"
        # dobles sostenidos/bemoles y microtonales no tienen digitación de
        # ocarina definida en la página; se dejan sin marcar el accidental
        # extra y se deja la nota base para que el usuario la revise.
    return f"{p.step}{acc}{p.octave}"


def musicxml_to_tokens(xml_path):
    """Recorre un MusicXML (parseado con music21) y devuelve la lista de
    tokens 'Nota:Duracion' / 'R:Duracion' en orden. Es monofónico: si hay
    acordes, se queda solo con la nota más aguda (asumimos que es lo que
    se toca con la ocarina)."""
    score = converter.parse(xml_path)
    tokens = []
    for el in score.flatten().notesAndRests:
        dur_code = quarterlength_to_duration_code(el.quarterLength)
        if el.isRest:
            tokens.append(f"R:{dur_code}")
        elif el.isChord:
            top_pitch = sorted(el.pitches, key=lambda p: p.midi)[-1]
            tokens.append(f"{pitch_to_note_name(top_pitch)}:{dur_code}")
        else:
            tokens.append(f"{pitch_to_note_name(el.pitch)}:{dur_code}")
    return tokens


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No se recibió ningún archivo"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Archivo vacío"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, file.filename)
        file.save(input_path)

        try:
            # homr guarda el .musicxml en la misma carpeta que la imagen de entrada
            # (no usa -o como oemer).
            subprocess.run(
                ["homr", input_path],
                check=True,
                capture_output=True,
                text=True,
                timeout=HOMR_TIMEOUT_SECONDS,
                cwd=tmpdir,
            )
        except FileNotFoundError:
            return jsonify({
                "error": "No se encontró el comando 'homr'. ¿Corriste 'pip install -r requirements.txt' con Python 3.10-3.12?"
            }), 500
        except subprocess.CalledProcessError as e:
            return jsonify({"error": f"homr falló al procesar la imagen: {e.stderr[-800:]}"}), 500
        except subprocess.TimeoutExpired:
            return jsonify({
                "error": f"homr tardó más de {HOMR_TIMEOUT_SECONDS // 60} minutos y se canceló. Probá con una imagen más simple o más chica."
            }), 500

        xml_files = glob.glob(os.path.join(tmpdir, "*.musicxml")) + glob.glob(
            os.path.join(tmpdir, "*.xml")
        )
        if not xml_files:
            return jsonify({"error": "homr no generó ningún MusicXML para esta imagen."}), 500

        try:
            tokens = musicxml_to_tokens(xml_files[0])
        except Exception as e:  # noqa: BLE001 - queremos reportar cualquier error de parseo al frontend
            return jsonify({"error": f"Error leyendo el MusicXML generado: {e}"}), 500

    if not tokens:
        return jsonify({"error": "No se detectaron notas en la partitura."}), 500

    # Nota: homr enfoca clave de sol y de fa, notas y ritmo; no reporta
    # dinámica, articulaciones ni dobles sostenidos/bemoles (ver limitaciones
    # en https://github.com/liebharc/homr). Para ocarina esto no suele ser
    # un problema porque esos matices no cambian la digitación.

    return jsonify({"tokens": tokens, "text": " ".join(tokens)})


if __name__ == "__main__":
    # host 127.0.0.1: solo accesible desde tu propia máquina.
    app.run(host="127.0.0.1", port=5000, debug=False)

"""
QR Code Generator — Flask Web Application
"""
import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from qr_engine import generate_qr

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB max upload
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
app.config["OUTPUT_FOLDER"] = os.path.join(os.path.dirname(__file__), "static", "generated")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "svg", "webp"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# --------------- Routes ---------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "No data provided"}), 400

        qr_type = payload.get("qr_type", "url")
        data = payload.get("data", {})
        fg_color = payload.get("fg_color", "#000000")
        bg_color = payload.get("bg_color", "#FFFFFF")
        gradient_end = payload.get("gradient_end")
        color_style = payload.get("color_style", "solid")
        module_style = payload.get("module_style", "square")
        error_correction = payload.get("error_correction", "M")
        logo_filename = payload.get("logo_filename")
        output_format = payload.get("output_format", "png")
        size = int(payload.get("size", 20))
        border = int(payload.get("border", 4))

        logo_path = None
        if logo_filename:
            logo_path = os.path.join(app.config["UPLOAD_FOLDER"], logo_filename)
            if not os.path.exists(logo_path):
                logo_path = None

        filename = generate_qr(
            qr_type=qr_type,
            data=data,
            fg_color=fg_color,
            bg_color=bg_color,
            gradient_end=gradient_end,
            color_style=color_style,
            module_style=module_style,
            error_correction=error_correction,
            logo_path=logo_path,
            output_format=output_format,
            size=size,
            border=border,
            output_dir=app.config["OUTPUT_FOLDER"],
        )

        file_url = f"/static/generated/{filename}"
        download_url = f"/download/{filename}"

        return jsonify({
            "success": True,
            "filename": filename,
            "file_url": file_url,
            "download_url": download_url,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(
        app.config["OUTPUT_FOLDER"],
        filename,
        as_attachment=True,
    )


@app.route("/view/<filename>")
def view_qr(filename):
    """Serve a standalone page with just the QR code — ideal for phone scanning."""
    return f'''<!DOCTYPE html>
<html><head><title>Scan QR Code</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#fff;}}
img{{max-width:90vmin;max-height:90vmin;image-rendering:pixelated;}}</style>
</head><body><img src="/static/generated/{filename}" alt="QR Code"></body></html>'''


@app.route("/upload-logo", methods=["POST"])
def upload_logo():
    if "logo" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["logo"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    filename = secure_filename(file.filename)
    # Add unique prefix to avoid collisions
    import uuid
    unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(filepath)

    return jsonify({
        "success": True,
        "filename": unique_name,
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

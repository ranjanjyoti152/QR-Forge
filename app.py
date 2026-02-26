"""
QR Code Generator — Flask Web Application
"""
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from urllib.parse import quote, unquote
import base64
from qr_engine import generate_qr

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB max upload
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
app.config["OUTPUT_FOLDER"] = os.path.join(os.path.dirname(__file__), "static", "generated")
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "qr_history.json")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "svg", "webp"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


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

        # iOS compatibility: wrap plain text as a URL
        if qr_type == "text" and data.get("_iosCompat"):
            text_content = data.get("text", "")
            host = request.host
            scheme = request.scheme
            # Use base64 to safely encode any text (newlines, colons, etc.)
            b64 = base64.urlsafe_b64encode(text_content.encode('utf-8')).decode('ascii')
            data = {"url": f"{scheme}://{host}/t?d={b64}"}
            qr_type = "url"

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

        # Save to history
        original_type = payload.get("qr_type", "url")
        original_data = payload.get("data", {})
        # Remove internal keys from data
        display_data = {k: v for k, v in original_data.items() if not k.startswith('_')}
        
        history_entry = {
            "id": filename.replace("qr_", "").split(".")[0],
            "qr_type": original_type,
            "data": display_data,
            "label": _make_label(original_type, display_data),
            "filename": filename,
            "file_url": file_url,
            "download_url": download_url,
            "fg_color": fg_color,
            "bg_color": bg_color,
            "module_style": module_style,
            "output_format": output_format,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        history = load_history()
        history.insert(0, history_entry)
        history = history[:50]  # Keep last 50
        save_history(history)

        return jsonify({
            "success": True,
            "filename": filename,
            "file_url": file_url,
            "download_url": download_url,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _make_label(qr_type, data):
    """Create a short label for the history entry."""
    if qr_type == "url":
        url = data.get("url", "")
        return url[:50] + ("..." if len(url) > 50 else "")
    elif qr_type == "text":
        text = data.get("text", "")
        return text[:50] + ("..." if len(text) > 50 else "")
    elif qr_type == "wifi":
        return f"WiFi: {data.get('ssid', '')}"
    elif qr_type == "vcard":
        return f"Contact: {data.get('fullName', '')}"
    elif qr_type == "email":
        return f"Email: {data.get('to', '')}"
    elif qr_type == "sms":
        return f"SMS: {data.get('phone', '')}"
    elif qr_type == "phone":
        return f"Phone: {data.get('phone', '')}"
    elif qr_type == "event":
        return f"Event: {data.get('title', '')}"
    return qr_type


@app.route("/history")
def get_history():
    """Return QR generation history."""
    history = load_history()
    return jsonify({"success": True, "history": history})


@app.route("/history/<entry_id>", methods=["DELETE"])
def delete_history(entry_id):
    """Delete a single history entry."""
    history = load_history()
    history = [h for h in history if h.get("id") != entry_id]
    save_history(history)
    return jsonify({"success": True})


@app.route("/history", methods=["DELETE"])
def clear_history():
    """Clear all history."""
    save_history([])
    return jsonify({"success": True})

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(
        app.config["OUTPUT_FOLDER"],
        filename,
        as_attachment=True,
    )


@app.route("/t")
def show_text():
    """Display QR code text content — used for iOS compatibility."""
    b64_data = request.args.get('d', '')
    try:
        decoded = base64.urlsafe_b64decode(b64_data.encode('ascii')).decode('utf-8')
    except Exception:
        decoded = unquote(b64_data)
    
    # Escape HTML to prevent XSS
    import html
    safe_text = html.escape(decoded).replace('\n', '<br>')
    
    return f'''<!DOCTYPE html>
<html><head><title>QR Code Content</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body{{margin:0;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;
    background:#0a0a0f;color:#e8e8f0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;padding:60px 24px 24px;gap:24px;}}
  .logo-link{{display:block;transition:transform 0.2s ease;}}
  .logo-link:hover{{transform:scale(1.05);}}
  .logo-link img{{height:60px;width:auto;filter:drop-shadow(0 2px 8px rgba(108,99,255,0.3));}}
  .card{{max-width:600px;width:100%;background:rgba(18,18,28,0.9);border:1px solid rgba(255,255,255,0.06);
    border-radius:16px;padding:32px;box-shadow:0 8px 32px rgba(0,0,0,0.5);}}
  .label{{font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;color:#8888a0;margin-bottom:12px;}}
  .content{{font-size:1.1rem;line-height:1.7;word-break:break-word;}}
</style>
</head><body>
<a href="https://www.proxpc.com" target="_blank" class="logo-link">
  <img src="https://www.proxpc.com/img/logo.svg" alt="ProX PC">
</a>
<div class="card">
  <div class="label">QR Code Content</div>
  <div class="content">{safe_text}</div>
</div>
</body></html>'''


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

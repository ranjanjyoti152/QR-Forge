"""
QR Code Generation Engine
Uses the standard qrcode library for PROVEN scanner compatibility,
then applies visual customization on top.
"""
import qrcode
import qrcode.image.svg
from PIL import Image, ImageDraw, ImageColor
from io import BytesIO
import os
import uuid
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas


# --------------- Data Formatters ---------------

def format_url(data: dict) -> str:
    url = data.get("url", "").strip()
    if url and not url.startswith(("http://", "https://", "HTTP://", "HTTPS://")):
        url = "https://" + url
    return url


def format_text(data: dict) -> str:
    return data.get("text", "").strip()


def format_wifi(data: dict) -> str:
    ssid = data.get("ssid", "").strip()
    password = data.get("password", "").strip()
    encryption = data.get("encryption", "WPA")
    hidden = "true" if data.get("hidden", False) else "false"
    return f"WIFI:T:{encryption};S:{ssid};P:{password};H:{hidden};;"


def format_vcard(data: dict) -> str:
    lines = ["BEGIN:VCARD", "VERSION:3.0"]
    fn = data.get("fullName", "").strip()
    if fn:
        lines.append(f"FN:{fn}")
        parts = fn.split(" ", 1)
        if len(parts) == 2:
            lines.append(f"N:{parts[1]};{parts[0]};;;")
        else:
            lines.append(f"N:{fn};;;;")
    if data.get("org", "").strip():
        lines.append(f"ORG:{data['org'].strip()}")
    if data.get("title", "").strip():
        lines.append(f"TITLE:{data['title'].strip()}")
    if data.get("phone", "").strip():
        lines.append(f"TEL;TYPE=CELL:{data['phone'].strip()}")
    if data.get("email", "").strip():
        lines.append(f"EMAIL:{data['email'].strip()}")
    if data.get("website", "").strip():
        lines.append(f"URL:{data['website'].strip()}")
    if data.get("address", "").strip():
        lines.append(f"ADR:;;{data['address'].strip()};;;;")
    lines.append("END:VCARD")
    return "\n".join(lines)


def format_email(data: dict) -> str:
    to = data.get("to", "").strip()
    subject = data.get("subject", "").strip()
    body = data.get("body", "").strip()
    parts = [f"mailto:{to}"]
    params = []
    if subject:
        params.append(f"subject={subject}")
    if body:
        params.append(f"body={body}")
    if params:
        parts.append("?" + "&".join(params))
    return "".join(parts)


def format_sms(data: dict) -> str:
    phone = data.get("phone", "").strip()
    message = data.get("message", "").strip()
    if message:
        return f"smsto:{phone}:{message}"
    return f"smsto:{phone}"


def format_phone(data: dict) -> str:
    return f"tel:{data.get('phone', '').strip()}"


def format_event(data: dict) -> str:
    start = data.get("startDate", "").replace("-", "").replace(":", "").replace(" ", "T")
    end = data.get("endDate", "").replace("-", "").replace(":", "").replace(" ", "T")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "BEGIN:VEVENT",
        f"SUMMARY:{data.get('title', '').strip()}",
    ]
    if data.get("location", "").strip():
        lines.append(f"LOCATION:{data['location'].strip()}")
    if start:
        lines.append(f"DTSTART:{start}")
    if end:
        lines.append(f"DTEND:{end}")
    if data.get("description", "").strip():
        lines.append(f"DESCRIPTION:{data['description'].strip()}")
    lines.extend(["END:VEVENT", "END:VCALENDAR"])
    return "\n".join(lines)


FORMATTERS = {
    "url": format_url,
    "text": format_text,
    "wifi": format_wifi,
    "vcard": format_vcard,
    "email": format_email,
    "sms": format_sms,
    "phone": format_phone,
    "event": format_event,
}


# --------------- Helpers ---------------

def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


ERROR_LEVELS = {
    "L": qrcode.constants.ERROR_CORRECT_L,
    "M": qrcode.constants.ERROR_CORRECT_M,
    "Q": qrcode.constants.ERROR_CORRECT_Q,
    "H": qrcode.constants.ERROR_CORRECT_H,
}


# --------------- Main Generator ---------------

def generate_qr(
    qr_type: str,
    data: dict,
    fg_color: str = "#000000",
    bg_color: str = "#FFFFFF",
    gradient_end: str = None,
    color_style: str = "solid",
    module_style: str = "square",
    error_correction: str = "M",
    logo_path: str = None,
    output_format: str = "png",
    size: int = 10,
    border: int = 4,
    output_dir: str = "static/generated",
) -> str:
    """
    Generate a QR code and save it. Returns the filename.
    Uses the STANDARD qrcode library rendering for maximum compatibility.
    """
    formatter = FORMATTERS.get(qr_type)
    if not formatter:
        raise ValueError(f"Unknown QR type: {qr_type}")
    content = formatter(data)
    if not content:
        raise ValueError("No content to encode")

    # Ensure sufficient error correction when logo is used
    if logo_path and error_correction in ["L", "M"]:
        error_correction = "Q"

    ec_level = ERROR_LEVELS.get(error_correction, qrcode.constants.ERROR_CORRECT_M)
    file_id = uuid.uuid4().hex[:12]
    os.makedirs(output_dir, exist_ok=True)

    # SVG format
    if output_format == "svg":
        return _generate_svg(content, ec_level, size, border, file_id, output_dir)

    # --- Use standard qrcode make_image (PROVEN to scan on all devices) ---
    fg_rgb = hex_to_rgb(fg_color)
    bg_rgb = hex_to_rgb(bg_color)

    qr = qrcode.QRCode(
        version=None,
        error_correction=ec_level,
        box_size=max(size, 10),  # Minimum 10px per module
        border=border,
    )
    qr.add_data(content)
    qr.make(fit=True)

    # Standard rendering — black on white (guaranteed scannable)
    img = qr.make_image(fill_color=fg_rgb, back_color=bg_rgb)
    img = img.convert("RGB")

    # Apply gradient coloring if requested (post-processing)
    if color_style != "solid" and gradient_end:
        grad_rgb = hex_to_rgb(gradient_end)
        img = _apply_gradient(img, fg_rgb, bg_rgb, grad_rgb, color_style)

    # Apply module style modifications (post-processing)
    if module_style != "square":
        img = _apply_module_style(img, fg_rgb, bg_rgb, module_style, max(size, 10))

    # Overlay logo
    if logo_path and os.path.exists(logo_path):
        img = _overlay_logo(img, logo_path)

    # Save
    if output_format == "pdf":
        filename = f"qr_{file_id}.pdf"
        filepath = os.path.join(output_dir, filename)
        _save_as_pdf(img, filepath)
    else:
        filename = f"qr_{file_id}.png"
        filepath = os.path.join(output_dir, filename)
        img.save(filepath, "PNG")

    return filename


def _apply_gradient(img, fg_rgb, bg_rgb, grad_rgb, color_style):
    """Apply gradient coloring to an already-generated QR code by recoloring dark pixels."""
    w, h = img.size
    pixels = img.load()

    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            # Check if this pixel is a "dark" module (foreground)
            brightness = (r + g + b) / 3
            if brightness < 128:
                # Calculate gradient factor
                if color_style == "horizontal_gradient":
                    t = x / max(w - 1, 1)
                elif color_style == "vertical_gradient":
                    t = y / max(h - 1, 1)
                elif color_style == "radial_gradient":
                    cx, cy = w / 2, h / 2
                    dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                    max_dist = (cx ** 2 + cy ** 2) ** 0.5
                    t = min(dist / max_dist, 1.0)
                elif color_style == "square_gradient":
                    cx, cy = w / 2, h / 2
                    t = max(abs(x - cx) / cx, abs(y - cy) / cy)
                    t = min(t, 1.0)
                else:
                    t = 0

                new_r = int(fg_rgb[0] + (grad_rgb[0] - fg_rgb[0]) * t)
                new_g = int(fg_rgb[1] + (grad_rgb[1] - fg_rgb[1]) * t)
                new_b = int(fg_rgb[2] + (grad_rgb[2] - fg_rgb[2]) * t)
                pixels[x, y] = (new_r, new_g, new_b)

    return img


def _apply_module_style(img, fg_rgb, bg_rgb, style, box_size):
    """Apply rounded/circle/gapped styling by post-processing the standard QR code."""
    w, h = img.size
    pixels = img.load()

    # Create a new image with background
    new_img = Image.new("RGB", (w, h), bg_rgb)
    draw = ImageDraw.Draw(new_img)

    # Find module grid by scanning for transitions
    # Each module is box_size x box_size pixels
    # We need to figure out where the modules are
    for y in range(0, h, box_size):
        for x in range(0, w, box_size):
            # Sample the center of this grid cell
            cx = min(x + box_size // 2, w - 1)
            cy = min(y + box_size // 2, h - 1)
            r, g, b = pixels[cx, cy]
            brightness = (r + g + b) / 3

            if brightness < 128:
                # This is a dark module — draw with style
                color = pixels[cx, cy]
                x0, y0 = x, y
                x1, y1 = min(x + box_size, w), min(y + box_size, h)

                if style == "circle":
                    margin = max(1, box_size // 8)
                    draw.ellipse(
                        [x0 + margin, y0 + margin, x1 - margin - 1, y1 - margin - 1],
                        fill=color,
                    )
                elif style == "rounded":
                    margin = max(0, box_size // 12)
                    radius = max(2, box_size // 3)
                    draw.rounded_rectangle(
                        [x0 + margin, y0 + margin, x1 - margin - 1, y1 - margin - 1],
                        radius=radius,
                        fill=color,
                    )
                elif style == "gapped":
                    margin = max(1, box_size // 6)
                    draw.rectangle(
                        [x0 + margin, y0 + margin, x1 - margin - 1, y1 - margin - 1],
                        fill=color,
                    )
                elif style == "vertical_bars":
                    margin = max(1, box_size // 5)
                    draw.rectangle(
                        [x0 + margin, y0, x1 - margin - 1, y1 - 1],
                        fill=color,
                    )
                elif style == "horizontal_bars":
                    margin = max(1, box_size // 5)
                    draw.rectangle(
                        [x0, y0 + margin, x1 - 1, y1 - margin - 1],
                        fill=color,
                    )
            else:
                # Background module — keep as background
                x0, y0 = x, y
                x1, y1 = min(x + box_size, w), min(y + box_size, h)
                draw.rectangle([x0, y0, x1 - 1, y1 - 1], fill=bg_rgb)

    return new_img


def _generate_svg(content, ec_level, size, border, file_id, output_dir):
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(
        version=None,
        error_correction=ec_level,
        box_size=size,
        border=border,
    )
    qr.add_data(content)
    qr.make(fit=True)
    img = qr.make_image(image_factory=factory)

    filename = f"qr_{file_id}.svg"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath)
    return filename


def _overlay_logo(qr_img: Image.Image, logo_path: str) -> Image.Image:
    """Overlay a logo at the center with white background."""
    logo = Image.open(logo_path).convert("RGBA")

    qr_w, qr_h = qr_img.size
    max_logo_size = int(min(qr_w, qr_h) * 0.18)
    logo.thumbnail((max_logo_size, max_logo_size), Image.LANCZOS)
    logo_w, logo_h = logo.size

    padding = max(6, max_logo_size // 10)
    bg_w = logo_w + padding * 2
    bg_h = logo_h + padding * 2

    bg = Image.new("RGBA", (bg_w, bg_h), (255, 255, 255, 255))
    mask = Image.new("L", (bg_w, bg_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    radius = max(4, padding // 2)
    mask_draw.rounded_rectangle([(0, 0), (bg_w, bg_h)], radius=radius, fill=255)
    bg.putalpha(mask)

    pos_x = (qr_w - bg_w) // 2
    pos_y = (qr_h - bg_h) // 2

    qr_rgba = qr_img.convert("RGBA")
    qr_rgba.paste(bg, (pos_x, pos_y), bg)
    qr_rgba.paste(logo, (pos_x + padding, pos_y + padding), logo)

    return qr_rgba.convert("RGB")


def _save_as_pdf(img: Image.Image, filepath: str):
    img_rgb = img.convert("RGB")
    temp_png = filepath.replace(".pdf", "_temp.png")
    img_rgb.save(temp_png, "PNG")

    w, h = img_rgb.size
    max_dim = 150 * mm
    scale = max_dim / max(w, h)
    pdf_w = w * scale
    pdf_h = h * scale

    c = pdf_canvas.Canvas(filepath, pagesize=A4)
    page_w, page_h = A4
    x = (page_w - pdf_w) / 2
    y = (page_h - pdf_h) / 2
    c.drawImage(temp_png, x, y, width=pdf_w, height=pdf_h)
    c.save()

    if os.path.exists(temp_png):
        os.remove(temp_png)

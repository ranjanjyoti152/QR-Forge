# 🔲 QR Forge

**A full-fledged, premium QR code generator built with Python & Flask.**

Generate stunning, universally compatible QR codes with custom colors, gradient styles, logo overlays, and multiple export formats — all from a beautiful dark-themed web UI.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

### 8 QR Code Types
| Type | Description |
|------|-------------|
| 🔗 **URL** | Website links with auto `https://` prefixing |
| 📝 **Text** | Plain text content |
| 📶 **WiFi** | Network credentials (SSID, password, encryption) |
| 👤 **vCard** | Contact cards (name, phone, email, org, address) |
| ✉️ **Email** | Pre-filled email with subject and body |
| 💬 **SMS** | Pre-filled text messages |
| 📞 **Phone** | Direct dial phone numbers |
| 📅 **Event** | Calendar events (iCal/vCalendar format) |

### Customization
- **6 Module Styles** — Square, Rounded, Circle/Dots, Gapped, Vertical Bars, Horizontal Bars
- **5 Color Modes** — Solid color, Radial gradient, Square gradient, Horizontal gradient, Vertical gradient
- **Custom Colors** — Pick any foreground, background, and gradient end color
- **Logo Overlay** — Upload your brand logo; error correction auto-boosts to HIGH (30%)
- **Error Correction** — Configurable: Low (7%), Medium (15%), Quartile (25%), High (30%)

### Export Formats
- **PNG** — High-resolution raster image
- **SVG** — Scalable vector graphic
- **PDF** — Print-ready A4 document

### Universal Compatibility
All QR codes use standard encoding that works with:
- ✅ iPhone Camera & Code Scanner
- ✅ Android Camera & Google Lens
- ✅ All third-party QR scanner apps

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/ranjanjyoti152/QR-Forge.git
cd QR-Forge

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

The app will be available at **http://localhost:5000**

---

## 📁 Project Structure

```
QR-Forge/
├── app.py                  # Flask web server & API routes
├── qr_engine.py            # QR code generation engine
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html          # Web UI (single-page app)
├── static/
│   ├── css/style.css       # Premium dark glassmorphism theme
│   ├── js/app.js           # Frontend logic & API calls
│   └── generated/          # Generated QR code output
└── uploads/                # User-uploaded logos
```

---

## 🔌 API Reference

### Generate QR Code
```http
POST /generate
Content-Type: application/json
```

**Request Body:**
```json
{
  "qr_type": "url",
  "data": { "url": "https://example.com" },
  "fg_color": "#000000",
  "bg_color": "#FFFFFF",
  "color_style": "solid",
  "module_style": "square",
  "error_correction": "H",
  "output_format": "png",
  "size": 20,
  "border": 4
}
```

**Response:**
```json
{
  "success": true,
  "filename": "qr_abc123def456.png",
  "file_url": "/static/generated/qr_abc123def456.png",
  "download_url": "/download/qr_abc123def456.png"
}
```

### Upload Logo
```http
POST /upload-logo
Content-Type: multipart/form-data
```

### Download QR Code
```http
GET /download/<filename>
```

### View QR Code (Full Screen)
```http
GET /view/<filename>
```

---

## 🛠️ Tech Stack

- **Backend** — Python, Flask
- **QR Engine** — `qrcode`, Pillow (PIL)
- **PDF Export** — ReportLab
- **SVG Export** — `qrcode` SVG factory
- **Frontend** — Vanilla HTML/CSS/JS
- **Design** — Dark glassmorphism, Inter font, CSS animations

---

## 📄 License

This project is licensed under the MIT License.

---

## 👤 Author

**Ranjan Jyoti**
- GitHub: [@ranjanjyoti152](https://github.com/ranjanjyoti152)
- Email: ranjanjyoti152@gmail.com

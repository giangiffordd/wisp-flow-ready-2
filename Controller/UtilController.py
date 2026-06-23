import os
import base64
import io as _io

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

# Update per tunnel/dev session — set via EXPO_URL env var, or edit the
# fallback below directly when starting a new Expo tunnel.
EXPO_URL: str = os.environ.get("EXPO_URL", "exp://localhost:8081")


@router.get("/open", response_class=HTMLResponse)
async def open_in_expo() -> str:
    import qrcode
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(EXPO_URL)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    buf = _io.BytesIO()
    qr_img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Open WISP-FLOW</title>
  <style>
    body {{ font-family: -apple-system, sans-serif; background: #0a0a0a; color: #fff;
           display: flex; flex-direction: column; align-items: center;
           justify-content: center; min-height: 100vh; margin: 0; text-align: center; padding: 2rem; box-sizing: border-box; }}
    h1 {{ font-size: 1.4rem; margin-bottom: 0.3rem; }}
    p  {{ color: #888; font-size: 0.85rem; margin-bottom: 1.2rem; }}
    img {{ border-radius: 12px; width: 220px; height: 220px; }}
    a  {{ background: #4f46e5; color: #fff; padding: 0.9rem 2rem; border-radius: 12px;
          text-decoration: none; font-size: 1rem; font-weight: 600; display: inline-block; margin-top: 1.2rem; }}
    .url {{ color: #555; font-size: 0.75rem; margin-top: 1rem; }}
  </style>
</head>
<body>
  <h1>WISP-FLOW AI</h1>
  <p>Scan with Expo Go — or tap the button below</p>
  <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
  <br>
  <a href="{EXPO_URL}">Open in Expo Go</a>
  <div class="url">{EXPO_URL}</div>
</body>
</html>"""

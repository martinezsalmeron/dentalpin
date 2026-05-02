#!/usr/bin/env bash
# Seed sample clinical photos for the issue #55 photo gallery.
#
# Generates synthetic JPEGs (different colors per category) inside the
# backend container, then uploads them through the public API so all the
# event handlers, thumbnails and EXIF code paths fire exactly like a
# real upload would. Idempotent-ish: re-running just adds more photos.

set -euo pipefail

API="${API:-http://localhost:8000}"
EMAIL="${EMAIL:-admin@demo.clinic}"
PASSWORD="${PASSWORD:-demo1234}"

echo "============================================================"
echo "DentalPin Demo Photo Seeder (issue #55)"
echo "============================================================"

# 1. Login -----------------------------------------------------------------
TOKEN=$(curl -sf -X POST "$API/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=$PASSWORD" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")
echo "[ok] logged in"

# 2. Pick the first 3 patients --------------------------------------------
PATIENTS=$(curl -sf -H "Authorization: Bearer $TOKEN" \
  "$API/api/v1/patients?page_size=3" \
  | python3 -c "import json,sys; print(' '.join(p['id'] for p in json.load(sys.stdin)['data']))")
echo "[ok] target patients: $PATIENTS"

# 3. Generate one synthetic JPEG per (color, label) combo inside the
#    backend container, then docker cp them out.
docker compose exec -T backend python <<'PY'
from PIL import Image, ImageDraw, ImageFont
import io, os

os.makedirs("/tmp/seed_photos", exist_ok=True)

# (filename, RGB color, caption text)
samples = [
    ("intra_frontal.jpg",      (220, 200, 180), "Intraoral frontal"),
    ("intra_lat_left.jpg",     (210, 195, 175), "Intraoral lateral L"),
    ("intra_lat_right.jpg",    (215, 198, 178), "Intraoral lateral R"),
    ("intra_occ_upper.jpg",    (225, 205, 180), "Occlusal superior"),
    ("intra_occ_lower.jpg",    (220, 200, 175), "Occlusal inferior"),
    ("extra_smile.jpg",        (240, 215, 200), "Smile"),
    ("extra_profile_left.jpg", (235, 210, 195), "Profile L"),
    ("xray_panoramic.jpg",     ( 30,  30,  30), "Panoramic X-ray"),
    ("xray_periapical.jpg",    ( 40,  40,  40), "Periapical X-ray"),
    ("clinical_before.jpg",    (200, 180, 160), "BEFORE"),
    ("clinical_after.jpg",     (210, 190, 170), "AFTER"),
]

for filename, color, caption in samples:
    img = Image.new("RGB", (800, 600), color=color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48
        )
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), caption, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((800 - w) / 2, (600 - h) / 2), caption,
              fill=(255, 255, 255), font=font)
    img.save(f"/tmp/seed_photos/{filename}", "JPEG", quality=85)

print(f"[ok] generated {len(samples)} synthetic JPEGs")
PY

CONTAINER_ID=$(docker compose ps -q backend)
docker cp "$CONTAINER_ID:/tmp/seed_photos" /tmp/seed_photos
echo "[ok] copied images to host"

# 4. Per-photo upload definitions: (file, kind, category, subtype, title)
declare -a PHOTOS=(
  "intra_frontal.jpg|photo|intraoral|frontal|Frontal intraoral"
  "intra_lat_left.jpg|photo|intraoral|lateral_left|Lateral izquierda"
  "intra_lat_right.jpg|photo|intraoral|lateral_right|Lateral derecha"
  "intra_occ_upper.jpg|photo|intraoral|occlusal_upper|Oclusal superior"
  "intra_occ_lower.jpg|photo|intraoral|occlusal_lower|Oclusal inferior"
  "extra_smile.jpg|photo|extraoral|smile|Sonrisa"
  "extra_profile_left.jpg|photo|extraoral|profile_left|Perfil izquierdo"
  "xray_panoramic.jpg|xray|xray|panoramic|Radiografía panorámica"
  "xray_periapical.jpg|xray|xray|periapical|Periapical 26"
  "clinical_before.jpg|photo|clinical|before|Antes — restauración 26"
  "clinical_after.jpg|photo|clinical|after|Después — restauración 26"
)

# 5. Upload + remember before/after ids per patient for pairing -----------
upload_one() {
  local patient="$1" file="$2" kind="$3" cat="$4" sub="$5" title="$6"
  curl -sf -X POST "$API/api/v1/media/patients/$patient/photos" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@/tmp/seed_photos/$file" \
    -F "title=$title" \
    -F "media_kind=$kind" \
    -F "media_category=$cat" \
    -F "media_subtype=$sub" \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['id'])"
}

for PATIENT in $PATIENTS; do
  echo ""
  echo "→ patient $PATIENT"
  BEFORE_ID=""; AFTER_ID=""
  for entry in "${PHOTOS[@]}"; do
    IFS='|' read -r FILE KIND CAT SUB TITLE <<< "$entry"
    DOC_ID=$(upload_one "$PATIENT" "$FILE" "$KIND" "$CAT" "$SUB" "$TITLE")
    echo "  + $TITLE → $DOC_ID"
    [[ "$SUB" == "before" ]] && BEFORE_ID="$DOC_ID"
    [[ "$SUB" == "after" ]]  && AFTER_ID="$DOC_ID"
  done
  if [[ -n "$BEFORE_ID" && -n "$AFTER_ID" ]]; then
    curl -sf -X POST \
      "$API/api/v1/media/documents/$BEFORE_ID/pair/$AFTER_ID" \
      -H "Authorization: Bearer $TOKEN" >/dev/null
    echo "  ↔ paired $BEFORE_ID ↔ $AFTER_ID"
  fi
done

echo ""
echo "============================================================"
echo "Done. Open http://localhost:3000 → patient → tab Galería"
echo "============================================================"

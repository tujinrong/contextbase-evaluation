"""Read-only validation of original JPEGs and the portable evidence HTML."""
import base64
import hashlib
import io
import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image

run = Path(__file__).resolve().parents[2] / "test-evidence" / "20261012-evidence-01"
output = Path(__file__).with_name("evidence-decode-verification.json")
if output.exists():
    raise SystemExit("Refusing to overwrite existing verification")
integrity = json.loads((run / "capture-integrity.json").read_text(encoding="utf-8"))
expected = {row["sha256"] for row in integrity["captures"]}


class Gallery(HTMLParser):
    def __init__(self):
        super().__init__()
        self.embedded = []

    def handle_starttag(self, tag, attrs):
        if tag != "img":
            return
        attrs = dict(attrs)
        source = attrs["src"]
        assert source.startswith("data:image/jpeg;base64,"), source[:40]
        self.embedded.append(base64.b64decode(source.split(",", 1)[1], validate=True))


gallery = Gallery()
gallery.feed((run / "test-evidence.html").read_text(encoding="utf-8"))
assert len(gallery.embedded) == integrity["counts"]["displayedImages"]
assert {hashlib.sha256(data).hexdigest() for data in gallery.embedded} == expected
records = []
for row in integrity["captures"]:
    data = (run / row["file"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == row["sha256"]
    with Image.open(io.BytesIO(data)) as image:
        assert image.format == "JPEG"
        image.load()
        assert image.size == (row["width"], row["height"])
    records.append({"file": row["file"], "sha256": row["sha256"], "decoded": True})
result = {
    "projectId": "test-project1", "runId": "20261012-evidence-01",
    "verifiedAt": datetime.now(timezone.utc).isoformat(),
    "status": "PASS", "decodedImages": len(records),
    "embeddedImages": len(gallery.embedded), "uniqueEmbeddedHashes": len(expected),
    "allEmbeddedBytesMatchOriginals": True, "originalBytesModified": False,
    "functionalSuccessInferred": False, "records": records,
}
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: value for key, value in result.items() if key != "records"}, ensure_ascii=False))

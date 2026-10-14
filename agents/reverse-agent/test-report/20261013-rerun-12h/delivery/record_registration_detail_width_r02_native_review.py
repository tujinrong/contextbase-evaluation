"""Persist already completed delivery_tools native views; no workbook authoring."""
from pathlib import Path
import copy
import hashlib
import json
from datetime import datetime, timezone

REPO = Path(r"D:\開発\contextbase-evaluation")
DEL = REPO / "agents/reverse-agent/test-report/20261013-rerun-12h/delivery"

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    from PIL import Image, ImageChops
    old_path = DEL / "registration-detail-excel-bitmap-r19-r01-actual-native-review.json"
    old = read(old_path)
    prior_css_path = DEL / "registration-detail-columns-probe-r03-actual-native-review.json"
    prior_css = read(prior_css_path)
    inv_path = DEL / "excel-bitmap-registration-detail-r19-r02-widthonly-tiles/inventory.json"
    assert sha(inv_path) == "2915e70b3814e38e5067b725f6af3596654f874a113b3394ead234a68e929b4a"
    inv = read(inv_path)
    doc = inv["documents"][0]
    assert doc["markdownSha256"] == "ecc68152d691076da8cc95c49387928d9e4f89d0f52aaaa5859708b547474cbd"
    assert doc["xlsxSha256"] == "dfd82ced097f7b1d336dc1cd752d9d8d89d2d0c76cdcaf3ad990cdcf68bd7986"
    assert len(doc["captures"]) == 114 and doc["originalPreviewCount"] == 60
    result_path = DEL / "excel-bitmap-registration-detail-r19-r02-widthonly/result.json"
    result = read(result_path)
    plan_path = Path(result["plan"])
    plan = read(plan_path)
    assert result["readOnly"] and not result["saved"] and not result["visible"]
    assert result["updateLinks"] == 0 and result["macrosDisabled"]
    assert result["workbookBytesUnchanged"] and result["planBytesUnchanged"]
    assert not result["cellsOrFormatsChanged"] and not result["pageSetupChanged"]
    assert len(result["cells"]) == 1323
    for expected, actual in zip(plan["cells"], result["cells"], strict=True):
        assert (expected["sheet"], expected["cell"]) == (actual["sheet"], actual["cell"])
        value = expected["value"]
        assert actual["value2"] == value or (value == "" and actual["value2"] is None)
    delta_path = DEL / "registration-detail-xlsx-r19-r02-widthonly-xml-delta.json"
    delta = read(delta_path)
    assert sha(delta_path) == "5ae47aee073dcfcd99b29daa819fcee9f85bb05a9fb426144e1084a81d100a45"
    assert delta["allLiteralsBlanksRowsMergeStylesTablesImagesOrderUnchanged"]
    assert delta["formulaCount"] == 0 and delta["previewRangeOrderUnchanged"]
    expected_pins = {}
    def add(raw, expected):
        path = Path(raw)
        if not path.is_absolute():
            path = REPO / path
        key = str(path)
        assert key not in expected_pins or expected_pins[key] == expected
        expected_pins[key] = expected
    for mapping in (old["afterHashes"], prior_css["afterHashes"], inv["sourceBindings"]):
        for raw, expected in mapping.items():
            add(raw, expected)
    for path in (old_path, prior_css_path, inv_path, result_path, plan_path, delta_path,
                 DEL / "model-assisted-registration-detail-r19-r02-widthonly.json",
                 DEL / "registration-detail-artifact-r19-r01-partial-native-hold.json"):
        add(str(path), sha(path))
    views = []
    for index, capture in enumerate(doc["captures"]):
        add(capture["path"], capture["sha256"])
        add(capture["originalPath"], capture["originalSha256"])
        region = capture["sourceRectangle"]
        with Image.open(capture["originalPath"]) as original, Image.open(capture["path"]) as tile:
            expected = original.convert("RGBA").crop((region["x"], region["y"],
                region["x"] + region["width"], region["y"] + region["height"]))
            actual_rgba = tile.convert("RGBA")
            assert actual_rgba.size == expected.size
            assert all(channel.getbbox() is None for channel in ImageChops.difference(expected, actual_rgba).split())
        item = copy.deepcopy(capture)
        item.update(actuallyReviewed=True, captureIndexZeroBased=index,
                    actuallyViewedBy="delivery_tools", view="view_image original pixels")
        views.append(item)
    after = {raw: sha(Path(raw)) for raw in expected_pins}
    assert after == expected_pins
    report = {
        "schema": "reverse-agent-owned-excel-actual-native-review/1",
        "createdUtc": datetime.now(timezone.utc).isoformat(),
        "scope": "OWNED_READ_ONLY_EXCEL_BITMAP_GEOMETRY_ONLY",
        "referenceMode": "training-assisted",
        "documentId": doc["documentId"],
        "canonicalDocumentPath": doc["canonicalDocumentPath"],
        "markdownSha256": doc["markdownSha256"],
        "xlsx": doc["xlsx"], "xlsxSha256": doc["xlsxSha256"],
        "inventory": str(inv_path), "inventorySha256": sha(inv_path),
        "actualOriginalPreviews": 60, "actualOriginalTiles": 114,
        "actuallyViewedZeroBasedIndices": list(range(114)), "unseen": [], "views": views,
        "status": "PASS_WHOLE_IDENTIFIERS_WITH_CITATION_WRAP_NOTES",
        "blocking": [],
        "resolved": [{"sheet": "イベント仕様", "cell": "U200", "literal": "EV-REG-001",
            "actualPreview": 18, "actualTileIndicesZeroBased": [35, 36],
            "observation": "Whole identifier remains on one visible row in the fresh Excel bitmap."}],
        "literalDisplay": "All copied cell values exact; no lost, hidden or cropped literal values observed.",
        "internalAsciiNumericWrap": [],
        "projectionDelta": {"onlyColumn": "イベント仕様!U", "beforeWidth": 2,
            "afterWidth": 12, "xmlDelta": str(delta_path), "xmlDeltaSha256": sha(delta_path)},
        "notes": [
            "All 60 ranges and 114 exact-RGBA tiles were actually viewed at original scale by delivery_tools.",
            "All columns and all 21 source graph / 3 static layout images were reviewed; connectors continue across copied ranges.",
            "Source citation line ranges and paths can naturally wrap at authored hyphens or slashes (for example 125-/125, 158-/159). They remain fully visible; no internal digit or identifier fragment was observed.",
            "Original-size ranges have white space and consecutive vertical graph continuations. All regions are present with complete pixel coverage.",
            "CopyPicture temporarily wrote the clipboard. Prior clipboard content was neither read nor output; only the owned copied sequence was read.",
            "Static derived workbook display only. ASP.NET application and business operations were not executed."
        ],
        "exactNonemptyStrings": sum(c["value"] != "" for c in plan["cells"]),
        "blankEquivalence": sum(c["value"] == "" for c in plan["cells"]),
        "excelVersion": result["excelVersion"], "excelBuild": result["excelBuild"],
        "ownedReadOnly": True, "saved": False, "pageSetupChanged": False,
        "cellsOrFormatsChanged": False, "allPinnedBytesUnchanged": True,
        "beforeHashes": expected_pins, "afterHashes": after,
        "historicalHold": str(old_path), "historicalHoldSha256": sha(old_path),
        "historicalInventoryModified": False, "historicalArtifactHoldModified": False,
        "businessContentAuthored": False, "semanticApproval": False,
        "formalQualityApproval": False, "stateProjectionIncluded": False,
        "wholeDocumentApproval": False, "published": False, "originalApplicationExecuted": False
    }
    output = DEL / "registration-detail-excel-width-r02-actual-native-review.json"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(output), "sha256": sha(output), "status": report["status"],
                      "pins": len(after), "actualTiles": 114, "blocking": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()

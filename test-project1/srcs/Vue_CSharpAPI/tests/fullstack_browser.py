"""Verify the built Vue assets against the real local API and immutable fixture service."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="https://localhost:7444")
parser.add_argument("--output", default=str(Path(__file__).resolve().parents[1] / "build/test-results/fullstack"))
args = parser.parse_args()
assert urlparse(args.url).hostname in {"localhost", "127.0.0.1"}
output = Path(args.output).resolve()
output.mkdir(parents=True, exist_ok=True)
checks, errors, policies = [], [], []

def check(value, name):
    assert value, name
    checks.append(name)

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    context = browser.new_context(ignore_https_errors=True, viewport={"width": 1280, "height": 650})
    context.add_init_script("window.policyErrors=[];addEventListener('securitypolicyviolation',e=>window.policyErrors.push(e.violatedDirective))")
    page = context.new_page()
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(args.url + "/__evidence/login?role=Administrator")
    expect(page.get_by_role("button", name="新規登録", exact=True)).to_be_enabled()
    with page.expect_response(lambda response: response.url.endswith("/api/students/search")) as response:
        page.get_by_role("button", name="検索", exact=True).click()
    data = response.value.json()
    check(response.value.status == 200, "built Vue reaches real HTTPS search API")
    check(data["formatVersion"] == "search-compact-1", "format version delivered to built client")
    check(set(data["criteria"]) == {"studentNo", "name", "classId", "statusCodes"}, "real API raw criteria four keys")
    check(data["items"][0]["studentId"] == "9007199254740993", "real bigint precision retained")
    check(not set(data["items"][0]).intersection({"addressDisplay", "phoneNumber", "updatedAt", "rowVersion"}), "real API reduced DTO")
    expect(page.locator(".student-grid tbody tr")).to_have_count(2)
    check(page.locator(".student-grid th").count() == 7, "built list has seven columns")
    page.screenshot(path=str(output / "built-search.png"), full_page=True)
    page.get_by_role("button", name="編集", exact=True).first.click()
    expect(page.locator("#REG-024")).to_be_visible()
    check(page.locator("#REG-002").input_value() == "TEST2026-0001", "real API edit loads source fixture")
    check(page.locator("#REG-002").get_attribute("readonly") is not None, "built edit keeps student number readonly")
    check(page.locator("#REG-003").input_value() == "テスト 太郎", "edit raw name preserved")
    page.screenshot(path=str(output / "built-editor.png"), full_page=True)
    check(page.evaluate("document.documentElement.scrollHeight") <= 650, "built editor fits 1280x650")
    page.get_by_role("button", name="論理削除", exact=True).click()
    expect(page.locator("dialog[open]")).to_be_visible()
    check(page.locator("dialog [data-cancel]").evaluate("e=>e===document.activeElement"), "built delete defaults to cancel")
    page.keyboard.press("Escape")
    expect(page.locator("dialog[open]")).to_have_count(0)
    page.locator("#REG-009").fill("原入力保持テスト")
    with page.expect_response(lambda response: "/api/students/9007199254740993" in response.url and response.request.method == "PUT") as failed:
        page.get_by_role("button", name="更新", exact=True).click()
    check(failed.value.status == 403, "immutable fixture blocks writes through real API")
    expect(page.locator("#REG-009")).to_have_value("原入力保持テスト")
    page.get_by_role("button", name="検索へ戻る", exact=True).click()
    expect(page.locator("dialog[open]")).to_contain_text("変更破棄")
    check(True, "real API failure retains raw and dirty guard")
    page.keyboard.press("Escape")
    check(errors == [], "built bundle has no runtime errors")
    check(page.evaluate("window.policyErrors") == [], "built bundle satisfies production CSP")
    browser_version = browser.version
    browser.close()

(output / "results.json").write_text(json.dumps({"status": "passed", "checks": checks, "count": len(checks),
    "browserVersion": browser_version, "scope": "built Vue + real HTTPS API + immutable service; no SQL"},
    ensure_ascii=False, indent=2), encoding="utf-8")
print(f"PASS built Vue/API browser: {len(checks)} checks")

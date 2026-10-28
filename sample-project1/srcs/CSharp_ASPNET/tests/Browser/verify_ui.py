"""Exercise production Razor/JS against the loopback, immutable --ui-scenarios host.

Requires Python Playwright + Chromium. No production credentials or database are used.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, expect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://localhost:7443")
    parser.add_argument("--output", default=str(Path(__file__).resolve().parents[2] / "build/test-results/browser"))
    args = parser.parse_args()
    if urlparse(args.base_url).hostname not in {"localhost", "127.0.0.1"}:
        raise ValueError("Only the local test host is allowed")
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    checks, measurements, errors = [], [], []

    def check(condition, name):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        browser_version = browser.version
        context = browser.new_context(ignore_https_errors=True, viewport={"width": 1366, "height": 650})
        context.add_init_script("window.uiPolicyErrors=[];addEventListener('securitypolicyviolation',e=>window.uiPolicyErrors.push(e.violatedDirective))")
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))

        def login(role="Staff"):
            response = page.goto(args.base_url + "/__evidence/login?role=" + role)
            check(response.status == 200, "fixture login " + role)
            expect(page.locator(".student-search")).to_be_visible()

        def geometry(kind, width, screenshot=True):
            result = page.evaluate("""() => ({
                width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth,
                scrollHeight:document.documentElement.scrollHeight,
                last:document.querySelector('.savebar,.resultfoot')?.getBoundingClientRect().bottom,
                dialogs:document.querySelectorAll('dialog[open]').length,
                grid:document.querySelector('.gridwrap') ? {
                    client:document.querySelector('.gridwrap').clientHeight,
                    scroll:document.querySelector('.gridwrap').scrollHeight} : null,
                policy:window.uiPolicyErrors
            })""")
            measurements.append({"state": kind, **result})
            check(result["scrollWidth"] <= width, kind + " no outer horizontal scroll " + str(width))
            check(result["scrollHeight"] <= 650, kind + " no outer vertical scroll " + str(width))
            check(result["last"] <= 650, kind + " actions fit " + str(width))
            check(result["policy"] == [], kind + " CSP satisfied")
            if screenshot:
                page.screenshot(path=str(output / f"{kind}-{width}.png"), full_page=True)
            return result

        login()
        page.locator("#SRC-002").fill("初期入力")
        expect(page.locator("[data-criteria-status]")).to_contain_text("条件を指定して検索")
        page.locator("#SRC-002").fill("")
        names = page.locator('[data-search-form] [name^="Criteria."]').evaluate_all("els=>[...new Set(els.map(e=>e.name))].sort()")
        check(names == ["Criteria.ClassId", "Criteria.Name", "Criteria.StatusCodes", "Criteria.StudentNo"], "exactly four search criteria")
        check(page.locator(".student-grid thead th").count() == 7, "seven list columns")
        for checkbox in page.locator('[name="Criteria.StatusCodes"]').all():
            checkbox.uncheck()
        page.get_by_role("button", name="検索", exact=True).click()
        expect(page.locator(".student-grid tbody tr")).to_have_count(20)
        for width in [1366, 1280]:
            page.set_viewport_size({"width": width, "height": 650})
            result = geometry("search", width)
            check(result["grid"]["scroll"] > result["grid"]["client"], "20 rows scroll inside grid " + str(width))
        requests = []
        page.on("request", lambda request: requests.append(request.url))
        before = len(requests)
        page.locator("#SRC-002").fill("未反映")
        expect(page.locator("[data-criteria-status]")).to_contain_text("未反映")
        check(len(requests) == before, "criteria changes cause no request")
        page.locator("#SRC-002").fill("")
        expect(page.locator("[data-criteria-status]")).not_to_contain_text("未反映")
        checks.append("reverted search input clears pending marker")
        page.locator("#SRC-002").fill("未反映")
        page.get_by_role("button", name="次へ", exact=True).click()
        expect(page.locator(".student-grid tbody tr")).to_have_count(4)
        check("検索結果 24" in page.locator('[data-field-id="SRC-017"]').inner_text(), "page uses last applied criteria")
        page.locator("#SRC-002").fill("存在しない")
        page.get_by_role("button", name="検索", exact=True).click()
        expect(page.locator(".student-grid tbody tr")).to_have_count(0)
        expect(page.locator('[data-field-id="SRC-017"]')).to_contain_text("0件")
        page.locator("#SRC-002").fill("あいうえおかきくけ")
        with page.expect_response(lambda response: response.url.endswith("/students/search")) as rejected:
            page.get_by_role("button", name="検索", exact=True).click()
        check(rejected.value.status == 422, "search overlength rejected")
        check(page.locator("#SRC-002").input_value() == "あいうえおかきくけ", "invalid raw name preserved")
        page.get_by_role("button", name="クリア", exact=True).click()
        expect(page.locator('[data-field-id="SRC-017"]')).to_contain_text("未検索")
        page.get_by_role("button", name="検索", exact=True).click()
        page.locator(".row-action").first.click()
        expect(page.locator(".student-editor")).to_be_visible()
        for width in [1366, 1280]:
            page.set_viewport_size({"width": width, "height": 650})
            geometry("editor", width)
        check(page.locator("#REG-002").get_attribute("readonly") is not None, "existing student number readonly")
        check(page.locator("dialog[open]").count() == 0, "normal editor has no confirmation dialog")
        original = page.locator("#REG-009").input_value()
        page.locator("#REG-009").fill("変更した住所")
        page.locator("#REG-030").click()
        expect(page.locator("#discard-dialog")).to_be_visible()
        check(page.locator("#discard-dialog [data-dialog-cancel]").evaluate("e=>e===document.activeElement"), "discard defaults to cancel")
        page.keyboard.press("Escape")
        expect(page.locator("#discard-dialog")).not_to_be_visible()
        check(page.locator("#REG-030").evaluate("e=>e===document.activeElement"), "discard cancel restores trigger focus")
        check(page.locator("#REG-009").input_value() == "変更した住所", "discard cancellation retains raw input")
        page.locator("#REG-009").fill(original)
        page.locator("#REG-030").click()
        expect(page.locator(".student-search")).to_be_visible()
        check(page.locator("dialog[open]").count() == 0, "reverted value no longer dirty")

        page.locator(".row-action").first.click()
        page.locator("#REG-009").fill("重複確認テスト")
        page.locator("#REG-027").click()
        expect(page.locator('#REG-032[open]')).to_be_visible()
        check(page.locator("dialog[open]").count() == 1, "duplicate is only open dialog")
        check(page.locator("#REG-034").evaluate("e=>e===document.activeElement"), "duplicate defaults to cancel")
        check(page.locator("#REG-032 tbody tr").count() <= 20, "duplicate candidate display limit")
        page.screenshot(path=str(output / "duplicate-1280.png"), full_page=True)
        page.locator("#REG-034").click()
        expect(page.locator("#REG-032")).not_to_be_visible()
        page.locator("#REG-027").click()
        expect(page.locator('#REG-032[open]')).to_be_visible()
        page.locator("#duplicate-reason").fill("同姓同名の別人と確認しました。")
        with page.expect_response(lambda response: response.url.endswith("/update")) as failed_save:
            page.locator("#REG-033").click()
        check(failed_save.value.status == 422, "synthetic confirmed save fails without writing")
        check(page.locator("#REG-009").input_value() == "重複確認テスト", "failed save retains raw input")
        page.locator("#REG-030").click()
        expect(page.locator("#discard-dialog")).to_be_visible()
        page.locator("[data-confirm-discard]").click()
        expect(page.locator(".student-search")).to_be_visible()

        login("Administrator")
        page.get_by_role("button", name="検索", exact=True).click()
        page.locator(".row-action").first.click()
        page.locator("#REG-031").click()
        expect(page.locator("#delete-dialog")).to_be_visible()
        check(page.locator("#delete-dialog [data-dialog-cancel]").evaluate("e=>e===document.activeElement"), "delete defaults to cancel")
        page.screenshot(path=str(output / "delete-1280.png"), full_page=True)
        page.keyboard.press("Escape")
        check(page.locator("#REG-031").evaluate("e=>e===document.activeElement"), "delete cancel restores focus")

        login("Viewer")
        check(page.locator('[data-field-id="SRC-015"]').count() == 0, "viewer has no new action")
        page.get_by_role("button", name="検索", exact=True).click()
        expect(page.locator(".row-action").first).to_have_text("参照")
        page.locator(".row-action").first.click()
        check(not page.locator("#REG-003").is_editable() and page.locator("#REG-027").is_disabled(), "viewer editor read only")
        check(not page.locator("#REG-031").is_visible(), "viewer has no delete action")
        page.locator("#REG-009").focus()
        check(page.locator("#REG-009").evaluate("e=>e===document.activeElement"), "viewer can focus read only text for full value")
        page.screenshot(path=str(output / "viewer-1280.png"), full_page=True)

        login()
        page.get_by_role("link", name="新規登録", exact=True).click()
        check(page.locator('[name^="Input.BirthDateInput."]').evaluate_all("es=>es.every(e=>e.value==='')"), "new birth date four raw fields empty")
        check(page.locator("#REG-013").input_value() == "", "new admission date empty")
        page.set_viewport_size({"width": 600, "height": 650})
        check(page.evaluate("document.documentElement.scrollWidth") <= 600, "narrow editor has no horizontal clipping")
        page.locator("#REG-030").scroll_into_view_if_needed()
        check(page.locator("#REG-030").is_visible(), "narrow editor back action reachable")
        page.screenshot(path=str(output / "new-narrow.png"), full_page=True)
        page.set_viewport_size({"width": 640, "height": 325})
        check(page.evaluate("document.documentElement.scrollWidth") <= 640, "200 percent equivalent viewport reflows")
        page.locator("#REG-030").scroll_into_view_if_needed()
        check(page.locator("#REG-030").is_visible(), "200 percent equivalent actions reachable")
        check(errors == [], "no JavaScript runtime errors")
        browser.close()

    result = {"status": "passed", "browser": "Playwright Chromium", "browserVersion": browser_version,
              "checks": checks, "count": len(checks), "measurements": measurements,
              "scope": "production Razor/JS with synthetic immutable service; no SQL or deployment"}
    (output / "browser-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PASS browser UI: {len(checks)} checks")


if __name__ == "__main__":
    main()

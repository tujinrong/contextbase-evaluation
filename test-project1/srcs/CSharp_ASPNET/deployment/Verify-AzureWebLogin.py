"""Exercise the real Azure login in Chromium without recording credentials or network bodies."""
import json
import os
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

BASE = 'https://app-contextbase-student-8a14b4.azurewebsites.net'
output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=True)
password = os.environ['CB_WEB_LOGIN_PASSWORD']
checks = []
stage = 'browser startup'
try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = context.new_page()
        page_errors = []
        page.on('pageerror', lambda error: page_errors.append(type(error).__name__))
        page.set_default_timeout(30000)
        stage = 'anonymous redirect and login form'
        response = page.goto(BASE + '/students', wait_until='networkidle', timeout=120000)
        assert response.status == 200 and page.url == BASE + '/login'
        assert page.locator('input[name="Username"]').get_attribute('autocomplete') == 'username'
        assert page.locator('input[name="Password"]').get_attribute('autocomplete') == 'current-password'
        assert page.locator('input[name="Password"]').get_attribute('type') == 'password'
        page.screenshot(path=str(output / 'login-desktop.png'), full_page=True)
        checks.append('anonymous students redirects to rendered login; labeled password form and autocomplete available')
        page.set_viewport_size({'width': 375, 'height': 812})
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        page.screenshot(path=str(output / 'login-mobile.png'), full_page=True)
        page.set_viewport_size({'width': 1280, 'height': 900})
        checks.append('login form fits 375px mobile viewport')
        stage = 'CSRF rejection'
        rejected = context.request.post(BASE + '/login', form={'Username': 'admin', 'Password': 'invalid-csrf-test'})
        assert rejected.status == 400
        checks.append('login POST without CSRF token rejected with 400')
        stage = 'incorrect password'
        page.locator('input[name="Username"]').fill('admin')
        page.locator('input[name="Password"]').fill('incorrect-test-password')
        with page.expect_response(lambda result: result.request.method == 'POST' and result.url == BASE + '/login') as attempted:
            page.get_by_role('button', name='ログイン', exact=True).click()
        assert attempted.value.status == 401
        assert page.locator('input[name="Password"]').input_value() == ''
        assert page.get_by_role('alert').is_visible()
        page.screenshot(path=str(output / 'login-error.png'), full_page=True)
        checks.append('incorrect password rejected; accessible generic error and cleared password')
        stage = 'successful login and database-backed screen'
        page.locator('input[name="Username"]').fill('admin')
        page.locator('input[name="Password"]').fill(password)
        page.get_by_role('button', name='ログイン', exact=True).click()
        page.wait_for_url(BASE + '/students', wait_until='networkidle', timeout=120000)
        assert page.get_by_role('heading', name='学生検索', exact=True).is_visible()
        assert page.locator('#SRC-009 option').count() == 48
        auth_cookie = next(cookie for cookie in context.cookies() if cookie['name'] == '__Host-StudentManagement')
        assert auth_cookie['secure'] and auth_cookie['httpOnly'] and auth_cookie['sameSite'] == 'Strict'
        page.screenshot(path=str(output / 'students-after-login.png'), full_page=True)
        checks.append('successful login opens actual student search with 47 prefecture codes; Secure HttpOnly Strict cookie')
        stage = 'actual database query'
        with page.expect_response(lambda result: result.request.method == 'POST' and result.url == BASE + '/students/search') as searched:
            page.get_by_role('button', name='検索', exact=True).click()
        assert searched.value.status == 200
        assert page.get_by_text('該当する学生はありません。', exact=True).is_visible()
        page.screenshot(path=str(output / 'students-empty-search.png'), full_page=True)
        checks.append('authenticated search executes successfully against Azure SQL and returns no students')
        stage = 'logout CSRF and sign out'
        assert context.request.post(BASE + '/logout').status == 400
        page.get_by_role('button', name='ログアウト', exact=True).click()
        page.wait_for_url(BASE + '/login', wait_until='networkidle')
        page.goto(BASE + '/students', wait_until='networkidle')
        assert page.url == BASE + '/login'
        assert not any(cookie['name'] == '__Host-StudentManagement' for cookie in context.cookies())
        checks.append('logout requires CSRF, removes login cookie, and protects students again')
        assert context.request.post(BASE + '/_evaluation/session').status == 404
        checks.append('Production evaluation login remains disabled')
        assert not page_errors, 'Browser page errors occurred.'
        checks.append('no browser JavaScript exceptions')
        browser.close()
    result = {'status': 'passed', 'checks': checks, 'businessWrites': False}
    (output / 'browser-login-verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True))
except Exception as error:
    # Playwright call traces may contain fill arguments; report only stage and error class.
    failure = {'status': 'failed', 'stage': stage, 'errorType': type(error).__name__, 'completedChecks': checks}
    (output / 'browser-login-verification.json').write_text(json.dumps(failure, indent=2), encoding='utf-8')
    print(json.dumps(failure))
    raise SystemExit(1)

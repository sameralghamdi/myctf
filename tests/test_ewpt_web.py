"""Browser/terminal integration, spoiler-free presentation and instance boundaries."""
import re
from urllib.parse import urlencode

import pytest

from app import models
from app.labs.ewpt_pages import WEB_NUMBERS
from conftest import auth_headers, register, start_lab, submit_flag
from test_ewpt import SLUGS, FLAG, sh


def web(client, token, iid, path='/', method='GET', data='', headers=None):
    response = client.post(f'/labs/{iid}/web/request', headers=auth_headers(token),
                           json={'path': path, 'method': method, 'data': data, 'headers': headers or {}})
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()


@pytest.mark.parametrize('number', sorted(WEB_NUMBERS))
def test_browser_target_available_without_pre_solve_flag(client, user, number):
    token, slug = user['token'], 'ewpt-' + SLUGS[number]
    detail = client.get('/api/challenges/' + slug, headers=auth_headers(token)).get_json()
    assert detail['has_web_ui'] and detail['is_shell']
    assert detail['default_lab_view'] in ('target', 'terminal')
    iid = start_lab(client, token, slug)
    response = client.get(f'/labs/{iid}/', headers=auth_headers(token))
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Target path' in html and 'Source' in html and 'Headers' in html
    assert 'sandbox="allow-scripts allow-forms"' in html and 'allow-same-origin' not in html
    assert not FLAG.search(html)
    root = web(client, token, iid)
    assert root['status'] in (200, 401)
    assert not FLAG.search(root['body'])
    assert 'EWPT' not in root['body']
    assert not FLAG.search(sh(client, token, iid, 'cat README.txt'))


def test_tomcat_manager_login_source_and_shared_app_state(client, user):
    token = user['token']; slug = 'ewpt-tomcat-weak-creds'
    iid = start_lab(client, token, slug)
    landing = web(client, token, iid)
    assert 'Apache Tomcat' in landing['body'] and '/manager/html' in landing['body']
    denied = web(client, token, iid, '/manager/html')
    assert denied['status'] == 401 and 'WWW-Authenticate' in denied['headers']
    assert not FLAG.search(denied['body'])
    wrong = web(client, token, iid, '/_auth?next=/manager/html', 'POST', 'username=tomcat&password=wrong')
    assert wrong['status'] == 401 and not FLAG.search(wrong['body'])
    manager = web(client, token, iid, '/_auth?next=/manager/html', 'POST', 'username=tomcat&password=tomcat')
    assert manager['status'] == 200
    for label in ('Tomcat Web Application Manager','Applications','Deploy','Server Information'):
        assert label in manager['body']
    flag = FLAG.search(manager['body']).group()
    assert f'<!-- {flag} -->' in manager['body']
    stopped = web(client, token, iid, '/manager/html', 'POST', 'action=stop&path=%2Fexamples')
    assert stopped['status'] == 200
    shell_page = sh(client, token, iid, 'curl -u tomcat:tomcat http://target.lab.local:8080/manager/html')
    assert '/examples</td><td>None specified</td><td>Servlet and JSP Examples</td><td>false' in shell_page
    assert FLAG.search(shell_page).group() == flag
    web(client, token, iid, '/_logout')
    assert web(client, token, iid, '/manager/html')['status'] == 401
    assert submit_flag(client, token, slug, flag).get_json()['correct']


def test_browser_and_terminal_share_shop_cart(client, user):
    token = user['token']; iid = start_lab(client, token, 'ewpt-coupon-king')
    first = web(client, token, iid)
    assert 'Order summary' in first['body'] and not FLAG.search(first['body'])
    for i in range(5):
        web(client, token, iid, '/apply-coupon', 'POST', 'coupon=WELCOME10')
        sh(client, token, iid, 'curl -d coupon=WELCOME10 http://target.lab.local/apply-coupon')
    paid = web(client, token, iid, '/checkout', 'POST')
    assert paid['status'] == 200 and FLAG.search(paid['body'])


def test_browser_login_injection_and_cookie_scope(client, user):
    token = user['token']; iid = start_lab(client, token, 'ewpt-fuzz-the-login')
    denied = web(client, token, iid, '/api/login', 'POST', 'username=admin&password=wrong')
    assert denied['status'] == 401 and 'Invalid username' in denied['body']
    login = web(client, token, iid, '/api/login', 'POST', urlencode({'username': "' OR 1=1-- -", 'password': 'x'}))
    assert login['status'] == 200 and 'Set-Cookie' in login['headers']
    dashboard = web(client, token, iid, '/admin')
    assert FLAG.search(dashboard['body'])
    # Browser target cookies never become platform response cookies.
    raw = client.post(f'/labs/{iid}/web/request', headers=auth_headers(token), json={'path':'/admin'})
    assert 'Set-Cookie' not in raw.headers
    second = start_lab(client, token, 'ewpt-password-reset-step-skip')
    assert not FLAG.search(web(client, token, second, '/admin')['body'])


def test_api_docs_try_it_out_header_and_source(client, user):
    token = user['token']; iid = start_lab(client, token, 'ewpt-fastapi-docs-leak')
    docs = web(client, token, iid, '/docs')
    assert 'openapi.json' in docs['body'] and 'data-header="X-Admin"' in docs['body']
    schema = web(client, token, iid, '/openapi.json')
    assert '/api/v1/admin/flag' in schema['body']
    assert web(client, token, iid, '/api/v1/admin/flag')['status'] == 401
    success = web(client, token, iid, '/api/v1/admin/flag', headers={'X-Admin':'true'})
    assert FLAG.search(success['body'])


def test_browser_reset_step_skip(client, user):
    token = user['token']; iid = start_lab(client, token, 'ewpt-password-reset-step-skip')
    assert 'Forgot your password?' in web(client, token, iid)['body']
    normal = web(client, token, iid, '/reset/step1', 'POST', 'email=admin@lab.local')
    assert 'Verification code' in normal['body']
    assert web(client, token, iid, '/reset/step2', 'POST', 'token=wrong')['status'] == 403
    assert 'Choose a new password' in web(client, token, iid, '/reset/step3')['body']
    updated = web(client, token, iid, '/reset/step3', 'POST', 'email=admin@lab.local&password=NewPass123!')
    assert 'Password updated' in updated['body']
    web(client, token, iid, '/api/login', 'POST', 'email=admin@lab.local&password=NewPass123!')
    assert FLAG.search(web(client, token, iid, '/admin')['body'])


def test_request_editor_supports_methods_headers_and_flag_submission(client, user):
    token = user['token']; iid = start_lab(client, token, 'ewpt-http-method-mayhem')
    assert 'PUT' in web(client, token, iid, '/uploads/', 'OPTIONS')['headers']['Allow']
    assert web(client, token, iid, '/uploads/probe.txt', 'PUT', 'hello')['status'] == 201
    flag = FLAG.search(web(client, token, iid, '/uploads/probe.txt')['body']).group()
    assert submit_flag(client, token, 'ewpt-http-method-mayhem', flag).get_json()['correct']


@pytest.mark.parametrize('payload', [
    {'path':'http://outside.example/'}, {'path':'//outside.example/'}, {'path':'/\\outside'},
    {'path':['/']}, {'method':123}, {'headers':{'X-Test':99}},
    {'headers':{'X-Test':'a\r\nInjected: header'}}, {'data':'a'*8193},
])
def test_browser_rejects_invalid_or_out_of_scope_requests(client, user, payload):
    token = user['token']; iid = start_lab(client, token, 'ewpt-tomcat-weak-creds')
    result = client.post(f'/labs/{iid}/web/request', headers=auth_headers(token), json=payload)
    assert result.status_code == 400
    assert not FLAG.search(result.get_data(as_text=True))


def test_browser_owner_isolation_reset_and_no_auth_leak(client, user):
    token = user['token']; iid = start_lab(client, token, 'ewpt-tomcat-weak-creds')
    authorized = web(client, token, iid, '/_auth?next=/manager/html', 'POST', 'username=tomcat&password=tomcat')
    old_flag = FLAG.search(authorized['body']).group()
    other = client.application.test_client(); _, other_token = register(other)
    for path, method in [('/', 'get'),('/web/request','post')]:
        result = getattr(other, method)(f'/labs/{iid}{path}', headers=auth_headers(other_token), **({'json':{'path':'/manager/html'}} if method == 'post' else {}))
        assert result.status_code == 403
    second = start_lab(other, other_token, 'ewpt-tomcat-weak-creds')
    assert web(other, other_token, second, '/manager/html')['status'] == 401
    reset = client.post(f'/api/labs/{iid}/reset', headers=auth_headers(token)).get_json()
    assert web(client, token, reset['instance_id'], '/manager/html')['status'] == 401
    assert not submit_flag(client, token, 'ewpt-tomcat-weak-creds', old_flag).get_json()['correct']


def test_neutral_briefs_public_urls_and_no_objectives_resources(client, user):
    token = user['token']; headers = auth_headers(token)
    rows = client.get('/api/challenges', headers=headers).get_json()
    assert len(rows) == 37
    for row in rows:
        assert row['public_slug'] == row['slug'] == f"case-{row['id']}"
        assert row['lab_kind'] in ('web', 'web_terminal', 'terminal')
        assert not re.search(r'(?i)\b(apache|tomcat|sqli|xss|traversal|ewpt|nginx|fastapi)\b', row['name'])
        detail = client.get('/api/challenges/' + row['public_slug'], headers=headers).get_json()
        assert not detail['objectives'] and not detail['references']
        assert not re.search(r'(?i)objective|exam topics|apache|2\.4\.49|SQL|Tomcat|nginx', detail['description'])
    target = next(row for row in rows if row['name'] == 'Operations Center')
    old_link = client.get('/challenges/ewpt-tomcat-weak-creds', headers=headers)
    assert old_link.status_code == 302 and old_link.headers['Location'].endswith(target['public_slug'])
    iid = start_lab(client, token, target['public_slug'])
    page = client.get('/challenges/' + target['public_slug'], headers=headers).get_data(as_text=True)
    assert 'Target page' in page and 'Terminal' in page
    assert 'Objectives</' not in page and 'Resources</' not in page
    assert 'tomcat' not in sh(client, token, iid, 'cat README.txt').lower()


def test_dns_can_be_discovered_without_a_domain_in_the_brief(client, user):
    token = user['token']; iid = start_lab(client, token, 'ewpt-dns-enumeration')
    assert 'lumoratech.lab' not in sh(client, token, iid, 'cat README.txt')
    assert 'lumoratech.lab' in sh(client, token, iid, 'cat /etc/resolv.conf')
    assert 'ns1.lumoratech.lab' in sh(client, token, iid, 'dig @192.168.0.2 -x 192.168.0.2')
    transfer = sh(client, token, iid, 'dig @192.168.0.2 lumoratech.lab AXFR')
    assert FLAG.search(transfer)


def test_report_tools_accept_natural_answer_format(client, user):
    token = user['token']; iid = start_lab(client, token, 'ewpt-architecture-mapping-quiz')
    assert 'ascending port order' in sh(client, token, iid, 'cat engagement.txt')
    assert FLAG.search(sh(client, token, iid, 'answer nginx uvicorn tomcat apache'))


def test_lab_pages_format_money_and_explain_failed_sign_in(client, user):
    token = user['token']
    iid = start_lab(client, token, 'ewpt-coupon-king')
    web(client, token, iid, '/cart', 'POST', 'quantity=-1')
    page = web(client, token, iid, '/')['body']
    assert '$-' not in page and '−$' in page
    iid = start_lab(client, token, 'ewpt-tomcat-weak-creds')
    first = web(client, token, iid, '/manager/html')['body']
    assert 'Incorrect username or password' not in first
    web(client, token, iid, '/_auth?next=%2Fmanager%2Fhtml', 'POST', 'username=tomcat&password=nope')
    again = web(client, token, iid, '/manager/html')['body']
    assert 'Incorrect username or password' in again
    iid = start_lab(client, token, 'ewpt-fuzz-the-login')
    denied = web(client, token, iid, '/admin')
    assert denied['status'] == 401 and 'Sign in required' in denied['body']
    iid = start_lab(client, token, 'ewpt-nginx-alias-traversal')
    assert 'nginx' in web(client, token, iid, '/static/')['body'].split('<address>')[-1]

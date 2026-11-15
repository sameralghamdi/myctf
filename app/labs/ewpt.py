"""EWPT terminal targets. All protocols and files are simulated in memory.

No subprocesses, network clients, eval, or host filesystem access. Mutable target
state is captured by each scenario's program factory, never shared by players.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
import secrets
import sqlite3
from urllib.parse import parse_qs, quote, unquote, urlencode, urlsplit

from .shell_scenarios import ShellScenario

HOME = '/home/ctf'
# Number -> host, port, short label. Non-HTTP challenges still have a scope host.
LEGACY_TARGETS = {
    101: ('login.lab.local', 80, 'Fuzz the Login'),
    102: ('methods.lab.local', 80, 'HTTP Method Mayhem'),
    103: ('shop.lab.local', 80, 'Coupon King'),
    104: ('osint.lab.local', 80, 'Vendor OSINT'),
    105: ('api.lab.local', 8000, 'FastAPI Docs Leak'),
    106: ('flask.lab.local', 80, 'Stack Fingerprint'),
    107: ('cms.lab.local', 8082, 'Apache Traversal'),
    108: ('tomcat.lab.local', 8080, 'Tomcat Manager'),
    109: ('nginx.lab.local', 5000, 'Nginx Alias Traversal'),
    110: ('192.168.0.2', 53, 'DNS Enumeration'),
    111: ('ssh.lab.local', 80, 'SSH Key Leak'),
    112: ('xrdp.lab.local', 3389, 'XRDP Exposure'),
    113: ('digest.lab.local', 80, 'Digest Authentication'),
    114: ('backup.lab.local', 80, 'Backup File Leak'),
    115: ('api-fuzz.lab.local', 80, 'API Endpoint Fuzzing'),
    116: ('reset.lab.local', 80, 'Password Reset Step Skip'),
    117: ('architecture.lab.local', 5000, 'Architecture Mapping'),
    118: ('logs.lab.local', 80, 'Log Analysis'),
    119: ('sqli-fuzz.lab.local', 80, 'SQL Injection Fuzzing'),
    120: ('trace.lab.local', 80, 'HTTP TRACE Leak'),
}

CASE_NAMES = {
    101: 'Reception',
    102: 'Storage Room',
    103: 'The Last Item',
    104: 'Public Record',
    105: 'Service Desk',
    106: 'Control Room',
    107: 'Old Office',
    108: 'Operations Center',
    109: 'Side Entrance',
    110: 'Name Service',
    111: 'Remote Office',
    112: 'Workstation',
    113: 'Restricted Area',
    114: 'Archive Room',
    115: 'Service Corridor',
    116: 'Account Services',
    117: 'Site Survey',
    118: 'Night Shift',
    119: 'Supply Room',
    120: 'Return Address',
}

TARGETS = {number: ('192.168.0.2' if number == 110 else 'target.lab.local', data[1], CASE_NAMES[number])
           for number, data in LEGACY_TARGETS.items()}


@dataclass
class Request:
    url: str = ''
    method: str = 'GET'
    headers: dict = field(default_factory=dict)
    data: str = ''
    creds: str = ''
    digest: bool = False
    cookie: str = ''
    cookie_file: str = ''
    output: str = ''
    remote_name: bool = False
    include: bool = False
    head: bool = False
    path_as_is: bool = False


def parse_request(args):
    r = Request()
    it = iter(args)
    for a in it:
        if a in ('-X', '--request'): r.method = next(it).upper()
        elif a in ('-H', '--header'):
            key, sep, value = next(it).partition(':')
            if not sep: raise ValueError('header needs Name: value')
            r.headers[key.lower()] = value.strip()
        elif a in ('-d', '--data', '--data-raw', '--data-urlencode', '--data-binary', '--json'):
            value = next(it)
            if a == '--data-urlencode':
                key, sep, val = value.partition('=')
                value = key + '=' + quote(val, safe='') if sep else quote(value, safe='')
            r.data += ('&' if r.data else '') + value
            if a == '--json': r.headers['content-type'] = 'application/json'
        elif a in ('-u', '--user'): r.creds = next(it)
        elif a == '--digest': r.digest = True
        elif a in ('-b', '--cookie'): r.cookie = next(it)
        elif a in ('-c', '--cookie-jar'): r.cookie_file = next(it)
        elif a in ('-o', '--output'): r.output = next(it)
        elif a in ('-O', '--remote-name'): r.remote_name = True
        elif a in ('-I', '--head'): r.head, r.method = True, 'HEAD'
        elif a in ('-i', '--include'): r.include = True
        elif a == '--path-as-is': r.path_as_is = True
        elif a in ('-s', '-S', '-sS', '--silent', '--show-error', '-L', '--location', '-k'): pass
        elif a.startswith('-') and set(a[1:]) <= set('sSiILk'):
            r.include = r.include or 'i' in a
            if 'I' in a: r.head, r.method = True, 'HEAD'
        elif a.startswith('-'): raise ValueError('unsupported curl option: ' + a)
        elif r.url: raise ValueError('one target URL per command')
        else: r.url = a
    if not r.url: raise ValueError('usage: curl [options] http://target/path')
    if r.data and r.method == 'GET': r.method = 'POST'
    return r


def build_runtime(number, flag):
    host, port, _ = TARGETS[number]
    state = {'uploads': {}, 'coupons': 0, 'quantity': 1, 'password': secrets.token_hex(16),
             'session': secrets.token_hex(16), 'key': 'SIMULATED-KEY-' + secrets.token_hex(24),
             'modes': {}, 'applications': {'/': True, '/docs': True, '/examples': True, '/host-manager': True, '/manager': True}}

    def file_path(shell, name):
        return shell._resolve(shell.program_cwd, name)

    def write(shell, name, text):
        p = file_path(shell, name)
        parent = p.rsplit('/', 1)[0] or '/'
        if parent not in shell.dirs:
            raise ValueError('output directory does not exist: ' + parent)
        shell.files[p] = text
        return p

    def fields(r):
        if r.headers.get('content-type', '').startswith('application/json'):
            try:
                data = json.loads(r.data)
                return data if isinstance(data, dict) else {}
            except ValueError: return {}
        return {k: v[-1] for k, v in parse_qs(r.data, keep_blank_values=True).items()}

    def target(r):
        """Return status, headers, body; target validation never makes a connection."""
        url = urlsplit(r.url if '://' in r.url else 'http://' + r.url)
        if url.scheme not in ('http', 'https') or url.hostname not in (host, LEGACY_TARGETS[number][0]) or (url.port or (443 if url.scheme == 'https' else 80)) != port:
            raise ValueError('target is outside this lab scope; read scope.txt')
        path = url.path or '/'
        # Match curl's normal removal of plain dot segments. Encoded dots survive.
        if not r.path_as_is:
            stack = []
            for piece in path.split('/'):
                if piece == '..':
                    if stack: stack.pop()
                elif piece != '.': stack.append(piece)
            path = '/'.join(stack) or '/'
        h = {'Server': {105: 'uvicorn', 106: 'Werkzeug httpd 0.14.1 (Python 3.8.17)',
                       107: 'Apache/2.4.49', 108: 'Apache Tomcat/8.5.19',
                       109: 'nginx/1.25.1'}.get(number, 'Apache/2.4.57'),
             'Content-Type': 'text/plain; charset=utf-8'}
        method, f = r.method, fields(r)
        def response(body, status=200, extra=None):
            from .ewpt_pages import render_target
            headers = {**h, **(extra or {})}
            body, content_type = render_target(number, path, method, status, headers, str(body), state)
            headers['Content-Type'] = content_type
            return status, headers, body
        def denied(): return response('Unauthorized', 401)
        def missing(): return response('Not Found', 404)
        def login():
            cookie = r.cookie or r.headers.get('cookie', '')
            return 'session=' + state['session'] in cookie.split('; ')

        if number == 101:
            if path == '/': return response('<form method="POST" action="/api/login">username password</form>')
            if path == '/api/login' and method == 'POST':
                # Execute against a throwaway in-memory toy DB, never the platform DB.
                db = sqlite3.connect(':memory:')
                try:
                    db.execute('CREATE TABLE users(username TEXT,password TEXT)')
                    db.execute('INSERT INTO users VALUES (?,?)', ('admin', state['password']))
                    query = "SELECT username FROM users WHERE username='%s' AND password='%s'" % (f.get('username', ''), f.get('password', ''))
                    row = db.execute(query).fetchone()
                except sqlite3.Error: row = None
                finally: db.close()
                if row and row[0] == 'admin':
                    return response('Welcome admin; visit /admin', extra={'Set-Cookie': 'session=' + state['session']})
                return denied()
            if path == '/admin': return response(flag) if login() else denied()
        elif number == 102:
            if path == '/': return response('File service: /uploads/')
            if path.startswith('/uploads/'):
                if method == 'OPTIONS': return response('', extra={'Allow': 'GET,HEAD,POST,PUT,DELETE,OPTIONS'})
                if method == 'PUT' and path != '/uploads/':
                    state['uploads'][path] = r.data
                    return response('Created', 201)
                if method == 'DELETE':
                    state['uploads'].pop(path, None)
                    return response('', 204)
                if method in ('GET', 'HEAD') and path in state['uploads']:
                    return response(state['uploads'][path] + '\n' + flag)
                return response('Directory listing forbidden', 403)
        elif number == 103:
            total = 100 * state['quantity'] - state['coupons'] * 10
            if path == '/': return response('Premium Flag $100; coupon WELCOME10. POST /apply-coupon coupon=...; POST /cart quantity=...; POST /checkout')
            if path == '/apply-coupon' and method == 'POST':
                if f.get('coupon') != 'WELCOME10': return response('Invalid coupon', 400)
                state['coupons'] += 1
                return response('Total: $' + str(100 * state['quantity'] - 10 * state['coupons']))
            if path == '/cart' and method == 'POST':
                try: state['quantity'] = int(f.get('quantity', '1'))
                except (ValueError, TypeError): return response('Invalid quantity', 400)
                return response('Total: $' + str(100 * state['quantity'] - state['coupons'] * 10))
            if path == '/checkout' and method == 'POST':
                return response(flag) if total <= 0 else response('Insufficient balance: total $' + str(total), 402)
        elif number == 104:
            if path in ('/', '/nexustech.html'):
                return response('<h1>NexusTech</h1>Custom web applications.\n<!-- Additional service: Maintenance and Support -->\nSubmit with: answer maintenance_and_support')
        elif number == 105:
            if path == '/': return response('{"info":"Visit the /docs endpoint for the OpenAPI UI"}')
            if path == '/docs': return response('OpenAPI schema: /openapi.json')
            if path == '/openapi.json':
                return response(json.dumps({'openapi': '3.0.0', 'paths': {'/api/v1/admin/flag': {'get': {'parameters': [{'name': 'X-Admin', 'in': 'header', 'required': True, 'schema': {'type': 'string', 'enum': ['true']}}]}}}}))
            if path == '/api/v1/admin/flag': return response(flag) if r.headers.get('x-admin') == 'true' else denied()
        elif number == 106:
            if path == '/': return response('Nexus portal. Framework information in response headers.')
            if path == '/robots.txt': return response('User-agent: *\nDisallow: /backup/app.py')
            if path == '/backup/app.py': return response('@app.route("/flag")\ndef flag():\n    # Requires X-Debug: 1\n    return read_secret()')
            if path == '/flag': return response(flag) if r.headers.get('x-debug') == '1' else denied()
        elif number == 107:
            if path == '/': return response('Apache default page. CGI enabled at /cgi-bin/.')
            decoded = unquote(path)
            if decoded.startswith(('/cgi-bin/', '/icons/')) and '/..' in decoded and decoded.endswith('/flag.txt'):
                return response(flag)
        elif number == 108:
            if path == '/': return response('Apache Tomcat 8.5.19. Manager: /manager/html')
            if path in ('/manager/html', '/manager/status'):
                if r.creds != 'tomcat:tomcat':
                    return response('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Tomcat Manager"'})
                if method == 'POST':
                    app = f.get('path')
                    action = f.get('action')
                    if app not in state['applications'] or action not in ('start', 'stop', 'reload'):
                        return response('Unknown application or command', 400)
                    if app == '/manager' and action == 'stop':
                        return response('The current manager application cannot stop itself in this lab', 400)
                    if action != 'reload': state['applications'][app] = action == 'start'
                return response('<h1>Tomcat Manager</h1>\n<!-- ' + flag + ' -->')
        elif number == 109:
            if path == '/': return response('<a href="/static/">Static files</a>')
            if path == '/static/': return response('assets: logo.svg, site.css')
            if path == '/static/site.css': return response('body { font-family: sans-serif; }', extra={'Content-Type':'text/css'})
            if path == '/static/logo.svg': return response('<svg xmlns="http://www.w3.org/2000/svg" width="120" height="36"><text y="26" font-size="24">Nexus</text></svg>', extra={'Content-Type':'image/svg+xml'})
            if unquote(path) == '/static../flag.txt': return response(flag)
        elif number == 111:
            if path == '/': return response('Nexus files. User ctf; SSH service is available.')
            if path == '/backup/': return response('id_rsa')
            if path == '/backup/id_rsa': return response(state['key'])
        elif number == 113:
            if path in ('/', '/flag'):
                if r.digest and r.creds == 'admin:admin': return response(flag if path == '/flag' else 'Authenticated; visit /flag')
                return response('Unauthorized', 401, {'WWW-Authenticate': 'Digest realm="example.com", nonce="training-nonce", qop="auth"'})
        elif number == 114:
            if path == '/': return response('Company website. Old deployment archives may remain.')
            if path == '/www.zip': return response('MYCTF_SIMULATED_ARCHIVE\n' + state['key'], extra={'Content-Type': 'application/zip'})
        elif number == 115:
            if path == '/': return response('API root: /api/. Use api-wordlist.txt.')
            if path == '/api/health': return response('{"status":"ok"}')
            if path == '/api/debug': return response(flag) if r.headers.get('x-forwarded-for') == '127.0.0.1' else response('Local clients only', 403)
        elif number == 116:
            if path in ('/reset/step1', '/reset/step2', '/reset/step3') and method in ('GET', 'HEAD'):
                return response('Reset your password')
            if path == '/': return response('Admin: admin@lab.local. POST /reset/step1 email=... -> /reset/step2 token=... -> /reset/step3 email=...&password=...; login at /api/login')
            if path == '/reset/step1' and method == 'POST': return response('If registered, an email was sent. Next: /reset/step2')
            if path == '/reset/step2' and method == 'POST': return response('Invalid token', 403)
            if path == '/reset/step3' and method == 'POST':
                password = f.get('password') or f.get('new_password')
                if f.get('email') == 'admin@lab.local' and isinstance(password, str) and password:
                    state['password'] = password
                    return response('Password reset. Log in at /api/login')
                return response('Email and password required', 400)
            if path in ('/api/login', '/login') and method == 'POST':
                if (f.get('email') == 'admin@lab.local' or f.get('username') == 'admin') and f.get('password') == state['password']:
                    return response('Logged in; visit /admin', extra={'Set-Cookie': 'session=' + state['session']})
                return denied()
            if path == '/admin': return response(flag) if login() else denied()
        elif number == 119:
            if path == '/': return response('Catalog: /product?id=1')
            if path == '/product':
                value = parse_qs(url.query, keep_blank_values=True).get('id', ['1'])[-1]
                db = sqlite3.connect(':memory:')
                try:
                    db.execute('CREATE TABLE products(id INTEGER,name TEXT,price TEXT)')
                    db.execute("INSERT INTO products VALUES (1,'Widget','25')")
                    db.execute('CREATE TABLE flags(flag TEXT)')
                    db.execute('INSERT INTO flags VALUES (?)', (flag,))
                    rows = db.execute('SELECT id,name,price FROM products WHERE id=' + value).fetchall()
                    return response('\n'.join(' | '.join(map(str, row)) for row in rows))
                except sqlite3.Error as exc: return response('SQL error: ' + str(exc), 500)
                finally: db.close()
        elif number == 120:
            if path == '/':
                if method == 'OPTIONS': return response('', extra={'Allow': 'GET,HEAD,OPTIONS,TRACE'})
                if method == 'TRACE': return response('TRACE / HTTP/1.1\n' + '\n'.join(k + ': ' + v for k, v in r.headers.items()) + '\nX-Lab-Flag: ' + flag)
                return response('Trace training service')
        return missing()

    def curl(shell, args, stdin, root):
        try:
            r = parse_request(args)
            if r.data.startswith('@'):
                content, err = shell._read(shell.program_cwd, r.data[1:], root, 'curl')
                if err: return '', err
                r.data = content
            if r.cookie and '=' not in r.cookie:
                content, err = shell._read(shell.program_cwd, r.cookie, root, 'curl')
                if err: return '', err
                r.cookie = content
            status, headers, body = target(r)
            if r.cookie_file and 'Set-Cookie' in headers: write(shell, r.cookie_file, headers['Set-Cookie'])
            if r.output or r.remote_name:
                name = r.output or urlsplit(r.url).path.rsplit('/', 1)[-1]
                if not name: raise ValueError('URL has no filename')
                write(shell, name, body)
                return '', ''
            reasons = {200: 'OK', 201: 'Created', 204: 'No Content', 400: 'Bad Request', 401: 'Unauthorized', 402: 'Payment Required', 403: 'Forbidden', 404: 'Not Found', 500: 'Internal Server Error'}
            prefix = 'HTTP/1.1 %d %s\n%s\n\n' % (status, reasons.get(status, ''), '\n'.join(k + ': ' + v for k, v in headers.items()))
            return (prefix if r.include or r.head else '') + ('' if r.head else body), ''
        except (ValueError, StopIteration, TypeError) as exc:
            return '', 'curl: ' + (str(exc) or 'missing option value')

    def ffuf(shell, args, stdin, root):
        options, it = {}, iter(args)
        try:
            for a in it:
                if a in ('-u', '-w', '-X', '-d', '-H', '-mc', '-fc', '-fs', '-ms'):
                    options.setdefault(a, []).append(next(it))
                elif a in ('-s', '-c'): pass
                else: raise ValueError('unsupported ffuf option: ' + a)
            url, wordfile = options['-u'][0], options['-w'][0]
            content, err = shell._read(shell.program_cwd, wordfile, root, 'ffuf')
            if err: return '', err
            selected = options.get('-mc', ['200,201,204,301,302,307,401,403,405,500'])[0]
            rejected = options.get('-fc', [''])[0].split(',')
            rows = []
            template = [url]
            for option in ('-X', '-d', '-H'):
                for value in options.get(option, []): template.extend([option, value])
            if not any('FUZZ' in value for value in template): raise ValueError('place FUZZ in the URL, data, or header')
            words = [line for line in content.splitlines() if line and not line.startswith('#')]
            for word in words[:256]:
                # URL payloads are encoded; form payloads preserve SQL quotes/spaces.
                expanded = [value.replace('FUZZ', quote(word, safe='') if i == 0 else urlencode({'v': word})[2:]) for i, value in enumerate(template)]
                status, _, body = target(parse_request(expanded))
                size = len(body.encode())
                if (selected == 'all' or str(status) in selected.split(',')) and str(status) not in rejected and str(size) not in options.get('-fs', [''])[0].split(',') and ('-ms' not in options or str(size) in options['-ms'][0].split(',')):
                    rows.append(f'{word} [Status: {status}, Size: {size}]')
            return '\n'.join(rows) or 'No matches.', ''
        except (ValueError, KeyError, StopIteration, TypeError) as exc:
            return '', 'ffuf: ' + (str(exc) or 'usage: ffuf -u URL/FUZZ -w wordlist.txt')

    def nmap(shell, args, stdin, root):
        if not args or not any(value in args for value in (host, LEGACY_TARGETS[number][0])): return '', 'nmap: target must match scope.txt'
        if number == 110: lines = ['53/tcp open domain EC2 DNS']
        elif number == 112: lines = ['3389/tcp open ms-wbt-server xrdp']
        elif number == 117: lines = ['5000/tcp open http nginx 1.25.1', '8000/tcp open http uvicorn', '8080/tcp open http Apache Tomcat 8.5.19', '8082/tcp open http Apache httpd 2.4.49']
        else:
            banner = {105: 'uvicorn', 106: 'Werkzeug httpd 0.14.1 Python 3.8.17', 107: 'Apache httpd 2.4.49', 108: 'Apache Tomcat 8.5.19', 109: 'nginx 1.25.1'}.get(number, 'Apache httpd')
            lines = [f'{port}/tcp open http {banner}']
            if number == 111: lines.append('22/tcp open ssh OpenSSH 8.2p1 Ubuntu')
        return 'Nmap scan report for ' + host + '\nPORT STATE SERVICE VERSION\n' + '\n'.join(lines), ''

    def dig(shell, args, stdin, root):
        if '@192.168.0.2' not in args: return '', 'dig: use the in-scope resolver @192.168.0.2'
        if '-x' in args and '192.168.0.2' in args:
            return '2.0.168.192.in-addr.arpa. 60 IN PTR ns1.nexustech.lab.', ''
        if any(a.upper() == 'AXFR' for a in args) and 'nexustech.lab' in args:
            return 'nexustech.lab. 60 IN SOA ns1.nexustech.lab. admin.nexustech.lab. 1 3600 600 86400 60\nflag.nexustech.lab. 60 IN TXT "' + flag + '"', ''
        if 'nexustech.lab' in args and any(a.upper() in ('NS','SOA') for a in args):
            return 'nexustech.lab. 60 IN NS ns1.nexustech.lab.', ''
        if 'version.bind' in args and any(a.upper() in ('CH', 'CHAOS') for a in args) and any(a.upper() == 'TXT' for a in args): return 'version.bind. 0 CH TXT "EC2 DNS"', ''
        if 'flag.nexustech.lab' in args and any(a.upper() == 'TXT' for a in args): return 'flag.nexustech.lab. 60 IN TXT "' + flag + '"', ''
        return ';; status: NXDOMAIN', ''

    def chmod(shell, args, stdin, root):
        if len(args) != 2 or args[0] != '600': return '', 'usage: chmod 600 <keyfile>'
        p = file_path(shell, args[1])
        if p not in shell.files: return '', 'chmod: No such file'
        state['modes'][p] = '600'
        return '', ''

    def ssh(shell, args, stdin, root):
        try:
            i = args.index('-i'); key = args[i + 1]
            destination = next((value for value in args if value in ('ctf@target.lab.local', 'ctf@ssh.lab.local')), None)
            if not destination: return '', 'ssh: target must match the assigned host and account'
            p = file_path(shell, key)
            if shell.files.get(p) != state['key']: return '', 'ssh: Permission denied (publickey)'
            if state['modes'].get(p) != '600': return '', 'ssh: UNPROTECTED PRIVATE KEY FILE! Use chmod 600.'
            shell.files['/home/ctf/flag.txt'] = flag
            # The simulated remote home maps to this terminal's home after login.
            shell.host = host
            cmd = args[args.index(destination) + 1:]
            if cmd: return (flag, '') if cmd in (['cat', '/home/ctf/flag.txt'], ['cat /home/ctf/flag.txt']) else ('', 'ssh: supported remote command: cat /home/ctf/flag.txt')
            return 'Authenticated to target.lab.local. Remote home mounted at /home/ctf; cat /home/ctf/flag.txt', ''
        except (ValueError, IndexError): return '', 'usage: ssh -i id_rsa ctf@target.lab.local [cat /home/ctf/flag.txt]'

    def rdp(shell, args, stdin, root):
        if not any(value in args for value in ('/v:target.lab.local', '/v:xrdp.lab.local')) or not all(value in args for value in ('/u:ctf', '/p:ctf')): return '', 'xfreerdp: authentication failed; use /v:host /u:user /p:password'
        shell.dirs.add(HOME + '/Desktop')
        shell.files[HOME + '/Desktop/flag.txt'] = flag
        return 'Simulated RDP connected. Desktop mounted at ~/Desktop. Use cat ~/Desktop/flag.txt (no graphical desktop).', ''

    def unzip(shell, args, stdin, root):
        if len(args) != 1: return '', 'usage: unzip www.zip'
        content = shell.files.get(file_path(shell, args[0]))
        if content != 'MYCTF_SIMULATED_ARCHIVE\n' + state['key']: return '', 'unzip: missing or invalid lab archive'
        base = file_path(shell, 'www')
        shell.dirs.add(base)
        shell.files[base + '/.env'] = 'APP_ENV=production\nDB_PASSWORD=forgotten-backup-secret'
        shell.files[base + '/flag.txt'] = flag
        return 'Archive: ' + args[0] + '\nextracting: www/.env\nextracting: www/flag.txt', ''

    def answer(shell, args, stdin, root):
        expected = {104: 'maintenance_and_support', 117: 'nginx_uvicorn_tomcat_apache', 118: '192.168.0.66'}[number]
        finding = re.sub(r'[\s,]+', '_', ' '.join(args).strip().lower())
        return (flag, '') if finding == expected else ('Incorrect answer. Review the evidence.', '')

    def awk(shell, args, stdin, root):
        if not args or args[0] != '{print $1}': return '', "awk: supported expression: '{print $1}'"
        text, err = shell._file_or_stdin(shell.program_cwd, args[1:], stdin, root, 'awk')
        return '\n'.join(line.split()[0] for line in (text or '').splitlines() if line.split()), err

    def sort(shell, args, stdin, root):
        text, err = shell._file_or_stdin(shell.program_cwd, [a for a in args if not a.startswith('-')], stdin, root, 'sort')
        numeric, reverse = any('n' in a for a in args if a.startswith('-')), any('r' in a for a in args if a.startswith('-'))
        try: return '\n'.join(sorted((text or '').splitlines(), key=(lambda x: float(x.split()[0])) if numeric else None, reverse=reverse)), err
        except (ValueError, IndexError): return '', 'sort: nonnumeric input'

    def uniq(shell, args, stdin, root):
        if any(a not in ('-c',) for a in args): return '', 'usage: uniq [-c] (piped input)'
        groups = []
        for line in (stdin or '').splitlines():
            if groups and groups[-1][1] == line: groups[-1][0] += 1
            else: groups.append([1, line])
        return '\n'.join(f'{count:7d} {line}' if '-c' in args else line for count, line in groups), ''

    result = {'nmap': nmap}
    if number not in (110, 112, 117, 118): result.update(curl=curl, ffuf=ffuf)
    if number == 110: result['dig'] = dig
    if number == 111: result.update(chmod=chmod, ssh=ssh)
    if number == 112: result['xfreerdp'] = rdp
    if number == 114: result['unzip'] = unzip
    if number in (104, 117, 118): result['answer'] = answer
    if number == 118: result.update(awk=awk, sort=sort, uniq=uniq)
    return result, target, state


def programs(number, flag):
    return build_runtime(number, flag)[0]


def scenario(number):
    host, port, label = TARGETS[number]
    brief = 'Investigate the assigned environment and recover the flag. No credentials or service information have been provided.'
    files = {
        HOME + '/README.txt': f'ENGAGEMENT {number}\nScope: {host}\n{brief}\nType help for terminal controls.\nIf a finding must be reported, use answer <finding> to obtain a flag.\nSubmit captured flags in the challenge panel.',
        HOME + '/scope.txt': host,
    }
    if number not in (110, 112, 117, 118):
        files.update({
            HOME + '/wordlist.txt': 'admin\nlogin\nbackup/\nbackup/id_rsa\nwww.zip\nbackup.zip\nrobots.txt\napi\ndocs\nopenapi.json\n',
            HOME + '/api-wordlist.txt': 'health\nusers\nstatus\ndebug\nadmin\n',
            HOME + '/sqli-payloads.txt': "test\nadmin\n' OR 1=1-- -\n1 ORDER BY 3-- -\n1 ORDER BY 4-- -\n-1 UNION SELECT 1,2,flag FROM flags-- -\n",
        })
    if number == 110:
        files['/etc/resolv.conf'] = 'nameserver 192.168.0.2\nsearch nexustech.lab'
    if number == 117:
        files[HOME + '/engagement.txt'] = ('Create a service inventory in ascending port order.\n'
            'Report the software family names using: answer <names separated by spaces or underscores>.\n'
            'Omit vendors and version numbers from the report.')
    if number == 118:
        rows = [f'192.168.0.10 - - [15/Nov/2026:12:00:{i:02d} +0000] "GET / HTTP/1.1" 200 512' for i in range(12)]
        rows += [f'192.168.0.66 - - [15/Nov/2026:12:01:{i % 60:02d} +0000] "POST /api/login?username=%27%22%3Cscript%3E{i} HTTP/1.1" {400 if i % 2 else 401} 32' for i in range(240)]
        rows += [f'192.168.0.25 - - [15/Nov/2026:12:02:{i:02d} +0000] "GET /products HTTP/1.1" 200 512' for i in range(30)]
        files[HOME + '/access.log'] = '\n'.join(rows)
    return ShellScenario(kind=f'ewpt_{number}', title='Terminal — ' + label, user='ctf', host='kali-web', home=HOME,
                         motd=f'Engagement {number}. Scope: {host}. Type help for terminal controls.',
                         files=files, programs=lambda flag: programs(number, flag))


EWPT_SCENARIOS = tuple(scenario(number) for number in TARGETS)

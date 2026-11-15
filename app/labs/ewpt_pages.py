"""Self-contained target pages. No external assets or platform credentials.

All user-controlled output is escaped. The renderer receives only responses
already authorized by the target; it is never given an instance flag directly.
"""
from __future__ import annotations

from html import escape as esc
import json
import re
from urllib.parse import urlencode

WEB_NUMBERS = frozenset({101, 102, 103, 104, 105, 106, 107, 108, 109, 111, 113, 114, 115, 116, 119, 120})
BROWSER_DEFAULTS = frozenset({101, 103, 104, 105, 106, 108, 116, 119})

CSS = '''
*{box-sizing:border-box}body{margin:0;background:#f5f6f8;color:#253044;font:15px/1.6 Arial,Helvetica,sans-serif}a{color:#1768ac}button,input,select{font:inherit}button,.button{display:inline-block;background:#225fbd;color:white;border:0;border-radius:5px;padding:10px 20px;cursor:pointer;text-decoration:none}button:hover,.button:hover{filter:brightness(.93)}button:disabled{opacity:.45;cursor:not-allowed}input,select{border:1px solid #ccd2da;border-radius:5px;padding:10px 12px;max-width:100%;background:white;color:#253044}label{display:block;margin:14px 0 6px;font-size:13px;font-weight:bold}.muted{color:#6f7784}.small{font-size:12px}h1,h2,h3{line-height:1.25}h1{font-size:30px}h2{font-size:21px}pre,code{font-family:Consolas,Menlo,monospace}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f0f2f5;padding:20px;border-radius:5px}.notice{padding:12px 16px;border:1px solid #cfdae8;background:#f0f6ff;margin:20px 0;border-radius:4px}.error{color:#a51d28;border-color:#e4b4b8;background:#fff0f0}.success{color:#1c6847;background:#eef9f1;border-color:#aad9b8}.card{background:white;border:1px solid #e0e4ea;border-radius:10px;padding:28px}.wrap{max-width:1080px;padding:35px 28px;margin:auto}.top{padding:20px 30px;border-bottom:1px solid #e3e6eb;background:white;display:flex;align-items:center;justify-content:space-between;gap:20px}.top b{font-size:20px;letter-spacing:-.7px}.top nav{display:flex;gap:24px}.top nav a{color:#596171;text-decoration:none;font-size:13px}.auth{max-width:420px;margin:58px auto;padding:0 20px}.auth input{width:100%}.auth button{width:100%;margin-top:24px}.brand{font-weight:bold;font-size:21px;letter-spacing:-1px;margin:0 0 30px}.auth .card{box-shadow:0 10px 35px #1d32400a}.auth h1{font-size:26px;margin:0 0 10px}.stack>*+*{margin-top:18px}.flex{display:flex;gap:16px;align-items:center}.columns{display:grid;grid-template-columns:1.35fr 1fr;gap:28px}table{width:100%;border-collapse:collapse;text-align:left}td,th{padding:10px;border-bottom:1px solid #e2e5ea;font-size:13px}th{background:#f4f6f8}.pill{font-size:11px;border-radius:20px;padding:4px 9px;background:#e8f4eb;color:#24683d}details summary{cursor:pointer}input:focus-visible,button:focus-visible,a:focus-visible{outline:3px solid #7aaaff;outline-offset:2px}@media(max-width:650px){.columns{grid-template-columns:1fr}.wrap{padding:24px 18px}.top nav{gap:12px}.auth{margin:30px auto}.card{padding:22px}h1{font-size:26px}}
'''


def document(title, content, extra='', body_class=''):
    return f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><style>{CSS}\n{extra}</style></head><body class="{body_class}">{content}</body></html>'


def note(message, error=False):
    return f'<div class="notice {"error" if error else "success"}" role="status">{esc(message)}</div>'


def field(label, name, *, type='text', value='', required=True):
    return f'<label for="{esc(name)}">{esc(label)}</label><input id="{esc(name)}" name="{esc(name)}" type="{esc(type)}" value="{esc(str(value))}" {"required" if required else ""} autocomplete="off">'


def nav(brand, links):
    return f'<header class="top"><b>{brand}</b><nav>' + ''.join(f'<a href="{esc(path)}">{esc(label)}</a>' for label, path in links) + '</nav></header>'


def flag_text(body):
    # Only called with a response body produced by the gated target.
    match = re.search(r'MYCTF\{[^}]+\}', body)
    return esc(match.group()) if match else ''


def auth_page(number, status, message='', step='login'):
    is_reset = number == 116
    brand = 'NEXUS <span style="font-weight:400;color:#8a93a3">workspace</span>' if is_reset else 'NEXUS<span style="color:#386de8">PORTAL</span>'
    if step == 'login':
        title = 'Welcome back' if is_reset else 'Staff sign in'
        action = '/api/login'
        inputs = field('Email address' if is_reset else 'Username', 'email' if is_reset else 'username', type='email' if is_reset else 'text') + field('Password', 'password', type='password')
        submit, subtitle = 'Sign in', 'Sign in to continue to your workspace.'
        footer = '<a href="/reset/step1">Forgot your password?</a>' if is_reset else 'Authorized staff only · Nexus Technologies'
    elif step == 'step1':
        title, subtitle, action, submit = 'Reset your password', 'Enter your email and we’ll send you a verification code.', '/reset/step1', 'Send reset code'
        inputs, footer = field('Email address', 'email', type='email'), '<a href="/">Back to sign in</a>'
    elif step == 'step2':
        title, subtitle, action, submit = 'Check your email', 'Enter the verification code sent to your email address.', '/reset/step2', 'Verify code'
        inputs, footer = field('Verification code', 'token'), '<a href="/reset/step1">Send another code</a>'
    else:
        title, subtitle, action, submit = 'Choose a new password', 'Set a new password for your account.', '/reset/step3', 'Save password'
        inputs = field('Email address', 'email', type='email') + field('New password', 'password', type='password')
        footer = '<a href="/">Back to sign in</a>'
    notice = note(message, status >= 400) if message else ''
    content = f'<main class="auth"><p class="brand">{brand}</p><section class="card"><h1>{title}</h1><p class="muted">{subtitle}</p>{notice}<form method="post" action="{action}">{inputs}<button type="submit">{submit}</button></form><p style="text-align:center;font-size:13px;margin-top:24px">{footer}</p></section><p class="muted small" style="text-align:center">Nexus Technologies · Account services</p>'
    if is_reset: content += '<p class="muted small" style="text-align:center">Need help? Contact admin@lab.local</p>'
    return document(title, content + '</main>')


def tomcat_home():
    extra = '.top{background:#f9f9f9;border-top:7px solid #4d7831}.tomcat-title{font:bold 33px Georgia,serif;color:#354b2f}.welcome{background:#558338;color:white;padding:28px;border-radius:6px}.welcome h1{font-size:24px}.welcome a{color:white}.tc-panels{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.tc-panel{background:#fff9e7;border:1px solid #e8dbb9;border-radius:6px;padding:22px}.tc-panel h2{font-size:18px}@media(max-width:650px){.tc-panels{grid-template-columns:1fr}}'
    body = '<header class="top"><span class="tomcat-title">Apache Tomcat</span><span>Version 8.5.19</span></header><main class="wrap"><div class="welcome"><h1>Apache Tomcat/8.5.19</h1><p>Tomcat is installed and running on this server.</p><a href="/manager/html" class="button" style="background:#f5f2d6;color:#344726">Manager App</a> <a href="/manager/status" style="margin-left:18px">Server Status</a></div><h2 style="margin-top:35px">Developer Quick Start</h2><p class="muted">Welcome to the Apache Tomcat web application server.</p><div class="tc-panels"><section class="tc-panel"><h2>Managing Tomcat</h2><p>View deployed applications and monitor the server.</p><a href="/manager/html">Web Application Manager →</a></section><section class="tc-panel"><h2>Server Information</h2><p>Apache Tomcat 8.5.19<br>JVM 1.8.0_144-b01<br>Linux amd64</p></section><section class="tc-panel"><h2>Application Server</h2><p>Java Servlet / JSP container</p><p class="muted small">Local server installation</p></section></div><footer class="muted small" style="margin-top:45px;border-top:1px solid #ddd;padding-top:18px">Apache Tomcat · Local training reproduction</footer></main>'
    return document('Apache Tomcat/8.5.19', body, extra)


def basic_auth_page(number, status):
    host = 'target.lab.local:8080' if number == 108 else 'target.lab.local'
    realm = 'Tomcat Manager' if number == 108 else 'example.com'
    next_path = '/manager/html' if number == 108 else '/flag'
    body = f'<main class="auth"><section class="card"><span class="muted small">{host}</span><h1 style="margin-top:15px">Sign in</h1><p class="muted">{esc(realm)}</p><form method="post" action="/_auth?{urlencode({"next": next_path})}">{field("Username", "username")}{field("Password", "password", type="password")}<button type="submit">Sign in</button></form><p class="muted small">The server requires {"Basic" if number == 108 else "Digest"} authentication.</p></section><p class="muted small" style="text-align:center">HTTP {status} · Unauthorized</p></main>'
    return document('Sign in — ' + host, body)


def tomcat_manager(path, body, state):
    extra = 'body{background:white;color:black;font:13px Arial,sans-serif;padding:8px}h1{font-size:25px;color:#303030;margin:12px 0}h2{font-size:17px;background:#525d76;color:white;padding:5px 8px;margin:18px 0 0}table{border:1px solid #999}th{background:#d2d8e3;text-align:center;font-size:12px}td{font-size:12px;border:1px solid #aaa;padding:7px}a{color:#0000aa}button{font-size:11px;padding:3px 8px;border:1px solid #999;border-radius:0;color:black;background:#eee}input{font-size:12px;padding:4px;border-radius:0}label{font-size:12px;margin-top:8px}.commands{display:flex;gap:5px;flex-wrap:wrap}.manager-nav{background:#eef0f5;padding:8px;border:1px solid #aaa}.manager-nav a{margin-right:20px}.subhead{padding:7px;background:#eee;border:1px solid #aaa}pre{font-size:12px}'
    contexts = {'/': 'Welcome to Tomcat', '/docs': 'Tomcat Documentation', '/examples': 'Servlet and JSP Examples', '/host-manager': 'Tomcat Host Manager', '/manager': 'Tomcat Manager Application'}
    rows = ''
    for context, running in state['applications'].items():
        commands = ''.join(f'<form method="post" action="/manager/html"><input type="hidden" name="path" value="{esc(context)}"><button name="action" value="{action}" type="submit">{label}</button></form>' for action, label in [('start','Start'),('stop','Stop'),('reload','Reload')])
        rows += f'<tr><td>{esc(context)}</td><td>None specified</td><td>{contexts.get(context,"Web application")}</td><td>{str(running).lower()}</td><td>0</td><td><div class="commands">{commands}</div></td></tr>'
    comment = re.search(r'<!--.*?-->', body, re.S)
    secret = comment.group() if comment else ''
    content = f'<header style="border-bottom:2px solid #525d76;padding-bottom:8px"><span style="float:right;font-size:12px">Apache Tomcat/8.5.19</span><h1>Tomcat Web Application Manager</h1></header><p><b>Message:</b> OK</p><h2>Manager</h2><nav class="manager-nav"><a href="/manager/html">List Applications</a><a href="/manager/status">Server Status</a><a href="/">Tomcat Home</a><a href="/_logout">Log out</a></nav>'
    if path != '/manager/status':
        content += f'<h2>Applications</h2><div style="overflow-x:auto"><table><thead><tr><th>Path</th><th>Version</th><th>Display Name</th><th>Running</th><th>Sessions</th><th>Commands</th></tr></thead><tbody>{rows}</tbody></table></div><h2>Deploy</h2><div class="subhead">WAR file to deploy</div><div style="padding:12px;border:1px solid #aaa"><label>Select WAR file to upload</label><input type="file" disabled><button disabled>Deploy</button><p class="muted small">WAR deployment is unavailable in this training target.</p></div>'
    content += '<h2>Server Information</h2><div style="overflow-x:auto"><table><thead><tr><th>Tomcat Version</th><th>JVM Version</th><th>JVM Vendor</th><th>OS Name</th><th>OS Version</th><th>OS Architecture</th></tr></thead><tbody><tr><td>Apache Tomcat/8.5.19</td><td>1.8.0_144-b01</td><td>Oracle Corporation</td><td>Linux</td><td>4.15.0</td><td>amd64</td></tr></tbody></table></div>' + secret
    return document('Tomcat Web Application Manager', content, extra)


def shop(path, status, body, state):
    total = 100 * state['quantity'] - state['coupons'] * 10
    content = nav('nexus / store', [('Shop', '/'), ('Your cart', '/')])
    if flag_text(body):
        content += f'<main class="wrap"><section class="card"><span class="pill">Payment complete</span><h1>Your Premium Flag is ready.</h1><pre>{flag_text(body)}</pre><p class="muted">Thank you for your order.</p><a href="/">Continue shopping</a></section></main>'
        return document('Order complete — Nexus Store', content)
    notice = note(body, status >= 400) if status >= 400 or (path == '/apply-coupon' and status == 200) else ''
    content += f'<main class="wrap"><p class="muted small">STORE / DIGITAL PRODUCTS</p><h1>Your cart</h1>{notice}<div class="columns"><section class="card"><div style="height:190px;background:#e8e7e2;border-radius:7px;display:flex;align-items:center;justify-content:center;margin-bottom:25px"><span style="font:70px Georgia;color:#6e735f">⚑</span></div><span class="muted small">DIGITAL DOWNLOAD</span><h2>Premium Flag</h2><p class="muted">One premium capture. Delivered instantly after checkout.</p><form method="post" action="/cart" class="flex">{field("Quantity", "quantity", type="number", value=state["quantity"])}<button type="submit" style="align-self:end">Update</button></form></section><aside class="card" style="align-self:start"><h2>Order summary</h2><p>Premium Flag <span style="float:right">$100.00</span></p><p class="muted">Quantity <span style="float:right">{state["quantity"]}</span></p><p class="muted">Discount <span style="float:right">−${state["coupons"] * 10:.2f}</span></p><hr style="border:0;border-top:1px solid #ddd;margin:24px 0"><h2>Total <span style="float:right">${total:.2f}</span></h2><form method="post" action="/apply-coupon">{field("Promo code", "coupon")}<button type="submit" style="margin-top:12px;background:#515848">Apply code</button></form><p class="muted small">New here? Save 10% with WELCOME10.</p><form method="post" action="/checkout"><button type="submit" style="width:100%;margin-top:16px;background:#252d25">Checkout</button></form></aside></div></main>'
    return document('Your cart — Nexus Store', content, 'body{background:#f7f6f2}.top b{font-family:Georgia,serif;font-size:25px}.card{border-color:#e3e1d9}h1,h2{font-family:Georgia,serif}')


def company(number):
    is_files = number in (111, 114)
    body = nav('NEXUS<span style="color:#3362d1">TECH</span>', [('Company', '/'), ('Services', '/nexustech.html')] if not is_files else [('Home','/')])
    body += '<main class="wrap"><section style="padding:45px 0 55px;max-width:780px"><p style="color:#3362d1;font-size:12px;letter-spacing:2px">TECHNOLOGY THAT MOVES YOU FORWARD</p><h1 style="font-size:clamp(36px,6vw,58px);letter-spacing:-2px">Better software.<br>Built around your business.</h1><p class="muted" style="font-size:18px;max-width:560px">We design and develop custom web applications for ambitious organizations.</p></section><div class="columns"><section class="card"><span class="small muted">01 / OUR EXPERTISE</span><h2>Custom web development</h2><p>Thoughtful, reliable applications that help your teams do more.</p></section><section class="card"><span class="small muted">02 / OUR APPROACH</span><h2>From idea to impact</h2><p>Close collaboration. Clear communication. Software that fits.</p></section></div><footer class="muted small" style="margin-top:60px;border-top:1px solid #ddd;padding-top:20px">© NexusTech · hello@nexustech.lab</footer></main>'
    if number == 104: body += '\n<!-- Additional service: Maintenance and Support -->'
    return document('NexusTech — Custom Web Applications', body, 'body{background:#f8faff}')


def swagger():
    extra = 'body{background:#fafafa;color:#3b4151}.swagger-top{background:#1b1b1b;color:#fff;padding:15px 28px;font-size:22px}.swagger-top b{color:#85c942}.version{font:12px monospace;color:#fff;background:#7b8490;border-radius:12px;padding:3px 9px;vertical-align:middle}.endpoint{border:1px solid #61affe;background:#ebf3fb;border-radius:4px;margin-top:24px}.endpoint summary{display:flex;align-items:center;gap:15px;padding:12px}.method{background:#61affe;color:white;padding:4px 20px;border-radius:3px;font-weight:bold;font-size:13px}.endpoint section{padding:10px 20px 25px;border-top:1px solid #c2d9f0}.endpoint button{background:#4990d0;border:1px solid #3983c3;width:100%}.schema{font-size:13px}.swagger-title{font-size:34px;letter-spacing:-1px}'
    body = '<header class="swagger-top"><b>◉</b> swagger <span style="font-size:11px;float:right;margin-top:7px">OpenAPI 3.0</span></header><main class="wrap"><h1 class="swagger-title">Nexus API <span class="version">1.0.0</span></h1><a href="/openapi.json" class="small">/openapi.json</a><p>Internal application API.</p><label>Servers</label><select><option>http://target.lab.local:8000</option></select><h2 style="margin-top:45px;border-bottom:1px solid #ddd;padding-bottom:12px">admin</h2><details class="endpoint"><summary><span class="method">GET</span><code>/api/v1/admin/flag</code><span class="small muted">Read admin flag</span></summary><section><h3>Parameters</h3><table><thead><tr><th>Name</th><th>Description</th></tr></thead><tbody><tr><td><b>X-Admin</b> <span style="color:#d33">* required</span><br><code>string (header)</code></td><td>Administrative request marker.<br><span class="schema">Allowed values: <code>true</code></span></td></tr></tbody></table><form method="get" action="/api/v1/admin/flag"><label for="x-admin">X-Admin</label><input id="x-admin" data-header="X-Admin" name="X-Admin" placeholder="X-Admin" required><button style="margin-top:16px" type="submit">Execute</button></form><h3>Responses</h3><p><b>200</b> Successful response</p><p><b>401</b> Unauthorized</p></section></details><details style="margin-top:35px;border:1px solid #ccc;padding:15px"><summary><b>Schemas</b></summary><p class="schema">HTTPValidationError</p></details></main>'
    return document('Nexus API — Swagger UI', body, extra)


def directory(path, items):
    rows = '<tr><td><a href="/">Parent Directory</a></td><td>—</td><td>—</td></tr>'
    for name, href, size in items:
        rows += f'<tr><td><a href="{esc(href)}">{esc(name)}</a></td><td>2026-11-15 10:42</td><td>{size}</td></tr>'
    return document('Index of ' + path, f'<h1>Index of {esc(path)}</h1><hr><table><thead><tr><th>Name</th><th>Last modified</th><th>Size</th></tr></thead><tbody>{rows}</tbody></table><hr><address>Apache Server</address>', 'body{font:16px "Times New Roman",serif;background:white;color:black;padding:8px}h1{font-size:32px}table{width:auto;min-width:65%}th,td{background:white;font:16px "Times New Roman",serif;border:0;padding:4px 30px 4px 0}a{color:#0000ee}')


def apache_home():
    body = '<main style="max-width:800px;margin:28px auto;border:2px solid #263249;background:white"><header style="background:#f7f7f7;padding:24px;text-align:center"><h1 style="font-size:27px">Apache2 Ubuntu Default Page</h1></header><h2 style="background:#d96321;color:white;text-align:center;margin:0;padding:12px">It works!</h2><section style="padding:25px"><p>This is the default welcome page used to test the operation of the Apache2 server after installation on Ubuntu systems.</p><p>If you can read this page, the Apache HTTP server installed at this site is working properly.</p></section><h2 style="background:#36475e;color:white;padding:10px 25px;font-size:18px">Configuration Overview</h2><section style="padding:5px 25px 25px"><p>The server configuration is split across several files.</p><pre>/etc/apache2/apache2.conf\n/etc/apache2/ports.conf\n/etc/apache2/sites-enabled/</pre><p>CGI applications are available under <code>/cgi-bin/</code>.</p></section><footer style="padding:15px 25px;background:#eee;font-size:12px">Apache/2.4.49 (Ubuntu) Server</footer></main>'
    return document('Apache2 Ubuntu Default Page: It works', body, 'body{background:#ddd}h2{border-radius:0}')


def render_target(number, path, method, status, headers, body, state):
    """Return (body, MIME type), preserving raw artifacts and protocol evidence."""
    plain = headers.get('Content-Type', 'text/plain; charset=utf-8')
    if status == 404:
        return document('404 Not Found', '<main class="wrap"><h1>Not Found</h1><p>The requested URL was not found on this server.</p><hr><p class="muted small">' + esc(headers.get('Server', '')) + '</p></main>'), 'text/html; charset=utf-8'
    if number == 108:
        if status == 401: return basic_auth_page(number, status), 'text/html; charset=utf-8'
        if path == '/': return tomcat_home(), 'text/html; charset=utf-8'
        if status == 200 and path in ('/manager/html', '/manager/status'): return tomcat_manager(path, body, state), 'text/html; charset=utf-8'
    if number == 113 and status == 401: return basic_auth_page(number, status), 'text/html; charset=utf-8'
    if number in (101, 116):
        if path == '/admin' and status == 200:
            page = nav('NEXUS workspace', [('Dashboard','/admin'),('Sign out','/_logout')]) + f'<main class="wrap"><p class="small muted">WORKSPACE / OVERVIEW</p><h1>Welcome, admin.</h1><section class="card"><h2>Administrator console</h2><p class="muted">Your private workspace token</p><pre>{flag_text(body)}</pre></section></main>'
            return document('Admin dashboard — Nexus', page), 'text/html; charset=utf-8'
        if path in ('/', '/api/login', '/login'):
            if status == 200 and method == 'POST': return document('Signed in', '<main class="auth"><section class="card"><h1>You’re signed in.</h1><a class="button" href="/admin">Open dashboard</a></section></main>'), 'text/html; charset=utf-8'
            return auth_page(number, status, 'Invalid username or password.' if status == 401 else ''), 'text/html; charset=utf-8'
        if number == 116 and path.startswith('/reset/step'):
            step = path.rsplit('/', 1)[-1]
            if method == 'POST' and status == 200:
                if step == 'step1': step = 'step2'
                elif step == 'step3': return document('Password updated', '<main class="auth"><section class="card"><h1>Password updated</h1><p>You can now sign in with your new password.</p><a class="button" href="/">Back to sign in</a></section></main>'), 'text/html; charset=utf-8'
            return auth_page(number, status, 'Invalid verification code.' if status >= 400 else '', step), 'text/html; charset=utf-8'
    if number == 103: return shop(path, status, body, state), 'text/html; charset=utf-8'
    if number == 104 and status == 200: return company(number), 'text/html; charset=utf-8'
    if number in (111, 114) and path == '/': return company(number), 'text/html; charset=utf-8'
    if number == 111 and path == '/backup/': return directory(path, [('id_rsa','/backup/id_rsa','1679')]), 'text/html; charset=utf-8'
    if number == 105:
        if path == '/docs': return swagger(), 'text/html; charset=utf-8'
        if path in ('/', '/openapi.json', '/api/v1/admin/flag'):
            try: body = json.dumps(json.loads(body), indent=2)
            except ValueError: pass
            return body, 'application/json' if path != '/api/v1/admin/flag' else 'text/plain; charset=utf-8'
    if number == 106 and path == '/':
        page = nav('Nexus Console', [('Overview','/')]) + '<main class="wrap"><p class="muted small">APPLICATION STATUS</p><h1>Everything is running.</h1><section class="card"><h2>Internal service portal</h2><p class="muted">Welcome to the Nexus operations console.</p><span class="pill">Service healthy</span></section></main>'
        return document('Nexus Console',page), 'text/html; charset=utf-8'
    if number == 107 and path == '/': return apache_home(), 'text/html; charset=utf-8'
    if number == 109 and path == '/':
        return document('Welcome to nginx!', '<main style="width:35em;max-width:90%;margin:60px auto"><h1>Welcome to nginx!</h1><p>If you see this page, the nginx web server is successfully installed and working.</p><p>Further configuration is required.</p><p><em>Thank you for using nginx.</em></p></main>', 'body{background:white;color:black;font-family:Tahoma,Verdana,Arial,sans-serif}h1{font-size:32px}'), 'text/html; charset=utf-8'
    if number == 109 and path == '/static/': return directory(path,[('logo.svg','/static/logo.svg','861'),('site.css','/static/site.css','2048')]), 'text/html; charset=utf-8'
    if number in (102, 120) and path == '/' and method not in ('OPTIONS','TRACE'):
        page = '<main class="wrap"><h1>' + ('File service' if number == 102 else 'Nexus HTTP service') + '</h1><p>Service is online.</p>' + ('<a href="/uploads/">Shared files →</a>' if number == 102 else '') + '</main>'
        return document('Nexus HTTP service',page), 'text/html; charset=utf-8'
    if number == 115 and path == '/': return '{"service":"Nexus API","version":"1.0","base":"/api/"}', 'application/json'
    if number == 119:
        if path == '/':
            page = nav('NEXUS / supply',[('Catalog','/')]) + '<main class="wrap"><p class="muted small">SHOP / ALL PRODUCTS</p><h1>Tools for your next idea.</h1><section class="card" style="max-width:370px"><div style="height:150px;background:#e3ebef;border-radius:6px;display:flex;align-items:center;justify-content:center"><div style="width:75px;height:75px;background:#90a9b7;box-shadow:12px 12px 0 #bacbd4;border-radius:10px"></div></div><h2>Widget</h2><p class="muted">A dependable everyday essential.</p><b>$25.00</b><p><a class="button" href="/product?id=1">View product</a></p></section></main>'
            return document('Catalog — Nexus Supply',page), 'text/html; charset=utf-8'
        if path == '/product':
            page = nav('NEXUS / supply',[('Catalog','/')]) + '<main class="wrap"><p class="muted small">CATALOG / PRODUCT</p><h1>Product details</h1>'
            if status >= 400: page += '<pre>' + esc(body) + '</pre>'
            else:
                rows = ''.join('<tr>' + ''.join('<td>'+esc(col.strip())+'</td>' for col in row.split('|')) + '</tr>' for row in body.splitlines())
                page += '<section class="card"><table><thead><tr><th>ID</th><th>Product</th><th>Price</th></tr></thead><tbody>' + rows + '</tbody></table></section>'
            return document('Product — Nexus Supply',page + '</main>'), 'text/html; charset=utf-8'
    return body, plain

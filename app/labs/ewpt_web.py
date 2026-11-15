"""Hybrid EWPT labs: a browser target and terminal sharing one instance runtime."""
from __future__ import annotations

import base64
import binascii
from urllib.parse import parse_qs, urlsplit

from flask import render_template

from .. import limiter
from .base import LabResult, get_state
from .ewpt import TARGETS, Request, build_runtime
from .ewpt_pages import BROWSER_DEFAULTS, WEB_NUMBERS
from .fakeshell import FakeShell
from .shelllab import ShellLab, _json


class EwptLab(ShellLab):
    def __init__(self, scenario):
        super().__init__(scenario)
        self.number = int(scenario.kind.split('_')[-1])
        self.has_web_ui = self.number in WEB_NUMBERS
        self.default_lab_view = 'target' if self.number in BROWSER_DEFAULTS else 'terminal'

    def _state(self, instance):
        st = get_state(instance['id'])
        if 'shell' not in st:
            commands, target, target_state = build_runtime(self.number, instance['flag'])
            sc = self.scenario
            files = {path: text.replace('{flag}', instance['flag']) for path, text in sc.files.items()}
            st.update(shell=FakeShell(files, user=sc.user, home=sc.home, host=sc.host,
                                     programs=commands), cwd=sc.home, target=target,
                      target_state=target_state, web_cookie='', web_credentials='')
        return st

    def dispatch(self, instance, subpath, request):
        sub = subpath.strip('/')
        if not self.has_web_ui or sub in ('shell', 'exec', 'terminal'):
            return super().dispatch(instance, 'shell' if sub == 'shell' else sub, request)
        st = self._state(instance)
        if sub == 'web/request':
            if request.method != 'POST': return _json({'error': 'Use POST.'}, 405)
            if not limiter.allow(f"ewpt-web:{instance['id']}", 120, 60):
                return _json({'error': 'Too many requests. Slow down a little.'}, 429)
            return self._request(st, request.get_json(silent=True))
        if request.method != 'GET': return _json({'error': 'Use the target request endpoint.'}, 405)
        host, port, title = TARGETS[self.number]
        initial_path = '/' + sub if sub else '/'
        if request.query_string:
            initial_path += '?' + request.query_string.decode('utf-8', errors='replace')
        return LabResult(render_template('labs/ewpt_browser.html', base=self.base_url(instance),
                                        host=host, port=port, title=title,
                                        initial_path=initial_path))

    def _request(self, st, payload):
        try:
            if not isinstance(payload, dict): raise ValueError('Request must be an object.')
            path = payload.get('path', '/')
            method = payload.get('method', 'GET')
            data = payload.get('data', '')
            headers = payload.get('headers', {})
            if not isinstance(path, str) or not path or len(path) > 2048:
                raise ValueError('Path must be text (max 2048 characters).')
            if not isinstance(method, str) or method.upper() not in {'GET','HEAD','POST','PUT','PATCH','DELETE','OPTIONS','TRACE'}:
                raise ValueError('Unsupported HTTP method.')
            if not isinstance(data, str) or len(data) > 8192: raise ValueError('Request body is too large.')
            if not isinstance(headers, dict) or len(headers) > 32: raise ValueError('Invalid request headers.')
            if any(not isinstance(k, str) or not isinstance(v, str) or len(k) > 100 or len(v) > 1024
                   or '\n' in k or '\r' in k or '\n' in v or '\r' in v for k,v in headers.items()):
                raise ValueError('Invalid request headers.')
            headers = {k.lower(): v for k, v in headers.items()}
            host, port, _ = TARGETS[self.number]
            origin = 'http://' + host + (':' + str(port) if port != 80 else '')
            if path.startswith(('http://', 'https://')):
                url = urlsplit(path)
                if url.hostname != host or (url.port or (443 if url.scheme == 'https' else 80)) != port:
                    raise ValueError('Target is outside this lab scope.')
                path = (url.path or '/') + ('?' + url.query if url.query else '')
            if not path.startswith('/') or path.startswith('//') or '\\' in path or any(ord(c) < 32 for c in path):
                raise ValueError('Enter a path on this lab target.')
            if '://' in path: raise ValueError('Enter a path on this lab target.')
            method = method.upper()
            if urlsplit(path).path == '/_auth':
                if self.number not in (108, 113) or method != 'POST':
                    raise ValueError('Authentication is unavailable for this request.')
                fields = parse_qs(data, keep_blank_values=True)
                st['web_credentials'] = fields.get('username', [''])[-1] + ':' + fields.get('password', [''])[-1]
                wanted = parse_qs(urlsplit(path).query).get('next', ['/'])[-1]
                allowed = ('/manager/html', '/manager/status', '/') if self.number == 108 else ('/flag', '/')
                path = wanted if wanted in allowed else allowed[0]
                method, data = 'GET', ''
            elif urlsplit(path).path == '/_logout':
                st['web_credentials'], st['web_cookie'] = '', ''
                path, method, data = '/', 'GET', ''
            creds = st['web_credentials']
            auth = headers.get('authorization', '')
            if auth.startswith('Basic '):
                try: creds = base64.b64decode(auth[6:], validate=True).decode('utf-8')
                except (binascii.Error, UnicodeDecodeError): raise ValueError('Invalid Basic authentication value.')
            target_request = Request(url=origin + path, method=method, data=data,
                                     headers=headers, creds=creds,
                                     cookie=headers.get('cookie', st['web_cookie']),
                                     digest=self.number == 113, path_as_is=True)
            status, response_headers, body = st['target'](target_request)
            if 'Set-Cookie' in response_headers:
                st['web_cookie'] = response_headers['Set-Cookie']
            if method == 'HEAD': body = ''
            return _json({'path': path, 'status': status, 'headers': response_headers,
                          'body': body})
        except (ValueError, TypeError) as exc:
            return _json({'error': str(exc)}, 400)

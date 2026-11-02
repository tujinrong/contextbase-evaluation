"""Authenticated loopback Streamable HTTP MCP transport for one native task."""
from contextlib import AbstractContextManager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import secrets
import threading


def encode_message(value):
    """Canonical wire JSON encoding shared by the broker and reply budget."""
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def tool_result(value):
    """Exact successful MCP tools/call result; inner JSON escaping is intentional."""
    return {'content': [{'type': 'text', 'text': encode_message(value).decode('utf-8')}], 'isError': False}


class Broker(AbstractContextManager):
    def __init__(self, schemas, invoke):
        self.schemas, self.invoke = schemas, invoke
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.RLock()
        self.active = False

    def __enter__(self):
        broker = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                self.send_error(405)

            def do_DELETE(self):
                self.send_error(405)

            def do_POST(self):
                if self.path != '/mcp' or not hmac.compare_digest(
                        self.headers.get('Authorization', ''), 'Bearer ' + broker.token):
                    self.send_error(403)
                    return
                origin = self.headers.get('Origin')
                if origin and origin not in {broker.url.removesuffix('/mcp'), 'http://localhost:' + str(broker.server.server_port)}:
                    self.send_error(403)
                    return
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                    if not 0 < length <= 2_000_000:
                        self.send_error(413)
                        return
                    message = json.loads(self.rfile.read(length))
                    if not isinstance(message, dict) or message.get('jsonrpc') != '2.0':
                        raise ValueError('Expected JSON-RPC 2.0 object')
                    if 'id' not in message:
                        self.send_response(202)
                        self.send_header('Content-Length', '0')
                        self.end_headers()
                        return
                    method, params = message.get('method'), message.get('params', {})
                    if method == 'initialize':
                        result = {'protocolVersion': (params.get('protocolVersion') if params.get('protocolVersion') in {'2024-11-05', '2025-03-26', '2025-06-18'} else '2025-06-18'),
                                  'capabilities': {'tools': {}},
                                  'serverInfo': {'name': 'contextbase', 'version': '1.0.0'},
                                  'instructions': 'Use the provided source and draft tools. Submission does not grant acceptance.'}
                    elif method == 'ping':
                        result = {}
                    elif method == 'tools/list':
                        result = {'tools': broker.schemas}
                    elif method == 'tools/call':
                        with broker.lock:
                            if not broker.active:
                                raise ValueError('Execution capability is revoked')
                            try:
                                value = broker.invoke(params['name'], params.get('arguments', {}))
                                result = tool_result(value)
                            except (ValueError, KeyError, RuntimeError) as exc:
                                result = {'content': [{'type': 'text', 'text': str(exc)}], 'isError': True}
                    else:
                        self.reply({'jsonrpc': '2.0', 'id': message['id'],
                                    'error': {'code': -32601, 'message': 'Unknown method'}})
                        return
                    self.reply({'jsonrpc': '2.0', 'id': message['id'], 'result': result})
                except (ValueError, TypeError, KeyError) as exc:
                    self.reply({'jsonrpc': '2.0', 'id': None,
                                'error': {'code': -32600, 'message': str(exc)}})

            def reply(self, message):
                payload = encode_message(message)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.url = 'http://127.0.0.1:' + str(self.server.server_port) + '/mcp'
        self.active = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.connection = {'url': self.url, 'token': self.token,
                           'enabled_tools': [row['name'] for row in self.schemas]}
        return self

    def __exit__(self, *args):
        with self.lock:
            self.active = False
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

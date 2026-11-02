"""Real HTTP MCP negotiation and role capability enforcement."""
import json
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from contextbase_runtime.native_mcp import Broker


def rpc(connection, method, params=None):
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}}).encode()
    request = Request(connection['url'], body, {'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream', 'Authorization': 'Bearer ' + connection['token']})
    with urlopen(request, timeout=5) as response:
        return json.load(response)


class NativeMcpTests(unittest.TestCase):
    def test_initialize_tools_and_call_over_http(self):
        schema = {'name': 'read', 'description': 'Read source', 'inputSchema': {'type': 'object'}}
        with Broker([schema], lambda name, args: {'path': args['path']}) as broker:
            result = rpc(broker.connection, 'initialize', {'protocolVersion': '2025-03-26'})['result']
            self.assertEqual('2025-03-26', result['protocolVersion'])
            self.assertEqual([schema], rpc(broker.connection, 'tools/list')['result']['tools'])
            answer = rpc(broker.connection, 'tools/call', {'name': 'read', 'arguments': {'path': 'A.cs'}})
            self.assertEqual({'path': 'A.cs'}, json.loads(answer['result']['content'][0]['text']))

    def test_missing_capability_and_cross_origin_are_rejected(self):
        with Broker([], lambda *args: {}) as broker:
            connection = {**broker.connection, 'token': 'wrong'}
            with self.assertRaises(HTTPError) as error:
                rpc(connection, 'tools/list')
            self.assertEqual(403, error.exception.code)
            body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'ping'}).encode()
            request = Request(broker.url, body, {'Authorization': 'Bearer ' + broker.token,
                              'Origin': 'https://untrusted.invalid'})
            with self.assertRaises(HTTPError) as error:
                urlopen(request, timeout=5)
            self.assertEqual(403, error.exception.code)


if __name__ == '__main__':
    unittest.main()

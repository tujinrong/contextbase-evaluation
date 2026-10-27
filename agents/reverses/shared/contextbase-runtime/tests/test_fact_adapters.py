"""Syntax facts preserve ownership and route candidates without binding targets."""
import hashlib
import unittest
from unittest.mock import patch

from contextbase_runtime import adapters


class FactAdapterTests(unittest.TestCase):
    def index(self, text, path='Fixture.cs'):
        digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
        result = adapters.index_source(path, text, source_sha256=digest)
        self.assertEqual('complete', result['status'], result['diagnostics'])
        return result

    def symbols(self, result):
        return {item['name']: item for item in result['symbols']}

    def test_csharp_call_ownership_tracks_methods_constructor_local_function_and_lambda(self):
        result = self.index('''
class Runner {
 Runner() { Initialize(); }
 void First() {
   Execute(1); void Local() { Nested(); }
   System.Action action = () => Deferred();
 }
 void Second() { Execute("text"); }
}
''')
        symbols = self.symbols(result)
        calls = {item['name']: item for item in result['calls'] if item['name'] != 'Execute'}
        for call, owner, context in [('Initialize', 'Runner', 'constructor'),
                                     ('Nested', 'Local', 'local-function'), ('Deferred', 'First', 'lambda')]:
            self.assertEqual(symbols[owner]['id'], calls[call]['callerId'])
            self.assertEqual(context, calls[call]['callerContext'])
        execute = [item for item in result['calls'] if item['name'] == 'Execute']
        self.assertEqual([symbols['First']['id'], symbols['Second']['id']], [item['callerId'] for item in execute])
        self.assertEqual([1, 1], [item['arity'] for item in execute])
        self.assertTrue(all(item['resolution'] == 'unresolved' for item in result['calls']))

    def test_top_level_and_lambda_keep_null_caller_without_claiming_handler_binding(self):
        result = self.index('''
Start();
System.Action action = () => Later();
app.MapGet("/item", Handler);
''')
        calls = {item['name']: item for item in result['calls']}
        self.assertIsNone(calls['Start']['callerId'])
        self.assertEqual('top-level', calls['Start']['callerContext'])
        self.assertIsNone(calls['Later']['callerId'])
        self.assertEqual('lambda', calls['Later']['callerContext'])
        entry = next(item for item in result['entries'] if item['kind'] == 'minimal-route')
        self.assertIsNone(entry['symbolId'])
        self.assertEqual('method-group', entry['handlerShape'])
        self.assertEqual(1, sum(item['kind'] == 'top-level-program' for item in result['entries']))

    def test_call_ids_include_path_raw_hash_range_and_kind_and_preserve_utf8_ranges(self):
        text = 'class Test { void Run() { Log("日本語"); Log("日本語"); } }'
        result = self.index(text)
        self.assertEqual(result, self.index(text))
        calls = result['calls']
        self.assertEqual(2, len({item['id'] for item in calls}))
        for item in calls:
            self.assertEqual(item['text'], text.encode()[item['startByte']:item['endByte']].decode())
            self.assertRegex(item['id'], r'^call:[0-9a-f]{64}$')
        self.assertNotEqual(calls[0]['id'], self.index(text, 'Different.cs')['calls'][0]['id'])
        self.assertNotEqual(calls[0]['id'], self.index(text + '\n')['calls'][0]['id'])

    def test_overloads_are_not_resolved_to_a_guessed_target(self):
        result = self.index('''class Calls {
 void Pick(int value) {} void Pick(string value) {}
 void Run() { Pick(1); Pick("text"); }
}''')
        self.assertEqual(2, len([s for s in result['symbols'] if s['name'] == 'Pick']))
        for call in result['calls']:
            self.assertEqual('unresolved', call['resolution'])
            self.assertNotIn('calleeId', call)
            self.assertEqual(self.symbols(result)['Run']['id'], call['callerId'])

    def test_mvc_routes_combine_templates_and_absolute_routes_override_class(self):
        result = self.index('''
[Route("api/[controller]")]
public class ResourceController : ControllerBase {
 [HttpGet("{id}")] public object Find(int id) => NotFound();
 [HttpPost, Route("~/submit")] public object Save() { return Store(); }
 [HttpDelete("/remove/{id}")] public void Remove(int id) { Delete(id); }
 [HttpPut] public void Update() { Persist(); }
 public void Helper() { Work(); }
 [HttpGet("private")] private void Hidden() { Work(); }
}
class Service { [HttpGet("accidental")] public void Method() {} }
''')
        entries = {item['name']: item for item in result['entries'] if item['kind'] == 'mvc-action'}
        self.assertEqual({'Find', 'Save', 'Remove', 'Update'}, set(entries))
        self.assertEqual('api/[controller]/{id}', entries['Find']['route'])
        self.assertEqual(2, entries['Find']['evidence'][0]['startLine'])
        self.assertEqual('/submit', entries['Save']['route'])
        self.assertEqual('/remove/{id}', entries['Remove']['route'])
        self.assertEqual('api/[controller]', entries['Update']['route'])
        self.assertEqual('expression-not-found', entries['Find']['handlerShape'])
        self.assertNotIn('disabled', entries['Find'])
        self.assertEqual(self.symbols(result)['Find']['id'], entries['Find']['symbolId'])
        self.assertTrue(all(item['resolution'] == 'unresolved' for item in entries.values()))

    def test_dynamic_mvc_templates_remain_unresolved_and_absolute_literal_still_overrides(self):
        result = self.index('''
[Route(RoutePrefix)] public class DynamicController {
 [HttpGet("items")] public void List() {}
 [HttpPost("/absolute")] public void Save() {}
 [HttpDelete(RouteSuffix)] public void Remove() {}
}
''')
        entries = {item['name']: item for item in result['entries']}
        for name in ('List', 'Remove'):
            self.assertIsNone(entries[name]['route'])
            self.assertEqual('unresolved', entries[name]['templateStatus'])
        self.assertEqual('/absolute', entries['Save']['route'])
        self.assertEqual('literal', entries['Save']['templateStatus'])

    def test_minimal_registrations_extract_verbs_and_do_not_count_di_or_middleware(self):
        result = self.index('''
services.AddScoped<IService, Service>();
app.UseRouting(); app.MapControllers();
app.MapGet("/read", () => NotFound());
app.MapPost(RouteName, Handler);
app.MapMethods("/multi", new[] { "GET", "POST" }, Handler);
app.MapMethods("/dynamic", AllowedVerbs, Handler);
''')
        entries = [item for item in result['entries'] if item['kind'] == 'minimal-route']
        self.assertEqual(5, len(entries))
        self.assertEqual(['MapGet', 'MapPost', 'MapMethods', 'MapMethods', 'MapMethods'],
                         [item['name'] for item in entries])
        self.assertEqual(['GET', 'POST', 'GET', 'POST', None], [item['verb'] for item in entries])
        self.assertEqual('expression-not-found', entries[0]['handlerShape'])
        self.assertIsNone(entries[1]['route'])
        self.assertEqual('unresolved', entries[1]['templateStatus'])
        self.assertEqual(5, len({item['id'] for item in entries}))
        self.assertTrue(all(item['symbolId'] is None for item in entries))

    def test_explicit_main_candidate_and_verbatim_route_literals(self):
        result = self.index('''class Program {
 static void Main(string[] args) { Launch(); }
 void Main(int ignored) { Helper(); }
}
[Route(@"api/items")] class VerbatimController {
 [HttpGet(@"list")] public void List() {}
}''')
        mains = [item for item in result['entries'] if item['kind'] == 'program-main']
        self.assertEqual(1, len(mains))
        self.assertEqual('Main', mains[0]['name'])
        self.assertFalse(any(item['kind'] == 'top-level-program' for item in result['entries']))
        route = next(item for item in result['entries'] if item['kind'] == 'mvc-action')
        self.assertEqual('api/items/list', route['route'])

    def test_java_calls_have_constructor_method_and_lambda_owners(self):
        result = self.index('''class Example {
 Example() { setup(); }
 void first() { execute(1); Runnable r = () -> deferred(); }
 void second() { execute("x"); new Item(); }
}''', 'Example.java')
        symbols = self.symbols(result)
        calls = result['calls']
        self.assertEqual(symbols['Example']['id'], next(c for c in calls if c['name'] == 'setup')['callerId'])
        deferred = next(c for c in calls if c['name'] == 'deferred')
        self.assertEqual(symbols['first']['id'], deferred['callerId'])
        self.assertEqual('lambda', deferred['callerContext'])
        construction = next(c for c in calls if c['kind'] == 'construction')
        self.assertEqual(symbols['second']['id'], construction['callerId'])
        self.assertEqual(0, construction['arity'])
        self.assertEqual([], result['entries'])

    def test_limits_failures_and_unsupported_languages_never_expose_partial_entries(self):
        text = 'app.MapGet("/entry", Handler);'
        digest = hashlib.sha256(text.encode()).hexdigest()
        with patch.object(adapters, 'MAX_NODES', 3):
            limited = adapters.index_source('Program.cs', text, source_sha256=digest)
        self.assertEqual('limit-exceeded', limited['status'])
        self.assertEqual([], limited['entries'])
        self.assertEqual([], limited['calls'])
        failed = adapters.index_source('Program.cs', text, source_sha256='not-a-hash')
        self.assertEqual('failed', failed['status'])
        self.assertEqual([], failed['entries'])
        self.assertEqual([], adapters.index_source('readme.txt', text, source_sha256=digest)['entries'])


if __name__ == '__main__':
    unittest.main()

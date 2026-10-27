"""Business catalog representation and host review gates with synthetic answers.

These tests prove that the contract can represent the agreed distinctions and
that a failed independent review blocks adoption. They do not evaluate an LLM's
ability to infer those distinctions from source or prove the prompt effective.
No input program is executed.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_discovery import DiscoveryAgent
from contextbase_runtime.controller import AcceptanceError
from test_independent_agents import add_fact_usage, request, simulated_answer


class UserFunctionCatalogTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='user-function-catalog-', dir=home)
        self.root = Path(self.temporary.name)
        source = self.root / 'source'
        source.mkdir()
        (source / 'Portal.cs').write_bytes(b'''class Portal {
 public bool LoginPage(string user) { return LocalLogin(user); }
 bool LocalLogin(string user) { return user.Length > 0; }
 public string SharedNav() { return "Home | Help"; }
 public object CustomerWorkbench(int[] waitingDays) { return new { Assigned = waitingDays.Length, Overdue = System.Linq.Enumerable.Count(waitingDays, day => day > 5) }; }
 public string CustomerSearch(string query) { return query; }
 public string DetailsPage(string selected) { return selected; }
 public string EditPopup(string selected) { return selected; }
 public string RoleMenu(bool viewer) { return viewer ? "Search" : "Search | New"; }
}
''')
        req = request()
        for item in req['goal']['requirements']:
            item['scope'] = 'portal'
        req['goal']['question'] = 'Identify user tasks and distinguish shared implementation and subordinate screens.'
        self.agent = DiscoveryAgent.create(source, self.root / 'work', req)
        self.contexts = []
        self.scenario = 'login'
        self.negative = False

    def tearDown(self):
        self.temporary.cleanup()

    def main_classification(self, entry, *, area, purpose, outcome):
        return {'category': 'main', 'scope': 'portal', 'area': area, 'actors': ['利用者'],
                'businessObject': '利用対象', 'purpose': purpose, 'trigger': '利用者が画面を開いて操作する',
                'outcome': outcome, 'rationale': 'An independent user purpose and observable outcome.',
                'alternative': 'Considered a shared component or subordinate operation.', 'entryRefs': [entry]}

    def common_classification(self, consumers):
        return {'category': 'common', 'scope': 'portal', 'responsibility': 'Reusable implementation shared by user tasks.',
                'consumers': consumers, 'rationale': 'An implementation capability consumed by another task.',
                'alternative': 'Considered an independent user task.'}

    def operation_classification(self, entry):
        return {'category': 'operation', 'scope': 'portal', 'parent': 'search.main',
                'purpose': 'Inspect or edit the selected search result.', 'useContext': 'Within the customer search task.',
                'outcome': 'The selected result is inspected or prepared.',
                'rationale': 'A subordinate step without a separate user goal in this synthetic scenario.',
                'alternative': 'Considered an independent task if separate business context were established.',
                'entryRefs': [entry]}

    def records(self, context):
        material = context['inventory']['files'][0]
        def record(key, kind, line, classification=None):
            return {'key': key, 'ownerRequirement': 'catalog', 'kind': kind, 'name': key,
                'statement': 'Synthetic source-backed catalog role for ' + key, 'basis': 'observed-source',
                'evidence': [{'path': material['path'], 'sha256': material['sha256'],
                              'startLine': line, 'endLine': line}],
                'dependsOn': [], 'classification': classification}
        if self.scenario == 'login':
            main = record('login.main', 'function', 2, self.main_classification(
                'login.entry', area='システム認証', purpose='ログインする', outcome='認証結果を確認し利用を開始できる'))
            if self.negative:
                main.update(kind='common', classification=self.common_classification(['login.entry']))
            return [record('login.entry', 'entry', 2), main,
                    record('local-login.common', 'common', 3, self.common_classification(['login.main']))]
        if self.scenario == 'workbench':
            main = record('workbench.main', 'function', 5, self.main_classification(
                'workbench.entry', area='担当案件照会', purpose='担当案件の件数と滞留状況を把握する',
                outcome='担当件数と期限超過件数を確認できる'))
            if self.negative:
                main.update(kind='common', classification=self.common_classification(['workbench.entry']))
            return [record('nav.entry', 'entry', 4), record('workbench.entry', 'entry', 5), main,
                    record('nav.common', 'common', 4, self.common_classification(['workbench.main']))]
        if self.scenario == 'navigation':
            navigation = record('navigation.menu', 'common', 9,
                self.common_classification(['navigation.entry']))
            if self.negative:
                navigation.update(kind='function', classification=self.main_classification(
                    'navigation.entry', area='システム操作選択', purpose='役割に応じた次の機能を選ぶ',
                    outcome='選択した機能のページへ移動する'))
            return [record('navigation.entry', 'entry', 9), navigation]
        records = [record('search.entry', 'entry', 6), record('search.main', 'function', 6,
            self.main_classification('search.entry', area='顧客業務', purpose='顧客を検索して確認する',
                                     outcome='対象顧客と必要な情報を確認できる'))]
        for key, line in (('details', 7), ('popup', 8)):
            classification = self.operation_classification(key + '.entry')
            kind = 'operation'
            if self.negative:
                classification = self.main_classification(key + '.entry', area='顧客業務',
                    purpose='Open the subordinate screen.', outcome='The subordinate screen is displayed.')
                kind = 'function'
            records += [record(key + '.entry', 'entry', line), record(key + '.operation', kind, line, classification)]
        return records

    def provider(self, workspace, directory, prompt, schema, timeout):
        context = json.loads(prompt[prompt.index('{"request":'):])
        self.contexts.append(context)
        answer = simulated_answer(context)
        if context['task']['operation'] == 'extract':
            answer['records'] = self.records(context)
            answer['coverage'][0].update(recordKeys=[record['key'] for record in answer['records']],
                                         evidence=deepcopy(answer['records'][0]['evidence']))
        elif self.negative:
            if self.scenario == 'workbench':
                check = next(item for item in answer['classificationChecks'] if item['key'] == 'workbench.main')
                check.update(status='fail', reason='The read-only case summary has an independent information outcome beyond navigation.')
            elif self.scenario == 'navigation':
                check = next(item for item in answer['classificationChecks'] if item['key'] == 'navigation.menu')
                check.update(status='fail', reason='Role-filtered destination links alone do not establish an independent user result.')
            else:
                answer['scopeChecks'][0].update(status='fail', reason=(
                    'Independent login was omitted from main functions.' if self.scenario == 'login' else
                    'Subordinate detail and popup screens were counted as separate main functions without independent goals.'))
        add_fact_usage(context, answer)
        return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': answer}

    def run_agent(self):
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            return self.agent.run(inline_sources=True)

    def assert_rejected_by_review(self):
        self.assertEqual('needs-investigation', self.run_agent()['status'])
        state = self.agent.session._state()
        self.assertEqual(1, len(state['candidates']), 'The representation passed mechanical candidate validation')
        self.assertEqual(1, len(state['verifications']))
        self.assertEqual([], state['acceptedRequirements'])
        with self.assertRaises(AcceptanceError):
            self.agent.session.adopt(state['candidates'][0])
        self.assertNotEqual(self.contexts[0]['task']['contextId'], self.contexts[1]['task']['contextId'])

    def test_independent_login_main_coexists_with_shared_local_login_implementation(self):
        self.assertEqual('complete', self.run_agent()['status'])
        records = self.agent.status()['records']
        self.assertEqual('function', records['login.main']['kind'])
        self.assertEqual('main', records['login.main']['classification']['category'])
        self.assertEqual('システム認証', records['login.main']['classification']['area'])
        self.assertEqual(['login.main'], records['local-login.common']['classification']['consumers'])
        self.assertEqual('common', records['local-login.common']['kind'])

    def test_shared_navigation_and_read_only_workbench_summary_have_distinct_representations(self):
        self.scenario = 'workbench'
        self.assertEqual('complete', self.run_agent()['status'])
        records = self.agent.status()['records']
        self.assertEqual('main', records['workbench.main']['classification']['category'])
        self.assertEqual('function', records['workbench.main']['kind'])
        self.assertEqual('common', records['nav.common']['classification']['category'])
        self.assertEqual(['workbench.main'], records['nav.common']['classification']['consumers'])
        self.assertFalse(any(record['kind'] == 'data' for record in records.values()),
                         'A read-only information outcome does not require a database-write record')

    def test_role_filtered_destination_links_remain_common_navigation_with_an_entry(self):
        self.scenario = 'navigation'
        self.assertEqual('complete', self.run_agent()['status'])
        records = self.agent.status()['records']
        self.assertEqual('common', records['navigation.menu']['kind'])
        self.assertEqual(['navigation.entry'], records['navigation.menu']['classification']['consumers'])
        self.assertEqual('entry', records['navigation.entry']['kind'])
        self.assertFalse(any(record['kind'] == 'function' for record in records.values()))

    def test_details_and_popup_can_remain_operations_under_a_single_user_task(self):
        self.scenario = 'screens'
        self.assertEqual('complete', self.run_agent()['status'])
        records = self.agent.status()['records']
        for key in ('details', 'popup'):
            self.assertEqual('operation', records[key + '.operation']['kind'])
            self.assertEqual('search.main', records[key + '.operation']['classification']['parent'])
            self.assertEqual([key + '.entry'], records[key + '.operation']['classification']['entryRefs'])
        self.assertEqual('function', records['search.main']['kind'])

    def test_review_can_reject_hiding_independent_login_only_in_common_and_entry(self):
        self.negative = True
        self.assert_rejected_by_review()

    def test_review_can_reject_hiding_an_independent_read_only_workbench_as_common(self):
        self.scenario = 'workbench'
        self.negative = True
        self.assert_rejected_by_review()

    def test_review_can_reject_promoting_role_filtered_navigation_to_a_main_function(self):
        self.scenario = 'navigation'
        self.negative = True
        self.assert_rejected_by_review()

    def test_review_can_reject_counting_every_subordinate_screen_as_a_main_function(self):
        self.scenario = 'screens'
        self.negative = True
        self.assert_rejected_by_review()


if __name__ == '__main__':
    unittest.main()

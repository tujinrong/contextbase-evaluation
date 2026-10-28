"""Origin-preserving candidate pages, never original-source or fact evidence."""
from copy import deepcopy
import json
import unittest

from contextbase_runtime import contracts as c, incremental
from contextbase_runtime.material_window import collect_materials


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


class CandidateMaterialWindowTests(unittest.TestCase):
    def setUp(self):
        same = {'statement': 'same text 日本語 😀\n' + 'x' * 90}
        self.materials = {'records': {'A': deepcopy(same), 'B': deepcopy(same)},
                          'units': {'A': deepcopy(same)}, 'unknowns': {}, 'factUsage': {}, 'feedback': {}}
        self.task = {'id': 'child-task', 'contextId': 'child-context', 'snapshotId': 'a' * 64}

    def page(self, key='A', *, collection='records', offset=0, limit=12000):
        request = {'operation': 'material', 'collection': collection, 'key': key,
                   'offset': offset, 'limit': limit}
        return {'request': request, 'reply': incremental._material_reply(request, self.materials, self.task)}

    def listing(self, *, collection='records', offset=0, limit=100):
        request = {'operation': 'listing', 'collection': collection, 'offset': offset, 'limit': limit}
        return {'request': request, 'reply': incremental._material_reply(request, self.materials, self.task)}

    def collect(self, latest=(), prior=()):
        return collect_materials(list(latest), list(prior), self.materials)

    def test_A_then_B_remains_jointly_visible_with_exact_origin(self):
        first, second = self.page('A'), self.page('B')
        visible, prior = self.collect([second], [first])
        self.assertEqual(['B'], [row['key'] for row in visible])
        self.assertEqual(['A'], [row['key'] for row in prior])
        for row, pair in ((visible[0], second), (prior[0], first)):
            self.assertEqual('candidate-material', row['kind'])
            self.assertEqual(encoded(self.materials[row['collection']][row['key']]), row['bodyText'])
            self.assertEqual(c.digest(self.materials[row['collection']][row['key']]), row['sha256'])
            self.assertEqual(pair['reply']['replySha256'], row['origin']['replySha256'])
            self.assertEqual(self.task['id'], row['origin']['taskId'])
            self.assertEqual(0, row['offset'])
            self.assertEqual(len(row['bodyText']), row['totalChars'])

    def test_latest_overlap_subtracts_exact_character_ranges_from_prior(self):
        old = self.page(offset=0, limit=40)
        latest = self.page(offset=10, limit=10)
        visible, prior = self.collect([latest], [old])
        whole = encoded(self.materials['records']['A'])
        self.assertEqual([(10, whole[10:20])], [(row['offset'], row['bodyText']) for row in visible])
        self.assertEqual([(0, whole[:10]), (20, whole[20:40])],
                         [(row['offset'], row['bodyText']) for row in prior])
        for row in prior:
            self.assertEqual(old['reply']['replySha256'], row['origin']['replySha256'])
            self.assertEqual((0, 40), (row['origin']['deliveredOffset'], row['origin']['deliveredEndOffset']))

    def test_newer_prior_page_wins_and_old_page_only_supplies_remaining_intervals(self):
        old = self.page(offset=0, limit=30)
        newer = self.page(offset=10, limit=10)
        visible, prior = self.collect([], [old, newer])
        self.assertEqual([], visible)
        self.assertEqual([10, 0, 20], [row['offset'] for row in prior])
        self.assertEqual(newer['reply']['replySha256'], prior[0]['origin']['replySha256'])
        self.assertEqual([10, 10, 10], [len(row['bodyText']) for row in prior])

    def test_repeated_latest_and_prior_deliveries_are_not_duplicated(self):
        page = self.page(offset=4, limit=20)
        visible, prior = self.collect([page, deepcopy(page)], [page, deepcopy(page)])
        self.assertEqual(1, len(visible))
        self.assertEqual([], prior)

    def test_identical_text_different_object_and_collection_stays_distinct(self):
        first = self.page('A')
        other_key = self.page('B')
        other_collection = self.page('A', collection='units')
        visible, prior = self.collect([other_collection], [first, other_key])
        self.assertEqual({('records', 'A'), ('records', 'B'), ('units', 'A')},
                         {(row['collection'], row['key']) for row in visible + prior})
        self.assertEqual(1, len({row['bodyText'] for row in visible + prior}))

    def test_stale_body_and_summary_versions_are_discarded(self):
        old_page, old_listing = self.page('A'), self.listing(limit=1)
        self.materials['records']['A']['statement'] = 'changed version'
        current = self.page('A')
        visible, prior = self.collect([current], [old_page, old_listing])
        self.assertEqual([current['reply']['result']['sha256']], [row['sha256'] for row in visible])
        self.assertEqual([], prior)

    def test_deleted_objects_and_collections_have_no_retained_pages(self):
        old = self.page('A')
        other = self.page('A', collection='units')
        del self.materials['records']['A']
        del self.materials['units']
        self.assertEqual(([], []), self.collect([old], [other]))

    def test_listing_summaries_are_distinct_from_body_and_keep_listing_origin(self):
        listing, page = self.listing(limit=1), self.page('A')
        visible, prior = self.collect([page], [listing])
        self.assertEqual('candidate-material', visible[0]['kind'])
        self.assertEqual('candidate-summary', prior[0]['kind'])
        self.assertEqual(encoded(listing['reply']['result']['items'][0]), prior[0]['bodyText'])
        self.assertEqual(0, prior[0]['origin']['listingIndex'])
        self.assertEqual(listing['reply']['replySha256'], prior[0]['origin']['replySha256'])

    def test_repeated_listing_with_different_limits_keeps_one_summary_per_object(self):
        first = self.listing(limit=2)
        repeated = self.listing(limit=1)
        visible, prior = self.collect([repeated], [first])
        self.assertEqual(['A'], [row['key'] for row in visible])
        self.assertEqual(['B'], [row['key'] for row in prior])

    def test_original_read_query_and_inventory_never_enter_candidate_materials(self):
        pairs = [{'request': {'operation': operation}, 'reply': {'result': {
            'sourceText': 'source', 'facts': [{'id': 'fact-1'}], 'evidence': {'path': 'source.cs'}}}}
            for operation in ('read', 'query', 'inventory', 'search')]
        self.assertEqual(([], []), self.collect(pairs, pairs))

    def test_empty_listing_and_empty_body_are_not_retained(self):
        self.assertEqual(([], []), self.collect([self.listing(offset=100)], [self.page(offset=10000)]))

    def test_collection_does_not_modify_receipts_or_current_objects(self):
        latest, prior = [self.page('B')], [self.page('A'), self.listing()]
        originals = deepcopy((latest, prior, self.materials))
        self.collect(latest, prior)
        self.assertEqual(originals, (latest, prior, self.materials))

    def test_reply_hash_damage_is_rejected(self):
        pair = self.page()
        pair['reply']['result']['bodyText'] = 'changed bytes'
        with self.assertRaises(ValueError):
            self.collect([pair])

    def test_resealed_wrong_body_cannot_claim_current_object_sha(self):
        pair = self.page()
        pair['reply']['result']['bodyText'] = '!' + pair['reply']['result']['bodyText'][1:]
        pair['reply']['resultSha256'] = c.digest(pair['reply']['result'])
        pair['reply']['replySha256'] = c.digest({key: value for key, value in pair['reply'].items()
                                               if key != 'replySha256'})
        with self.assertRaises(ValueError):
            self.collect([pair])

    def test_original_delivery_range_and_request_binding_are_checked(self):
        pair = self.page(offset=0, limit=20)
        pair['request']['offset'] = 1
        with self.assertRaises(ValueError):
            self.collect([pair])


if __name__ == '__main__':
    unittest.main()

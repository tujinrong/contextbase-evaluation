"""A lookup must not borrow the matching rule of an unrelated collection."""
import unittest
from contextbase.detail.semantics import operation_summary


class PredicateScopeTests(unittest.TestCase):
    def test_reference_lookup_does_not_borrow_record_key(self):
        effect={'operation':'read','expression':'eras.FirstOrDefault(era => era.Name.Equals(code)).Clone()'}
        event={'data_rules':[{'target':'レコードの照合条件','method':'MatchesRecordKey','rule':'kana and phone'}]}
        text=operation_summary(effect,event,{})
        self.assertNotIn('下記の照合規則',text)
        self.assertIn('era.Name.Equals(code)',text)
        self.assertNotIn('.Clone()',text)

    def test_lookup_links_only_its_referenced_matcher(self):
        effect={'operation':'read','expression':'rows.FirstOrDefault(row => MatchCode(row, code))?.Clone()'}
        event={'data_rules':[{'target':'レコードの照合条件','method':'MatchCode','rule':'source-derived match'}]}
        text=operation_summary(effect,event,{})
        self.assertIn('下記の照合規則',text)
        self.assertIn('複製',text)


if __name__=='__main__':unittest.main()

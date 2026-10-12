import unittest
from mcterpgen.scan import vue
from mcterpgen.ui_state import separate,describe

class UIStateTests(unittest.TestCase):
    def analyze(self,text):
        record=vue(text,'x.vue');screen={'path':'x.vue',**record}
        data={'records':{'x.vue':record},'screens':[screen],'texts':{'x.vue':text},'inventory':[{'path':'x.vue'}],'stats':{}}
        separate(data);return data
    def test_visible_model_is_state_not_input(self):
        d=self.analyze('<template><EditPage v-model:visible="editVisible"/><a-input v-model="name"/></template>')
        self.assertEqual([i['binding'] for i in d['screens'][0]['items']],['name'])
        self.assertEqual(d['screens'][0]['items'][0]['order'],1)
        self.assertEqual(d['screens'][0]['state_bindings'][0]['value'],'editVisible')
    def test_business_value_remains_with_open_model(self):
        d=self.analyze('<template><a-select v-model:open="opened" v-model:value="value"/></template>')
        self.assertEqual(len(d['screens'][0]['items']),1)
        self.assertEqual(d['screens'][0]['items'][0]['binding'],'value')
    def test_state_documented_separately(self):
        d=self.analyze('<template><Modal v-model:visible="show"/></template>')
        text=describe('## 2. 項目一覧',{'screens':d['screens']})
        self.assertIn('業務入力項目数には含めない',text);self.assertIn('show',text)

if __name__=='__main__':unittest.main()

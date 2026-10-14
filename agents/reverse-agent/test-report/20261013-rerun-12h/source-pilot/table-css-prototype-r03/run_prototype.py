"""Fresh r03: generic eligible last-column minimum, no role/body inference."""
from pathlib import Path
import importlib.util

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'table-css-prototype-r02/run_prototype.py'
spec=importlib.util.spec_from_file_location('table_css_r02_technical_functions',BASE)
prior=importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
probe=prior.probe
probe.HERE=HERE
probe.CSS += probe.SELECTOR+' th:last-child,'+probe.SELECTOR+' td:last-child{min-width:20em}'
probe.FIXTURE=probe.FIXTURE.replace(probe.EMBEDDED,'')
probe.FIXTURE += prior.original_table(['分類ID','物理ID','logical','kind','size','required','default','source','description'],
    [['SYNTHETIC_CATEGORY_WITH_LONG_NAME','`sample_atomic_identifier_abcdefghijklmno`','日本語項目',
      'unique_synthetic_datatype','1234567890','Y','NULL','FixtureOnly:3','非No先頭の9列合成表。' * 20]])
probe.FIXTURE += probe.EMBEDDED

if __name__=='__main__':
    probe.main()

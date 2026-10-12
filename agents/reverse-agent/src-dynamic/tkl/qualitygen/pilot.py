"""Pilot facade: isolated specification inputs and fresh-result finalization."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from overviewgen.core import load,save
from overviewgen.publish import table
from .pilot_base import json_contract,generate_only,FEATURE_METHODS
from . import pilot_base


def normalize_fixtures(base:Path):
    """Mock values match the reference model; physical DB metadata is still unknown."""
    for name,literal in [('Program.vb','1'),('EventHarness.vb','2')]:
        path=base/'harness'/name
        text=path.read_text(encoding='utf-8')
        source='{"sell_kbn",'+literal+'}'
        target='{"sell_kbn",CShort('+literal+')}'
        if source not in text and target not in text:
            raise ValueError('Expected fixture value not found: '+name)
        save(path,text.replace(source,target))
    save(base/'harness/fixture-contract.json',{
        'sales_kind':'System.Int16 boxed value, matching original nullable Int16 property',
        'fixedprice_discount':'System.Int32',
        'rate_injected_into_order_model':'System.Single',
        'physical_database_types_confirmed':False,
        'reason':'The earlier Int32 mock failed at nullable Int16 unboxing before price assignment. This fixture correction does not modify the original method body.',
        'not_verified':['All provider scalar type combinations','Actual Npgsql result metadata','WPF binding conversion']})
    readme=base/'README.md'
    text=readme.read_text(encoding='utf-8')
    old='dotnet run --project pilot/TKL-011/Pilot.vbproj --configuration Release -- report/pilot/native-result.json\npython -m qualitygen --finalize-pilot'
    text=text.replace(old,'python -m qualitygen.native_checks')
    if '## 評価用データの型' not in text:
        text+='\n## 評価用データの型\n\n売上区分は原本の受取プロパティに合わせた16ビット整数を渡す。DBの物理列型が確認できたという意味ではない。値だけが同じでも、外部依存の代替が異なる型を返すと原本と異なる例外になる。fixture-contract.jsonに適用範囲を記録する。\n'
    save(readme,text)


def prepare(root:Path,data):
    assessment=pilot_base.prepare(root,data)
    from .pilot_extension import prepare_extension
    prepare_extension(root,data,root/'pilot/TKL-011')
    normalize_fixtures(root/'pilot/TKL-011')
    save(root/'report/pilot/Pilot総合検証.md','# Pilot総合検証\n\n今回の仕様・比較ソースを生成した。ネイティブ比較は未実行。過去の一致を今回の合格とみなさない。\n')
    save(root/'report/pilot/execution-binding.json',{'status':'pending','run_id':None})
    return load(root/'report/pilot/preparation.json',assessment)


def finalize(root:Path):
    from .native_checks import validate
    result=validate(root)
    pilot_base.finalize(root)
    path=root/'report/pilot/Pilot総合検証.md'
    rows=Counter(r['family'] for r in result['results']);passed=Counter(r['family'] for r in result['results'] if r['passed'])
    text=path.read_text(encoding='utf-8')+'\n## 5. 追加したイベント評価\n\n'
    text+='値引率・値引額・計算・マイナス指定・書籍選択・価格取得・郵便番号の7イベントを追加した。直接宣言19イベント中10イベントの選択した本体が対象。実際のWPF発火・フォーカス・DB動作は含めない。\n\n'
    text+=table(['比較群','ケース','一致'],[[name,rows[name],passed[name]] for name in sorted(rows)])
    text+='\n原本と再実装に与える価格・住所は試験用である。保持値と計算引数の型、未設定と0、更新する項目と維持する項目、共通処理の呼出回数を比較する。小数率はモデルへの注入であり、UIの入力許容を保証しない。\n\n'
    text+='実行IDと仕様・参照実装・再実装・テスト・プロジェクト設定のハッシュが一致した結果のみ確定する。比較対象・ケース数はharness/test-plan.jsonと照合する。負の対照試験はnative-mutations.jsonを参照する。\n'
    save(path,text)
    return result

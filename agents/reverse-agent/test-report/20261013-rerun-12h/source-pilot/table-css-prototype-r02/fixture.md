# Trusted synthetic CSS fixture

| 単独欄 |
|---|
| OneColumnStableIdentifier 日本語説明 |

| 識別子 | 説明 |
|---|---|
| TwoColumnStableIdentifier | 二列表の説明。二列表の説明。二列表の説明。二列表の説明。二列表の説明。二列表の説明。二列表の説明。二列表の説明。 |

| 分類ID | パラメータ | 説明 |
|---|---|---|
| SYNTHETIC_CATEGORY_WITH_LONG_NAME | sample_parameter_identifier_abcdefghijklmnopqrstuvwxyz | 日本語説明を自然に折り返す。日本語説明を自然に折り返す。日本語説明を自然に折り返す。日本語説明を自然に折り返す。日本語説明を自然に折り返す。日本語説明を自然に折り返す。日本語説明を自然に折り返す。日本語説明を自然に折り返す。日本語説明を自然に折り返す。日本語説明を自然に折り返す。日本語説明を自然に折り返す。日本語説明を自然に折り返す。日本語説明を自然に折り返す。日本語説明を自然に折り返す。日本語説明を自然に折り返す。日本語説明を自然に折り返す。 |

| 分類ID | 列A | 列B | 列C | 列D | 説明 |
|---|---|---|---|---|---|
| SYNTHETIC_CATEGORY_WITH_LONG_NAME | sample_atomic_identifier_abcdefghijklmno | unique_synthetic_datatype | 123456789012345678901234567890123456789012345678901234567890 | PLAIN-LEGAL-WRAP-TOKEN | 長い日本語の合成説明。長い日本語の合成説明。長い日本語の合成説明。長い日本語の合成説明。長い日本語の合成説明。長い日本語の合成説明。長い日本語の合成説明。長い日本語の合成説明。長い日本語の合成説明。長い日本語の合成説明。長い日本語の合成説明。長い日本語の合成説明。長い日本語の合成説明。長い日本語の合成説明。 |

| No | physical_id | logical | kind | size | required | default | source | description |
|---|---|---|---|---|---|---|---|---|
| 1 | `sample_atomic_identifier_abcdefghijklmno` | 日本語項目 | unique_synthetic_datatype | 1234567890 | Y | NULL | FixtureOnly:1 | 日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。 |
| 2 | SampleAtomicIdentifierWithManyCharactersWithoutBreaks | 空欄例 | text |  | N |  | FixtureOnly:2 | 説明の後に `SyntheticInlineCode` を保持する。 |

| No | group | item | type | io | binding | choice | required | format | description |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SyntheticGroup | SyntheticItem | text | I | sample_atomic_identifier_abcdefghijklmno | SyntheticCandidate | Y | 99999 | 日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。日本語説明。 |

| 分類ID | code value | description |
|---|---|---|
| CODE_1 | `SYNTHETIC-STATUS-0123456789` | 合成codeの文字と値を保持する。 |
| CODE_2 | `-12345678901234567890.25` | 合成codeの文字と値を保持する。 |
| CODE_3 | `12345678901234567890.012345` | 合成codeの文字と値を保持する。 |
| CODE_4 | `2026-10-13T14:45:00+09:00` | 合成codeの文字と値を保持する。 |
| CODE_5 | `CODE VALUE WITH SPACES` | 合成codeの文字と値を保持する。 |

| protected one-column |
|---|
| `OneColumnCodeWithManyCharactersWithoutBreaksAndNoStyleChange` |

| protected key | protected code |
|---|---|
| TwoColumnProtected | `TwoColumnCodeWithManyCharactersWithoutBreaksAndNoStyleChange` |

<style>#embedded{width:320px;border:2px solid #345;padding:8px;font-size:15px}#embedded table{width:300px;border-collapse:collapse}#embedded td{border:1px solid #789;padding:4px}#embedded input{width:120px}#embedded textarea{width:140px;height:40px}</style><div id="embedded"><h3>独立合成レイアウト</h3><table><tbody><tr><td>固定欄</td><td>ScreenAtomicIdentifier</td></tr><tr><td><input disabled value="fixture"></td><td><textarea disabled>合成表示</textarea></td></tr></tbody></table></div>
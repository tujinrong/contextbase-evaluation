# Latest local build and path regression

Status: PASSED. Final application: ../app/; intermediate compiler/package/runtime data: ../../.tmp/.

Reported assertion counts: {"core": 138, "fixture": 39, "native-ui": 245, "framework": 23}.

See results.json and the fixed command logs. These checks do not execute a real business database, deploy the application, or establish formal acceptance. NuGet audit: ENABLED.

2026-10-25 regeneration: native-ui uses real forms with fictional method-local fixture at 96 DPI (1180/1280 x 610), including all 10000 rows and stale/pending/scroll state paths. This is not real database or manual acceptance. Path guards: 21; own input/DDL/source checks: 177. Earlier unrelated result files were moved to .tmp/legacy-work. See ../generation/generation.md for changed source and limits. PackageReference is unchanged; --locked-mode does not imply a persistent dependency lock file is present.

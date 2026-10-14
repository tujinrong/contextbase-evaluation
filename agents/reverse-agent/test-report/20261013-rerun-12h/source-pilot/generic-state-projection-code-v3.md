# Generic projection code handoff

This file contains five generic gate definitions and generic boundary/task strings only. It contains no source-only manuscript, facts, source excerpts, history, evaluation material, or current-job paths. Importing it performs no job or provider call.

The receiving clean role must create its own helper and set its already authorized snapshot mode, exact manifest SHA, canonical root/path allowlist, fresh job root, runtime receipt allowlist, and explicit parent document SHA pins. Keep source-only and assisted roots separate. Do not infer authorization from an input mode string or automatically discover other modes.

Use the existing frozen contextbase.ai workflow for the AI call and raw answer preservation. Verify all runtime files against the receipt and actual import path; verify manifest/original allowed input hashes and all canonical bytes before and after. Canonical paths require capsule.safe_path, a regular .md within the role root, and exact canonical relative-name matching. Fix the helper's own code SHA before and after invocation.

Use the state JSON fields id, title, canonicalLocations, references, projectionAssumptions, requiresCanonicalRevision, canonicalRevisionReason, html. A location is {documentSha256, heading, headingLine, startLine, endLine}. Require one exact pinned document SHA and an existing heading section range. Reject duplicate state IDs, unexpected bound manuscript SHA sets, HTML on a requiresCanonicalRevision state, and renderable HTML lacking source references or canonical locations. Validate references through workflow.references_valid against the receiving role's manifest.

The five transferred gates are byte-identical function/class excerpts of the inspected helper. The generic boundary/task strings are role-neutral control instructions and include no business answer. The receiving helper must be independently reviewed after mode/path adaptation. Do not import the originating executable helper because its module top level starts argparse and has fixed role paths.

These gates do not prove complete HTML inertness or semantic fidelity. Use the strict renderer sanitizer, an independent source/canonical meaning review, and native-size state visual inspection. Retain projectionMeaningVerified=false, independentSemanticReviewRequired=true, strictRendererSanitizerRequired=true, htmlGateIsNotFullInertnessProof=true until the respective checks finish. Keep the projection separate from the canonical specification and do not use it to repair a missing canonical fact.

Version 2 adds strip().casefold() normalization to http-equiv refresh rejection. The padded refresh negative case was accepted by version 1 and is rejected by version 2. No provider or browser was used by the gate probe; complete inertness remains unproven.

Version 3 adds the generic validate_projection_state_fields gate. Canonical omissions require empty HTML and a nonblank reason; nonrevision states require nonblank AI-authored HTML. The caller must additionally pin the exact manifest hash and authorized source root before input reads, pin the complete runtime receipt hash and destination, and compare the receipt hash after the AI call. These root/mode/hash values belong to the receiving role and are not embedded in the generic code.

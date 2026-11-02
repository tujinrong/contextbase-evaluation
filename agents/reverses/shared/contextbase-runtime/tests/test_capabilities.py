"""Selected Skills are frozen, staged privately and checked before execution."""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from contextbase_runtime.capabilities import (
    MAX_BUNDLE_BYTES, normalize_capabilities, stage_skills, validate_capabilities,
)


class CapabilityTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='capabilities-', dir=home)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.skill = self.make_skill('selected')

    def make_skill(self, folder, name='source-evidence'):
        path = self.root / folder / 'SKILL.md'
        path.parent.mkdir()
        path.write_bytes(('---\r\nname: ' + name + '\r\ndescription: Source review fixture.\r\n'
                          '---\r\nRead references/rules.md.\r\n').encode())
        reference = path.parent / 'references/rules.md'
        reference.parent.mkdir()
        reference.write_text('Keep the original source evidence.\n', encoding='utf-8')
        return path

    def policy(self):
        return normalize_capabilities({'skills': ['selected/SKILL.md'],
                                       'web_search': 'cached', 'subagents': True}, self.root)

    def test_defaults_require_no_skill_files_or_staging_directory(self):
        policy = normalize_capabilities()
        self.assertEqual([], policy['skills'])
        self.assertEqual('disabled', policy['web_search'])
        self.assertIs(False, policy['subagents'])
        destination = self.root / 'not-created'
        self.assertEqual([], stage_skills(policy, destination))
        self.assertFalse(destination.exists())

    def test_selected_bundle_and_support_documents_are_staged_exactly(self):
        policy = self.policy()
        self.assertEqual(str(self.skill.resolve()), policy['skills'][0]['path'])
        self.assertEqual('source-evidence', policy['skills'][0]['name'])
        rows = policy['skills'][0]['files']
        self.assertEqual(['SKILL.md', 'references/rules.md'], [row['path'] for row in rows])
        for row in rows:
            raw = (self.skill.parent / row['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
            self.assertEqual(len(raw), row['bytes'])
        copies = stage_skills(policy, self.root / 'private/skills')
        self.assertEqual([self.root / 'private/skills/source-evidence/SKILL.md'], copies)
        for row in rows:
            self.assertEqual((self.skill.parent / row['path']).read_bytes(),
                             (copies[0].parent / row['path']).read_bytes())
        self.assertEqual(policy, validate_capabilities(policy))

    def test_changed_removed_or_added_support_documents_invalidate_snapshot(self):
        reference = self.skill.parent / 'references/rules.md'
        original = reference.read_bytes()
        for change in ('edit', 'remove', 'add'):
            with self.subTest(change=change):
                reference.write_bytes(original)
                extra = self.skill.parent / 'extra.md'
                if extra.exists():
                    extra.unlink()
                policy = self.policy()
                if change == 'edit':
                    reference.write_text('Changed policy.\n', encoding='utf-8')
                elif change == 'remove':
                    reference.unlink()
                else:
                    extra.write_text('New context.\n', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'bundle changed'):
                    validate_capabilities(policy)
                destination = self.root / ('unstaged-' + change)
                with self.assertRaises(ValueError):
                    stage_skills(policy, destination)
                self.assertFalse(destination.exists())
                self.assertEqual(policy, validate_capabilities(policy, check_files=False))

    def test_duplicate_paths_and_names_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            normalize_capabilities({'skills': ['selected/SKILL.md',
                                               'selected/../selected/SKILL.md']}, self.root)
        self.make_skill('other')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            normalize_capabilities({'skills': ['selected/SKILL.md', 'other/SKILL.md']}, self.root)

    def test_script_dependencies_are_explicitly_unsupported(self):
        script = self.skill.parent / 'scripts/analyze.py'
        script.parent.mkdir()
        script.write_text('raise RuntimeError("must never run")\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'executable dependencies are unsupported'):
            self.policy()

    def test_source_symlink_or_windows_junction_is_rejected(self):
        link = self.skill.parent / 'linked.md'
        try:
            link.symlink_to(self.skill)
        except OSError as exc:
            if os.name != 'nt':
                self.skipTest('Symlink creation unavailable: ' + str(exc))
            # Directory junctions need no symlink privilege on Windows.
            target = self.root / 'outside'
            target.mkdir()
            link = self.skill.parent / 'linked-docs'
            result = subprocess.run(['cmd.exe', '/c', 'mklink', '/J', str(link), str(target)],
                                    capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(0, result.returncode, result.stderr.decode(errors='replace'))
        with self.assertRaisesRegex(ValueError, 'symlinks or junctions'):
            self.policy()

    def test_oversized_skill_bundle_is_rejected_before_staging(self):
        (self.skill.parent / 'large.txt').write_bytes(b'x' * MAX_BUNDLE_BYTES)
        with self.assertRaisesRegex(ValueError, 'limit'):
            self.policy()

    def test_existing_private_skill_is_not_overwritten(self):
        destination = self.root / 'private'
        target = destination / 'source-evidence'
        target.mkdir(parents=True)
        marker = target / 'marker.txt'
        marker.write_text('Preserve this file.', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            stage_skills(self.policy(), destination)
        self.assertEqual('Preserve this file.', marker.read_text(encoding='utf-8'))

    def test_invalid_options_are_not_silently_ignored(self):
        for option in ({'shell': True}, {'hooks': []}, {'plugins': []},
                       {'skills': 'selected/SKILL.md'}, {'subagents': 1},
                       {'web_search': 'automatic'}, {'skills': [None]}):
            with self.subTest(option=option), self.assertRaises(ValueError):
                normalize_capabilities(option, self.root)

    def test_manifest_traversal_duplicates_and_fingerprints_are_rejected(self):
        original = self.policy()
        variants = []
        for relative in ('../escape.md', 'references\\escape.md', '/escape.md',
                         'references/../escape.md', 'C:/escape.md'):
            policy = deepcopy(original)
            policy['skills'][0]['files'][0]['path'] = relative
            variants.append(policy)
        policy = deepcopy(original)
        policy['skills'][0]['files'].append(deepcopy(policy['skills'][0]['files'][0]))
        variants.append(policy)
        policy = deepcopy(original)
        policy['skills'][0]['files'][0]['sha256'] = 'invalid'
        variants.append(policy)
        for policy in variants:
            with self.subTest(policy=policy), self.assertRaises(ValueError):
                validate_capabilities(policy, check_files=False)

    def test_skill_metadata_requires_a_unique_valid_name(self):
        for header in ('name: Invalid Name', 'name: one\nname: two', 'description: Missing name'):
            with self.subTest(header=header):
                self.skill.write_text('---\n' + header + '\n---\nBody\n', encoding='utf-8')
                with self.assertRaises(ValueError):
                    self.policy()

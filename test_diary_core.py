# Tests for diary_core, run against a real scratch diary directory with
# real encryption, not mocked.

import os
import shutil
import tempfile
import unittest

from cryptography.fernet import Fernet

import diary_core


class SetupAndUnlockTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="pydiary-test-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_a_new_diary_reports_absent(self):
        self.assertFalse(diary_core.diary_exists(self.root))

    def test_setup_creates_a_usable_diary(self):
        diary_core.setup_diary(self.root, "correct horse")
        self.assertTrue(diary_core.diary_exists(self.root))

    def test_the_right_password_unlocks(self):
        diary_core.setup_diary(self.root, "correct horse")
        key = diary_core.unlock_diary(self.root, "correct horse")
        self.assertIsNotNone(key)

    def test_the_wrong_password_is_refused_not_crashed(self):
        diary_core.setup_diary(self.root, "correct horse")
        key = diary_core.unlock_diary(self.root, "wrong guess")
        self.assertIsNone(key)

    def test_two_diaries_with_the_same_password_get_different_keys(self):
        root_a = tempfile.mkdtemp(prefix="pydiary-test-a-")
        root_b = tempfile.mkdtemp(prefix="pydiary-test-b-")
        self.addCleanup(shutil.rmtree, root_a, ignore_errors=True)
        self.addCleanup(shutil.rmtree, root_b, ignore_errors=True)
        key_a = diary_core.setup_diary(root_a, "same password")
        key_b = diary_core.setup_diary(root_b, "same password")
        self.assertNotEqual(key_a, key_b)


class EntryTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="pydiary-test-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.key = diary_core.setup_diary(self.root, "hunter2")

    def test_a_written_entry_reads_back(self):
        diary_core.write_entry(self.root, self.key, "today", "it was a fine day")
        text = diary_core.read_entry(self.root, self.key, "today")
        self.assertEqual(text, "it was a fine day")

    def test_a_missing_entry_reads_as_none(self):
        self.assertIsNone(diary_core.read_entry(self.root, self.key, "never written"))

    def test_entries_are_listed(self):
        diary_core.write_entry(self.root, self.key, "one", "a")
        diary_core.write_entry(self.root, self.key, "two", "b")
        self.assertEqual(diary_core.list_entries(self.root), ["one", "two"])

    def test_rewriting_a_title_replaces_the_stored_text(self):
        # Reusing a title is how the CLI edits an entry, so the second write
        # has to replace the first: one file left, holding the later text.
        diary_core.write_entry(self.root, self.key, "today", "first draft")
        diary_core.write_entry(self.root, self.key, "today", "second draft")
        self.assertEqual(diary_core.read_entry(self.root, self.key, "today"), "second draft")
        self.assertEqual(diary_core.list_entries(self.root), ["today"])

    def test_an_entry_can_be_deleted(self):
        diary_core.write_entry(self.root, self.key, "today", "text")
        self.assertTrue(diary_core.delete_entry(self.root, "today"))
        self.assertIsNone(diary_core.read_entry(self.root, self.key, "today"))

    def test_deleting_a_missing_entry_is_reported_not_raised(self):
        self.assertFalse(diary_core.delete_entry(self.root, "never written"))

    def test_a_stored_entry_cannot_be_read_with_the_wrong_key(self):
        diary_core.write_entry(self.root, self.key, "secret", "private text")
        wrong_key = diary_core.derive_key("not the password", b"0" * 16)
        # read_entry reports a key that does not match the stored token as
        # None instead of letting InvalidToken escape, so a wrong key is
        # pinned to a clean refusal rather than an uncaught crash.
        self.assertIsNone(diary_core.read_entry(self.root, wrong_key, "secret"))

    def test_a_traversal_title_reads_as_none_instead_of_the_decoy_file(self):
        # A file one level above entries holds validly encrypted text, so a
        # read that resolved the slashed title would hand the plaintext back.
        # The refusal is what makes this None, not the file being absent.
        decoy = os.path.join(self.root, "decoy")
        with open(decoy, "wb") as f:
            f.write(Fernet(self.key).encrypt(b"leaked"))
        self.assertIsNone(diary_core.read_entry(self.root, self.key, "../decoy"))
        self.assertTrue(os.path.exists(decoy))


class SafeTitleTests(unittest.TestCase):
    def test_an_ordinary_title_is_accepted(self):
        self.assertEqual(diary_core.safe_title("monday notes"), "monday notes")

    def test_a_path_with_a_slash_is_refused(self):
        self.assertIsNone(diary_core.safe_title("../../etc/passwd"))

    def test_a_backslash_is_refused(self):
        self.assertIsNone(diary_core.safe_title("..\\..\\windows"))

    def test_a_bare_dot_is_refused(self):
        self.assertIsNone(diary_core.safe_title("."))
        self.assertIsNone(diary_core.safe_title(".."))

    def test_an_empty_title_is_refused(self):
        self.assertIsNone(diary_core.safe_title(""))
        self.assertIsNone(diary_core.safe_title("   "))

    def test_surrounding_whitespace_is_trimmed(self):
        self.assertEqual(diary_core.safe_title("  today  "), "today")


class TraversalIsBlockedEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="pydiary-test-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.key = diary_core.setup_diary(self.root, "hunter2")

    def test_writing_outside_the_entries_directory_is_refused(self):
        # Expect ValueError when title validation fails on traversal attempts.
        with self.assertRaises(ValueError):
            diary_core.write_entry(self.root, self.key, "../../escape", "text")
        outside = os.path.join(self.root, "..", "..", "escape")
        self.assertFalse(os.path.exists(outside))

    def test_deleting_through_a_traversal_title_is_refused(self):
        # Deletion must not be a way around the check the write path already
        # enforces: a slashed title is refused and the file it names outside
        # the entries directory survives untouched.
        outside = os.path.join(self.root, "outside-marker")
        with open(outside, "w", encoding="utf-8") as f:
            f.write("keep me")
        self.assertFalse(diary_core.delete_entry(self.root, "../outside-marker"))
        self.assertTrue(os.path.exists(outside))


if __name__ == "__main__":
    unittest.main()

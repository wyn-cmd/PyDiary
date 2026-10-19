# Tests for diary_core, run against a real scratch diary directory with
# real encryption, not mocked.

import os
import shutil
import tempfile
import unittest

from cryptography.fernet import Fernet

import diary_core


class SetupAndUnlockTests(unittest.TestCase):
    # Set up a temporary scratch directory before each test.
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="pydiary-test-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    # A brand new directory should not look like an initialized diary.
    def test_a_new_diary_reports_absent(self):
        self.assertFalse(diary_core.diary_exists(self.root))

    # Setting up a diary creates the required structure.
    def test_setup_creates_a_usable_diary(self):
        diary_core.setup_diary(self.root, "correct horse")
        self.assertTrue(diary_core.diary_exists(self.root))

    # Using the correct password successfully unlocks and returns a key.
    def test_the_right_password_unlocks(self):
        diary_core.setup_diary(self.root, "correct horse")
        key = diary_core.unlock_diary(self.root, "correct horse")
        self.assertIsNotNone(key)

    # An incorrect password returns None instead of raising an error.
    def test_the_wrong_password_is_refused_not_crashed(self):
        diary_core.setup_diary(self.root, "correct horse")
        key = diary_core.unlock_diary(self.root, "wrong guess")
        self.assertIsNone(key)

    # Two separate diaries get distinct encryption keys even with the same password.
    def test_two_diaries_with_the_same_password_get_different_keys(self):
        root_a = tempfile.mkdtemp(prefix="pydiary-test-a-")
        root_b = tempfile.mkdtemp(prefix="pydiary-test-b-")
        self.addCleanup(shutil.rmtree, root_a, ignore_errors=True)
        self.addCleanup(shutil.rmtree, root_b, ignore_errors=True)
        key_a = diary_core.setup_diary(root_a, "same password")
        key_b = diary_core.setup_diary(root_b, "same password")
        self.assertNotEqual(key_a, key_b)


class EntryTests(unittest.TestCase):
    # Prepare an initialized diary for entry testing.
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="pydiary-test-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.key = diary_core.setup_diary(self.root, "hunter2")

    # Written entries can be read back with matching content.
    def test_a_written_entry_reads_back(self):
        diary_core.write_entry(self.root, self.key, "today", "it was a fine day")
        text = diary_core.read_entry(self.root, self.key, "today")
        self.assertEqual(text, "it was a fine day")

    # Reading an unwritten entry returns None.
    def test_a_missing_entry_reads_as_none(self):
        self.assertIsNone(diary_core.read_entry(self.root, self.key, "never written"))

    # All written entry titles are listed correctly.
    def test_entries_are_listed(self):
        diary_core.write_entry(self.root, self.key, "one", "a")
        diary_core.write_entry(self.root, self.key, "two", "b")
        self.assertEqual(diary_core.list_entries(self.root), ["one", "two"])

    # Rewriting an existing title updates the stored text and keeps only one file.
    def test_rewriting_a_title_replaces_the_stored_text(self):
        diary_core.write_entry(self.root, self.key, "today", "first draft")
        diary_core.write_entry(self.root, self.key, "today", "second draft")
        self.assertEqual(diary_core.read_entry(self.root, self.key, "today"), "second draft")
        self.assertEqual(diary_core.list_entries(self.root), ["today"])

    # An entry can be deleted successfully.
    def test_an_entry_can_be_deleted(self):
        diary_core.write_entry(self.root, self.key, "today", "text")
        self.assertTrue(diary_core.delete_entry(self.root, "today"))
        self.assertIsNone(diary_core.read_entry(self.root, self.key, "today"))

    # Deleting a non-existent entry returns False instead of raising an error.
    def test_deleting_a_missing_entry_is_reported_not_raised(self):
        self.assertFalse(diary_core.delete_entry(self.root, "never written"))

    # Reading an entry with an incorrect key safely returns None.
    def test_a_stored_entry_cannot_be_read_with_the_wrong_key(self):
        diary_core.write_entry(self.root, self.key, "secret", "private text")
        wrong_key = diary_core.derive_key("not the password", b"0" * 16)
        self.assertIsNone(diary_core.read_entry(self.root, wrong_key, "secret"))

    # Path traversal attempts read as None and leave decoy files untouched.
    def test_a_traversal_title_reads_as_none_instead_of_the_decoy_file(self):
        decoy = os.path.join(self.root, "decoy")
        with open(decoy, "wb") as f:
            f.write(Fernet(self.key).encrypt(b"leaked"))
        self.assertIsNone(diary_core.read_entry(self.root, self.key, "../decoy"))
        self.assertTrue(os.path.exists(decoy))


class SafeTitleTests(unittest.TestCase):
    # Standard titles pass through validation.
    def test_an_ordinary_title_is_accepted(self):
        self.assertEqual(diary_core.safe_title("monday notes"), "monday notes")

    # Titles containing forward slashes are rejected.
    def test_a_path_with_a_slash_is_refused(self):
        self.assertIsNone(diary_core.safe_title("../../etc/passwd"))

    # Titles containing backslashes are rejected.
    def test_a_backslash_is_refused(self):
        self.assertIsNone(diary_core.safe_title("..\\..\\windows"))

    # Bare dot titles are rejected.
    def test_a_bare_dot_is_refused(self):
        self.assertIsNone(diary_core.safe_title("."))
        self.assertIsNone(diary_core.safe_title(".."))

    # Empty or blank titles are rejected.
    def test_an_empty_title_is_refused(self):
        self.assertIsNone(diary_core.safe_title(""))
        self.assertIsNone(diary_core.safe_title("   "))

    # Surrounding whitespace is stripped from valid titles.
    def test_surrounding_whitespace_is_trimmed(self):
        self.assertEqual(diary_core.safe_title("  today  "), "today")


class TraversalIsBlockedEndToEndTests(unittest.TestCase):
    # Set up a diary for traversal defense tests.
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="pydiary-test-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.key = diary_core.setup_diary(self.root, "hunter2")

    # Writing outside the entries directory raises a ValueError.
    def test_writing_outside_the_entries_directory_is_refused(self):
        with self.assertRaises(ValueError):
            diary_core.write_entry(self.root, self.key, "../../escape", "text")
        outside = os.path.join(self.root, "..", "..", "escape")
        self.assertFalse(os.path.exists(outside))

    # Deleting through traversal titles is blocked and leaves outside files alone.
    def test_deleting_through_a_traversal_title_is_refused(self):
        outside = os.path.join(self.root, "outside-marker")
        with open(outside, "w", encoding="utf-8") as f:
            f.write("keep me")
        self.assertFalse(diary_core.delete_entry(self.root, "../outside-marker"))
        self.assertTrue(os.path.exists(outside))


if __name__ == "__main__":
    unittest.main()

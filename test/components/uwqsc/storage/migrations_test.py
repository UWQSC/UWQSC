"""
Testing the storage connection and migrations
"""

import os
import tempfile
import unittest

from uwqsc.storage import apply_migrations, connect, register_migration


class MigrationsTest(unittest.TestCase):
    """
    This class is used to test per-brick schema migrations
    """

    @classmethod
    def setUpClass(cls):
        register_migration("storage_test_a", 1, "CREATE TABLE IF NOT EXISTS a_t (x INTEGER);")
        register_migration("storage_test_a", 2, "ALTER TABLE a_t ADD COLUMN y INTEGER;")
        register_migration("storage_test_b", 1, "CREATE TABLE IF NOT EXISTS b_t (x INTEGER);")

    def test_applies_once(self):
        """
        Testing that migrations apply on connect and are not re-applied
        """

        conn = connect(":memory:")
        columns = [row[1] for row in conn.execute("PRAGMA table_info(a_t)")]
        self.assertEqual(columns, ["x", "y"])

        self.assertEqual(apply_migrations(conn), [])

    def test_owners_do_not_collide(self):
        """
        Testing that two owners can both use version 1
        """

        conn = connect(":memory:")
        versions = set(conn.execute(
            "SELECT owner, version FROM schema_migrations "
            "WHERE owner LIKE 'storage_test_%'"
        ).fetchall())
        self.assertEqual(versions,
                         {("storage_test_a", 1), ("storage_test_a", 2), ("storage_test_b", 1)})

    def test_conflicting_registration_raises(self):
        """
        Testing that re-registering a version with different SQL is rejected
        """

        register_migration("storage_test_b", 1, "CREATE TABLE IF NOT EXISTS b_t (x INTEGER);")
        with self.assertRaises(ValueError):
            register_migration("storage_test_b", 1, "CREATE TABLE other (z TEXT);")

    def test_file_database_reopens(self):
        """
        Testing that a file database is created, and reopening it is a no-op
        """

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "nested", "db.sqlite")
            connect(path).close()
            self.assertTrue(os.path.exists(path))
            conn = connect(path)
            self.assertEqual(apply_migrations(conn), [])
            conn.close()


if __name__ == "__main__":
    unittest.main()

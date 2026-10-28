import unittest
from v2_source_audit_diff import compare

class AuditDiffTests(unittest.TestCase):
    def test_persistent_recovered_and_new(self):
        a=[{"kind":"RSS","name":"A","ok":False},{"kind":"RSS","name":"B","ok":False},
           {"kind":"RSS","name":"C","ok":True}]
        b=[{"kind":"RSS","name":"A","ok":False},{"kind":"RSS","name":"B","ok":True},
           {"kind":"RSS","name":"C","ok":False}]
        r=compare(a,b)
        self.assertEqual(r["persistent_failures"],["RSS:A"])
        self.assertEqual(r["recovered_once"],["RSS:B"])
        self.assertEqual(r["new_failures"],["RSS:C"])
        self.assertFalse(r["safe_to_delete_source"])
    def test_duplicate_source_refused(self):
        with self.assertRaises(ValueError):
            compare([{"kind":"RSS","name":"A"},{"kind":"RSS","name":"A"}],[])
    def test_missing_source_not_recovery(self):
        r=compare([{"kind":"RSS","name":"A","ok":False}],[])
        self.assertEqual(r["missing_from_current"],1)
        self.assertEqual(r["recovered_once"],[])
if __name__=="__main__":unittest.main()

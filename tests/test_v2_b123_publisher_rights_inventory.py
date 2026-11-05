import unittest
from v2_b123_publisher_rights_inventory import build_registry_rights_inventory

class RightsInventoryTests(unittest.TestCase):
    def test_each_live_publisher_holds_rights_and_factuality_gates(self):
        audit=build_registry_rights_inventory()
        self.assertEqual(set(audit['products']), {'english','arabic'})
        self.assertGreaterEqual(audit['publisher_ids_total'], 7)
        for product,rows in audit['products'].items():
            self.assertTrue(rows)
            self.assertEqual(len({r['source_id'] for r in rows}),len(rows))
            self.assertTrue(all(r['rights_status']=='UNVERIFIED' for r in rows))
            self.assertTrue(all(r['republication_permission_evidenced'] is False for r in rows))
            self.assertTrue(all(r['independent_fact_check_evidenced'] is False for r in rows))
        self.assertFalse(audit['can_release'])

if __name__=='__main__':unittest.main()

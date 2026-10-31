"""Prevent publisher-ID collisions between live preview and canonical V2 registry."""
import json
import unittest
from pathlib import Path
from v2_b46_live_editorial import SOURCE_CATALOG

class SourceCatalogIdentity(unittest.TestCase):
    def test_registry_source_ids_match_exact_feed_urls(self):
        registry=json.loads((Path(__file__).resolve().parents[1]/"config/v2/source_registry.json").read_text())
        by_id={row["id"]:row for row in registry["sources"]}
        for product,sources in SOURCE_CATALOG.items():
            for source in sources:
                source_id=source["source_id"]
                if source_id.startswith("preview-"):
                    self.assertNotIn(source_id,by_id)
                    continue
                self.assertIn(source_id,by_id)
                self.assertEqual(source["feed_url"],by_id[source_id]["entrypoint"],
                                 f"{product} {source_id}: publisher identity mismatch")

if __name__=="__main__":unittest.main()

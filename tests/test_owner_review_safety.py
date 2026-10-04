"""Owner-review identity guards do not touch unknown databases or directories."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import owner_review

class OwnerReviewSafety(unittest.TestCase):
    def config(self, host="localhost", name="axyrel_owner_review_" + "1" * 32):
        return {"database_url":f"postgresql+psycopg://review:unused@{host}/{name}", "identity":"2" * 32}

    def test_remote_or_unknown_name_rejected_before_any_connection(self):
        for config in [self.config(host="example.invalid"), self.config(name="existing_unknown")]:
            with patch.object(owner_review, "create_engine") as factory:
                with self.assertRaises(RuntimeError): owner_review.verify(config)
                factory.assert_not_called()

    def test_wrong_marker_never_connects_to_target_database(self):
        admin=MagicMock()
        admin.connect.return_value.__enter__.return_value.execute.return_value.scalar.return_value=None
        with patch.object(owner_review, "create_engine", return_value=admin) as factory:
            with self.assertRaises(RuntimeError): owner_review.verify(self.config())
            self.assertEqual(factory.call_count,1)
            self.assertEqual(factory.call_args.args[0].database,"postgres")
            admin.dispose.assert_called_once()

    def test_matching_catalog_marker_allows_only_identified_target(self):
        admin, target=MagicMock(), MagicMock()
        admin.connect.return_value.__enter__.return_value.execute.return_value.scalar.return_value="axyrel-owner-review:"+"2"*32
        with patch.object(owner_review,"create_engine",side_effect=[admin,target]) as factory:
            self.assertIs(owner_review.verify(self.config()),target)
            self.assertEqual(factory.call_args_list[0].args[0].database,"postgres")
            self.assertEqual(factory.call_args_list[1].args[0].database,"axyrel_owner_review_"+"1"*32)
            target.connect.assert_not_called()

    def test_unknown_directory_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            state=Path(directory); marker=state/"unknown.txt";marker.write_text("preserve")
            with patch.object(owner_review,"STATE",state),patch.object(owner_review,"CONFIG",state/"configuration.json"),patch.object(owner_review,"create_engine") as factory:
                with self.assertRaises(RuntimeError):owner_review.initialize()
                factory.assert_not_called()
                self.assertEqual(marker.read_text(),"preserve")

    def test_existing_ready_environment_is_not_reseeded(self):
        with tempfile.TemporaryDirectory() as directory:
            state=Path(directory);config=state/"configuration.json";config.write_text(json.dumps({"ready":True}))
            with patch.object(owner_review,"STATE",state),patch.object(owner_review,"CONFIG",config),patch.object(owner_review,"verify") as verify,patch.object(owner_review,"create_engine") as factory:
                owner_review.initialize();verify.assert_called_once();factory.assert_not_called()

if __name__=="__main__":unittest.main(verbosity=2)

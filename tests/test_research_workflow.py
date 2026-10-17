"""A self-review, old head or withdrawn approval cannot establish independence."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import research_workflow as research


class ReviewTests(unittest.TestCase):
    def test_only_latest_independent_current_head_approval_counts(self):
        reviews = [
            {"id": 1, "user": {"login": "author"}, "state": "APPROVED", "commit_id": "current"},
            {"id": 2, "user": {"login": "reviewer"}, "state": "APPROVED", "commit_id": "old"},
            {"id": 3, "user": {"login": "outsider"}, "state": "APPROVED", "commit_id": "current"},
        ]
        allowed = ["author", "reviewer"]
        self.assertEqual(research.independent_reviews(reviews, "author", "current", allowed), [])
        reviews.append({"id": 4, "user": {"login": "reviewer"}, "state": "APPROVED", "commit_id": "current"})
        self.assertEqual(research.independent_reviews(reviews, "author", "current", allowed), ["reviewer"])
        reviews.append({"id": 5, "user": {"login": "reviewer"}, "state": "COMMENTED", "commit_id": "current"})
        self.assertEqual(research.independent_reviews(reviews, "author", "current", allowed), ["reviewer"])
        reviews.append({"id": 6, "user": {"login": "reviewer"}, "state": "DISMISSED", "commit_id": "current"})
        self.assertEqual(research.independent_reviews(reviews, "author", "current", allowed), [])
        self.assertEqual(research.independent_reviews(reviews, "author", "current", []), [])


if __name__ == "__main__":
    unittest.main()

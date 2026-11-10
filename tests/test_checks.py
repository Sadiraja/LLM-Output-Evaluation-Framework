import unittest
from llm_eval.checks import factual_consistency, format_compliance
from llm_eval.stats import cohen_kappa, spearman

QA = {"format": "sentence", "must_include": [["canberra"]], "match": "word"}
JS = {"format": "json", "expected_json": {"name": "A B", "age": 3}}
LS = {"format": "list3", "must_include": [["solar"], ["wind"], ["hydro"], ["tidal"]], "min_hits": 3, "match": "prefix"}


class T(unittest.TestCase):
    def test_fact(self):
        self.assertTrue(factual_consistency(QA, "The capital is Canberra.").passed)
        self.assertFalse(factual_consistency(QA, "It is Sydney.").passed)
        self.assertTrue(factual_consistency(JS, '```json\n{"name":"a b","age":3}\n```').passed)
        self.assertEqual(factual_consistency(JS, '{"name":"A B","age":4}').score, 0.5)
        self.assertTrue(factual_consistency(LS, "- Solar\n- Wind\n- Hydroelectric").passed)
        self.assertFalse(factual_consistency(LS, "- Solar\n- Wind\n- Coal").passed)

    def test_format(self):
        self.assertTrue(format_compliance(QA, "Canberra.").passed)
        self.assertFalse(format_compliance(QA, "Sure! Canberra.").passed)
        self.assertFalse(format_compliance(JS, '```json\n{"name":"A B","age":3}\n```').passed)
        self.assertTrue(format_compliance(JS, '{"name":"A B","age":3}').passed)
        self.assertFalse(format_compliance(LS, "1. a\n2. b\n3. c").passed)
        self.assertTrue(format_compliance(LS, "- a\n- b\n- c").passed)

    def test_stats(self):
        self.assertAlmostEqual(cohen_kappa([1, 2, 1, 2], [1, 2, 1, 2], [1, 2]), 1.0)
        self.assertAlmostEqual(spearman([1, 2, 3], [1, 2, 3]), 1.0)


if __name__ == "__main__":
    unittest.main()

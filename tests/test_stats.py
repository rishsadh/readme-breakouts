import unittest

from readme_breakouts.stats import fisher_two_sided, holm, quantiles, wilson


class Stats(unittest.TestCase):
    def test_wilson_known_value(self):
        lo, hi = wilson(82, 100)
        self.assertAlmostEqual(lo, 0.7333, places=3)
        self.assertAlmostEqual(hi, 0.8830, places=3)

    def test_wilson_edges(self):
        self.assertEqual(wilson(0, 0), (0.0, 0.0))
        lo, hi = wilson(0, 50)
        self.assertEqual(lo, 0.0)
        self.assertLess(hi, 0.08)
        lo, hi = wilson(50, 50)
        self.assertEqual(hi, 1.0)

    def test_fisher_tea_tasting(self):
        # Fisher's lady tasting tea: 3,1 / 1,3 gives two-sided p = 0.4857
        self.assertAlmostEqual(fisher_two_sided(3, 1, 1, 3), 0.4857, places=3)

    def test_fisher_extreme_and_null(self):
        self.assertAlmostEqual(fisher_two_sided(10, 0, 0, 10), 2 / 184756, places=8)
        self.assertEqual(fisher_two_sided(5, 5, 5, 5), 1.0)

    def test_holm(self):
        self.assertEqual(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
        self.assertEqual(holm([]), [])

    def test_quantiles(self):
        self.assertEqual(quantiles([]), None)
        self.assertEqual(quantiles([4]), (4, 4, 4, 4, 4))
        self.assertEqual(quantiles([1, 2, 3, 4, 5]), (1, 2, 3, 4, 5))


if __name__ == "__main__":
    unittest.main()


class Stratified(unittest.TestCase):
    def test_equal_to_plain_share_when_strata_are_proportional(self):
        from readme_breakouts.stats import stratified_share
        share, (lo, hi) = stratified_share({"a": 600, "b": 400}, {"a": 30, "b": 20}, {"a": 60, "b": 40})
        self.assertAlmostEqual(share, 0.5)
        self.assertLess(lo, 0.5)
        self.assertGreater(hi, 0.5)

    def test_reweights_when_a_small_stratum_is_oversampled(self):
        from readme_breakouts.stats import stratified_share
        # 10% of the population is stratum b, but half the sample is. b is all positive, a is all negative.
        share, _ = stratified_share({"a": 900, "b": 100}, {"a": 0, "b": 50}, {"a": 50, "b": 50})
        self.assertAlmostEqual(share, 0.1)

    def test_interval_stays_in_bounds_for_zero(self):
        from readme_breakouts.stats import stratified_share
        share, (lo, hi) = stratified_share({"a": 50, "b": 50}, {"a": 0, "b": 0}, {"a": 10, "b": 10})
        self.assertEqual(share, 0)
        self.assertEqual(lo, 0.0)
        self.assertGreater(hi, 0)
        self.assertLess(hi, 0.3)

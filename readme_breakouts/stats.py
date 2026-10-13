"""Small statistics helpers on the standard library: Wilson intervals, Fisher's exact test, Holm."""
import math
import statistics


def wilson(k, n, z=1.96):
    """95% Wilson score interval for a proportion, as fractions (lo, hi)."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def fisher_two_sided(a, b, c, d):
    """Two-sided Fisher exact p-value for the 2x2 table [[a, b], [c, d]] (rows are groups)."""
    r1, r2, c1 = a + b, c + d, a + c
    n = r1 + r2

    def prob(x):
        return math.comb(r1, x) * math.comb(r2, c1 - x) / math.comb(n, c1)

    lo, hi = max(0, c1 - r2), min(r1, c1)
    p_obs = prob(a)
    return min(1.0, sum(prob(x) for x in range(lo, hi + 1) if prob(x) <= p_obs * (1 + 1e-9)))


def holm(pvalues):
    """Holm-Bonferroni adjusted p-values, in the input order."""
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    adj = [0.0] * len(pvalues)
    running = 0.0
    m = len(pvalues)
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvalues[i]))
        adj[i] = running
    return adj


def quantiles(values):
    """(min, q1, median, q3, max) of a list of numbers, or None when empty."""
    v = sorted(values)
    if not v:
        return None
    if len(v) == 1:
        return (v[0],) * 5
    q = statistics.quantiles(v, n=4, method="inclusive")
    return (v[0], q[0], q[1], q[2], v[-1])


def pct(x):
    return f"{100 * x:.0f}%"


def stratified_share(pop_sizes, hits, sample_sizes, z=1.96):
    """Post-stratified estimate of a population share from a stratified sample.

    pop_sizes, hits and sample_sizes map stratum -> N, positives in the sample, n. Returns
    (share, (lo, hi)). The interval is a Wilson interval on an effective sample size worked out
    from the stratified variance, so it stays inside 0 to 1 for rare features."""
    total = sum(pop_sizes[k] for k in sample_sizes)
    share = sum(pop_sizes[k] / total * hits[k] / sample_sizes[k] for k in sample_sizes)
    var = 0.0
    for k, n in sample_sizes.items():
        p = hits[k] / n
        f = n / pop_sizes[k]
        var += (pop_sizes[k] / total) ** 2 * (1 - f) * p * (1 - p) / max(n - 1, 1)
    n_total = sum(sample_sizes.values())
    if var <= 0 or share <= 0 or share >= 1:
        n_eff = n_total
    else:
        n_eff = min(share * (1 - share) / var, 10 * n_total)
    k_eff = share * n_eff
    return share, wilson(k_eff, n_eff, z)

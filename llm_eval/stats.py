"""Pure-python statistics (no numpy needed)."""
import math
import random


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def bootstrap_ci(diffs, n=2000, seed=0, alpha=0.05):
    rng = random.Random(seed)
    k = len(diffs)
    ms = sorted(mean([diffs[rng.randrange(k)] for _ in range(k)]) for _ in range(n))
    return ms[int(n * alpha / 2)], ms[int(n * (1 - alpha / 2)) - 1]


def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for t in range(i, j + 1):
            r[order[t]] = (i + j) / 2 + 1
        i = j + 1
    return r


def pearson(a, b):
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den if den else None


def spearman(a, b):
    return pearson(ranks(a), ranks(b))


def cohen_kappa(a, b, categories, weights="none"):
    """Cohen's kappa; weights='quadratic' for ordinal scales."""
    k = len(categories)
    idx = {c: i for i, c in enumerate(categories)}
    n = len(a)
    obs = [[0.0] * k for _ in range(k)]
    for x, y in zip(a, b):
        obs[idx[x]][idx[y]] += 1
    row = [sum(r) for r in obs]
    col = [sum(obs[i][j] for i in range(k)) for j in range(k)]
    num = den = 0.0
    for i in range(k):
        for j in range(k):
            w = 0.0 if i == j else (1.0 if weights == "none" else ((i - j) / (k - 1)) ** 2)
            num += w * obs[i][j]
            den += w * row[i] * col[j] / n
    return 1 - num / den if den else None

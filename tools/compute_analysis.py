"""The analysis behind the site.

Reproduces the existing pipeline (PCA, k-means, penalised logistic regression, a
classification tree) and adds what the original omitted: the complex survey design.
NSDUH is a stratified multistage sample, so unweighted percentages describe the sample
rather than the country, and standard errors that ignore the design are too small.

    source/NSDUH_*.txt  ->  derived/analysis.json   (aggregate only)
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from paths import (DERIVED, YEARS, LABELS, SEX, AGE, INCOME, HEALTH,
                   load_pooled, analysis_frame)
import numpy as np, pandas as pd
import statsmodels.api as sm
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, cohen_kappa_score, confusion_matrix

SEED = 1
PCA_VARS = ["ALC_PASTMO", "MJ_PASTMO", "CIG_PASTMO", "IRSEX", "CATAG6", "INCOME", "HEALTH"]
MODEL_VARS = ["ALC_PASTMO", "MJ_PASTMO", "CIG_PASTMO", "IRSEX", "CATAG6", "INCOME", "HEALTH"]
wm = lambda s, w: float(np.average(s, weights=w))

def main():
    df = load_pooled()
    a = analysis_frame(df)
    R = {"years": list(YEARS), "pooled_rows": int(len(df)), "n": int(len(a)), "seed": SEED}

    # ---- 1. sample accounting ----
    adolescents = int((df.CATAG6 == 1).sum())
    R["sample"] = dict(
        pooled=int(len(df)), analysed=int(len(a)),
        adolescents_excluded=adolescents,
        adults_missing_outcome=int(len(df) - len(a) - adolescents),
        population_note="adults 18 and over",
        weight_sum=float(a.WT.sum()),
        by_year=[dict(year=int(y), pooled=int((df.YEAR == y).sum()),
                      analysed=int((a.YEAR == y).sum())) for y in YEARS])

    # ---- 2. descriptives, weighted against unweighted ----
    R["prevalence"] = [
        dict(measure=LABELS[c], var=c,
             unweighted=round(a[c].mean() * 100, 2),
             weighted=round(wm(a[c], a.WT) * 100, 2),
             by_year=[dict(year=int(y),
                           unweighted=round(a[a.YEAR == y][c].mean() * 100, 2),
                           weighted=round(wm(a[a.YEAR == y][c], a[a.YEAR == y].WT) * 100, 2))
                      for y in YEARS])
        for c in ["ALC_PASTMO", "MJ_PASTMO", "CIG_PASTMO", "MDE"]]

    def breakdown(col, mapping, name):
        out = []
        for k in sorted(a[col].dropna().unique()):
            g = a[a[col] == k]
            out.append(dict(level=mapping.get(int(k), str(int(k))), n=int(len(g)),
                            unweighted=round(g.MDE.mean() * 100, 2),
                            weighted=round(wm(g.MDE, g.WT) * 100, 2)))
        return dict(name=name, rows=out)
    R["mde_by"] = [breakdown("IRSEX", SEX, "Sex"), breakdown("CATAG6", AGE, "Age band"),
                   breakdown("INCOME", INCOME, "Household income"),
                   breakdown("HEALTH", HEALTH, "Self-rated health")]

    # ---- 3. PCA ----
    X = a[PCA_VARS].astype(float)
    Xs = StandardScaler().fit_transform(X)
    p = PCA(random_state=SEED).fit(Xs)
    R["pca"] = dict(
        vars=PCA_VARS,
        explained=[round(float(v) * 100, 2) for v in p.explained_variance_ratio_],
        cumulative=[round(float(v) * 100, 2) for v in np.cumsum(p.explained_variance_ratio_)],
        loadings=[dict(var=v, pc1=round(float(p.components_[0][i]), 3),
                       pc2=round(float(p.components_[1][i]), 3),
                       pc3=round(float(p.components_[2][i]), 3))
                  for i, v in enumerate(PCA_VARS)])

    # ---- 4. k-means on the first three components ----
    scores = p.transform(Xs)[:, :3]
    km = KMeans(n_clusters=4, n_init=10, random_state=SEED).fit(scores)
    a["cluster"] = km.labels_
    prof = []
    for c in range(4):
        g = a[a.cluster == c]
        prof.append(dict(cluster=int(c), n=int(len(g)),
                         pct=round(100 * len(g) / len(a), 1),
                         pct_weighted=round(100 * g.WT.sum() / a.WT.sum(), 1),
                         alc=round(g.ALC_PASTMO.mean() * 100, 1),
                         mj=round(g.MJ_PASTMO.mean() * 100, 1),
                         cig=round(g.CIG_PASTMO.mean() * 100, 1),
                         mde=round(g.MDE.mean() * 100, 1),
                         age=round(float(g.CATAG6.mean()), 2),
                         income=round(float(g.INCOME.mean()), 2),
                         health=round(float(g.HEALTH.mean()), 2)))
    prof.sort(key=lambda r: -r["mj"])
    R["clusters"] = prof

    # stability: refit on resamples and see whether the structure returns
    rng = np.random.default_rng(SEED)
    sizes = []
    for _ in range(20):
        idx = rng.choice(len(scores), size=min(40000, len(scores)), replace=False)
        k2 = KMeans(n_clusters=4, n_init=5, random_state=int(rng.integers(1e6))).fit(scores[idx])
        s = np.sort(np.bincount(k2.labels_, minlength=4) / len(idx) * 100)
        sizes.append(s)
    sizes = np.array(sizes)
    R["cluster_stability"] = dict(
        runs=len(sizes),
        sorted_sizes_mean=[round(float(v), 1) for v in sizes.mean(axis=0)],
        sorted_sizes_sd=[round(float(v), 2) for v in sizes.std(axis=0, ddof=1)])

    # ---- 5. prediction ----
    Xm = a[MODEL_VARS].astype(float).values
    y = a.MDE.astype(int).values
    cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
    lasso = LogisticRegression(solver="liblinear", l1_ratio=1, C=1.0, max_iter=2000)
    prob = cross_val_predict(lasso, StandardScaler().fit_transform(Xm), y, cv=cv,
                             method="predict_proba")[:, 1]
    auc = roc_auc_score(y, prob)
    pred50 = (prob >= .5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred50).ravel()
    R["model"] = dict(
        auc=round(float(auc), 4),
        accuracy=round(float((pred50 == y).mean()), 4),
        kappa=round(float(cohen_kappa_score(y, pred50)), 4),
        predicted_positive=int(pred50.sum()),
        imbalance_ratio=round(float((y == 0).sum() / (y == 1).sum()), 2),
        confusion=dict(tn=int(tn), fp=int(fp), fn=int(fn), tp=int(tp)))

    # thresholds: what the same model looks like at a lower cut
    R["thresholds"] = []
    for t in (0.50, 0.30, 0.20, 0.15, 0.10):
        pr = (prob >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y, pr).ravel()
        R["thresholds"].append(dict(
            t=t, sensitivity=round(tp / (tp + fn), 3), specificity=round(tn / (tn + fp), 3),
            precision=round(tp / (tp + fp), 3) if (tp + fp) else 0.0,
            kappa=round(float(cohen_kappa_score(y, pr)), 3),
            flagged=int(pr.sum()), flagged_pct=round(100 * pr.mean(), 1)))

    # ---- 6. what the design does to the standard errors ----
    Xd = sm.add_constant(a[MODEL_VARS].astype(float))
    naive = sm.GLM(y, Xd, family=sm.families.Binomial()).fit()
    # Design-adjusted standard errors. NSDUH is stratified with replicate clusters, so the
    # stratum-replicate combination is used as the clustering unit. statsmodels does not
    # implement a full survey estimator, so this is an approximation: it captures the
    # clustering and the weighting, not the stratification gain. It therefore tends to be
    # conservative, and the ratio below is best read as "roughly how far out the naive
    # standard errors are", not as an exact design effect.
    groups = (a.VESTR_C.astype(str) + "_" + a.VEREP.astype(str)).values
    design = sm.GLM(y, Xd, family=sm.families.Binomial(), var_weights=a.WT.values).fit(
        cov_type="cluster", cov_kwds={"groups": groups})
    R["design_effect"] = [
        dict(term=t,
             naive_coef=round(float(naive.params[t]), 4), naive_se=round(float(naive.bse[t]), 5),
             design_coef=round(float(design.params[t]), 4), design_se=round(float(design.bse[t]), 5),
             se_ratio=round(float(design.bse[t] / naive.bse[t]), 2))
        for t in Xd.columns]

    # ---- 7. classification tree ----
    tree = DecisionTreeClassifier(max_depth=4, min_samples_leaf=500, random_state=SEED).fit(Xm, y)
    imp = sorted(zip(MODEL_VARS, tree.feature_importances_), key=lambda kv: -kv[1])
    R["tree"] = dict(depth=4,
                     importance=[dict(var=v, importance=round(float(i), 4)) for v, i in imp],
                     first_split=MODEL_VARS[int(tree.tree_.feature[0])])

    DERIVED.mkdir(parents=True, exist_ok=True)
    json.dump(R, open(DERIVED / "analysis.json", "w"), indent=1)

    s = R["sample"]
    print(f"  pooled {s['pooled']:,} -> analysed {s['analysed']:,}")
    print(f"    adolescents never asked the adult question: {s['adolescents_excluded']:,}")
    print(f"    adults with a missing outcome:              {s['adults_missing_outcome']:,}")
    print(f"\n  {'measure':38s} {'unwtd':>7s} {'wtd':>7s}")
    for r in R["prevalence"]:
        print(f"  {r['measure']:38s} {r['unweighted']:6.2f}% {r['weighted']:6.2f}%")
    print(f"\n  PCA: first three components explain {R['pca']['cumulative'][2]:.1f}%")
    print(f"  clusters (by marijuana rate): " +
          ", ".join(f"{c['pct']}%/mj {c['mj']}%" for c in R["clusters"]))
    m = R["model"]
    print(f"\n  model: AUC {m['auc']}  accuracy {m['accuracy']}  kappa {m['kappa']}  "
          f"predicted positive {m['predicted_positive']:,} of {R['n']:,}")
    print(f"  imbalance {m['imbalance_ratio']} to 1")
    print(f"\n  design effect on standard errors (approximate, ratio design/naive):")
    for d in R["design_effect"]:
        print(f"    {d['term']:12s} naive SE {d['naive_se']:.5f}  design SE {d['design_se']:.5f}  x{d['se_ratio']}")


def sim_params():
    """Aggregate parameters for the notebook's synthetic generator. Aggregates only."""
    import json as _j
    df = load_pooled(); a = analysis_frame(df)
    P = dict(n=int(len(a)), years=list(YEARS))
    P["marginals"] = {c: round(float(a[c].mean()), 4) for c in ["ALC_PASTMO","MJ_PASTMO","CIG_PASTMO"]}
    P["cat"] = {c: {str(int(k)): round(float(v), 4) for k, v in a[c].value_counts(normalize=True).items()}
                for c in ["IRSEX","CATAG6","INCOME","HEALTH"]}
    Xd = sm.add_constant(a[MODEL_VARS].astype(float))
    fit = sm.GLM(a.MDE.astype(int), Xd, family=sm.families.Binomial()).fit()
    P["mde_logit"] = {t: round(float(fit.params[t]), 4) for t in Xd.columns}
    # weight profile by age band: this is what makes weighting bite
    P["weight_by_age"] = {str(int(k)): round(float(g.WT.mean()), 1) for k, g in a.groupby("CATAG6")}
    (DERIVED / "sim_params.json").write_text(_j.dumps(P, indent=1))
    print(f"  sim_params.json written ({len(P['mde_logit'])} coefficients)")

if __name__ == "__main__":
    main()
    sim_params()

"""Build the Colab notebook. Runs on synthetic data because the real files are 1.1 GB."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from paths import NOTEBOOKS, DERIVED, SAMHSA
import nbformat as nbf

REPO = "https://github.com/johnfisher-ai/fisher-nsduh-analysis"
SITE = "https://johnfisher-ai.github.io/fisher-nsduh-analysis"

def main():
    P = json.load(open(DERIVED / "sim_params.json"))
    A = json.load(open(DERIVED / "analysis.json"))
    nb = nbf.v4.new_notebook(); C = []
    md = lambda s: C.append(nbf.v4.new_markdown_cell(s))
    co = lambda s: C.append(nbf.v4.new_code_cell(s))

    md(f"""# Depression and substance use in the NSDUH

A runnable companion to an analysis of the **National Survey on Drug Use and Health**,
2022 to 2024. Three years pooled give {A['n']:,} adults with a usable depression outcome.

> ### This notebook runs on synthetic data
> The three public-use files total about 1.1 GB, far more than a notebook can carry. The
> generator below builds a dataset from this study's aggregate parameters, so every cell
> runs with no setup and the code paths are real.
>
> **Numbers produced here are simulated.** The real figures are on the
> [analysis page]({SITE}/analysis.html). Part 1b switches onto the real files once you have
> downloaded them from [SAMHSA]({SAMHSA}).

The thing this notebook is really about: NSDUH is a **complex survey**, and treating it as
a simple random sample changes both the estimates and how precise they appear.""")

    co("""import numpy as np, pandas as pd
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, cohen_kappa_score, confusion_matrix
import matplotlib.pyplot as plt
pd.set_option("display.width", 130)
print("ready")""")

    md("## Part 1a. Synthetic data from the study's aggregates")
    co(f"""PARAMS = {json.dumps(P, indent=1)}

SEED = 1

def simulate(n=None, seed=SEED):
    \"\"\"Build a dataset with the study's marginals, its logistic relationship to MDE, and a
    weight profile that varies by age, which is what makes weighting matter.\"\"\"
    rng = np.random.default_rng(seed)
    n = n or PARAMS["n"]
    d = pd.DataFrame({{c: rng.random(n) < p for c, p in PARAMS["marginals"].items()}}).astype(int)
    for col, probs in PARAMS["cat"].items():
        lv = np.array([int(k) for k in probs]); pr = np.array(list(probs.values()), float)
        d[col] = rng.choice(lv, size=n, p=pr / pr.sum())
    b = PARAMS["mde_logit"]
    lin = b["const"] + sum(d[k] * v for k, v in b.items() if k != "const")
    d["MDE"] = (rng.random(n) < 1 / (1 + np.exp(-lin))).astype(int)
    # NSDUH over-samples the young, so their weights are smaller. That is the whole point.
    wmap = {{int(k): v for k, v in PARAMS["weight_by_age"].items()}}
    d["WT"] = d.CATAG6.map(wmap) * rng.lognormal(0, .25, n)
    d["YEAR"] = rng.choice(PARAMS["years"], n)
    return d

df = simulate()
print(f"simulated {{len(df):,}} adults")
print(f"unweighted MDE: {{df.MDE.mean()*100:.2f}}%   weighted: {{np.average(df.MDE, weights=df.WT)*100:.2f}}%")
df.head()""")

    md(f"""### 1b. Using the real files instead

Download the public-use files from [SAMHSA]({SAMHSA}). Read only the columns you need: each
file has about 2,650, and reading all of them is slow and memory hungry.""")
    co("""USE_REAL_DATA = False
DATA_DIR = "."

KEEP = ["IRSEX","CATAG6","INCOME","HEALTH2","IRALCRC","IRMJRC","CIGMON",
        "AMDEYR","AMIPY","ANALWT2_C","VESTR_C","VEREP"]

def load_real(data_dir=DATA_DIR, years=(2022, 2023, 2024)):
    frames = []
    for y in years:
        d = pd.read_csv(f"{data_dir}/NSDUH_{y}_Tab.txt", sep="\\t",
                        usecols=lambda c: c in KEEP, low_memory=False)
        d["YEAR"] = y
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    d["ALC_PASTMO"] = (d.IRALCRC == 1).astype(int)
    d["MJ_PASTMO"]  = (d.IRMJRC  == 1).astype(int)
    d["CIG_PASTMO"] = (d.CIGMON  == 1).astype(int)
    d["MDE"]    = d.AMDEYR.where(d.AMDEYR.isin([1, 2])).map({1: 1, 2: 0})
    d["HEALTH"] = d.HEALTH2.where(d.HEALTH2.isin([1, 2, 3, 4]))
    d["WT"] = d.ANALWT2_C / len(years)      # pooling: divide by the number of years
    return d[d.MDE.notna() & d.HEALTH.notna()].copy()

if USE_REAL_DATA:
    df = load_real()
    print(f"loaded {len(df):,} adults")
else:
    print("using synthetic data (set USE_REAL_DATA = True once the files are downloaded)")""")

    md("""## Part 2. The survey design

Every respondent carries a weight saying how many people they represent. Unweighted, you
describe the respondents; weighted, you estimate the population. When a survey deliberately
over-samples a group whose behavior differs, the two answers differ.""")
    co("""wm = lambda s, w: float(np.average(s, weights=w))

rows = []
for c in ["ALC_PASTMO", "MJ_PASTMO", "CIG_PASTMO", "MDE"]:
    rows.append(dict(measure=c,
                     unweighted=round(df[c].mean()*100, 2),
                     weighted=round(wm(df[c], df.WT)*100, 2)))
tab = pd.DataFrame(rows)
tab["difference"] = (tab.unweighted - tab.weighted).round(2)
print(tab.to_string(index=False))

print("\\nBy age band, the two nearly agree within each band:")
for k in sorted(df.CATAG6.unique()):
    g = df[df.CATAG6 == k]
    print(f"  age code {k}: n={len(g):6,d}  unweighted {g.MDE.mean()*100:5.2f}%   "
          f"weighted {wm(g.MDE, g.WT)*100:5.2f}%")
print("\\nIt is the age MIX that differs, which is why only the overall figure moves.")""")

    md(f"""## Part 3. Reduce, then group

Seven measures on different scales, so standardize first, then take principal components and
cluster on the leading three.

> **The synthetic data understates this step.** The generator draws each variable
> independently, so there is no correlation structure for PCA to find and the components come
> out near-equal at about 1/7 each. On the real data the first three carry
> {A['pca']['cumulative'][2]:.1f}%. The code below is the right code; only the simulated input
> is uninformative here. Run it against the real files to see the actual structure.""")
    co("""VARS = ["ALC_PASTMO","MJ_PASTMO","CIG_PASTMO","IRSEX","CATAG6","INCOME","HEALTH"]
Xs = StandardScaler().fit_transform(df[VARS].astype(float))
pca = PCA(random_state=SEED).fit(Xs)
print("variance explained:", np.round(pca.explained_variance_ratio_*100, 1))
print("cumulative       :", np.round(np.cumsum(pca.explained_variance_ratio_)*100, 1))

scores = pca.transform(Xs)[:, :3]
km = KMeans(n_clusters=4, n_init=10, random_state=SEED).fit(scores)
df["cluster"] = km.labels_
print()
print(df.groupby("cluster")[["ALC_PASTMO","MJ_PASTMO","CIG_PASTMO","MDE"]].mean().mul(100).round(1))""")

    md("""### The scree plot, the correlation circle, and the elbow

Three standard PCA and clustering diagnostics. The correlation circle is the one that makes
the components interpretable: each arrow is a variable, and arrows pointing the same way are
variables that move together.""")
    co("""fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))

# scree
ev = pca.explained_variance_ratio_*100
ax[0].bar(range(1, len(ev)+1), ev, color="#2a78d6")
ax[0].plot(range(1, len(ev)+1), np.cumsum(ev), "o-", color="#1baf7a")
ax[0].set_xlabel("component"); ax[0].set_ylabel("% variance"); ax[0].set_title("Scree plot")
ax[0].grid(axis="y", alpha=.3)

# correlation circle
ax[1].add_patch(plt.Circle((0,0), 1, fill=False, color="#8b95a6"))
ax[1].axhline(0, color="#d8dee8", lw=1); ax[1].axvline(0, color="#d8dee8", lw=1)
for i, v in enumerate(VARS):
    x, y = pca.components_[0, i], pca.components_[1, i]
    ax[1].arrow(0, 0, x, y, head_width=.03, color="#2a78d6", length_includes_head=True)
    ax[1].text(x*1.12, y*1.12, v, fontsize=8, ha="center")
ax[1].set_xlim(-1.3, 1.3); ax[1].set_ylim(-1.3, 1.3); ax[1].set_aspect("equal")
ax[1].set_xlabel(f"PC1 ({ev[0]:.0f}%)"); ax[1].set_ylabel(f"PC2 ({ev[1]:.0f}%)")
ax[1].set_title("Correlation circle")

# elbow
sub = scores[np.random.default_rng(SEED).choice(len(scores), min(25000, len(scores)), replace=False)]
wss = [KMeans(n_clusters=k, n_init=5, random_state=SEED).fit(sub).inertia_ for k in range(1, 9)]
ax[2].plot(range(1, 9), wss, "o-", color="#2a78d6")
ax[2].plot(4, wss[3], "o", ms=11, color="#1baf7a")
ax[2].set_xlabel("k"); ax[2].set_ylabel("within-cluster spread"); ax[2].set_title("Elbow plot")
ax[2].grid(alpha=.3)
plt.tight_layout(); plt.show()""")

    md("""**A caution.** K-means returns four groups whether or not four groups exist. Before
reading anything into them, check that the same structure comes back on resamples.""")
    co("""rng = np.random.default_rng(SEED)
sizes = []
for _ in range(20):
    idx = rng.choice(len(scores), size=min(40000, len(scores)), replace=False)
    k2 = KMeans(n_clusters=4, n_init=5, random_state=int(rng.integers(1e6))).fit(scores[idx])
    sizes.append(np.sort(np.bincount(k2.labels_, minlength=4) / len(idx) * 100))
sizes = np.array(sizes)
print("cluster sizes over 20 resamples (sorted):")
print("  mean:", np.round(sizes.mean(axis=0), 1))
print("  sd  :", np.round(sizes.std(axis=0, ddof=1), 2))
print("\\nReproducible is not the same as real: a continuum can be cut reproducibly too.")""")

    md("""## Part 4. Prediction, and why accuracy misleads

The outcome is rare. Watch what accuracy does about that.""")
    co("""X = StandardScaler().fit_transform(df[VARS].astype(float))
y = df.MDE.astype(int).values
cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
model = LogisticRegression(solver="liblinear", l1_ratio=1, C=1.0, max_iter=2000)
prob = cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]

pred = (prob >= .5).astype(int)
print(f"AUC       {roc_auc_score(y, prob):.4f}")
print(f"accuracy  {(pred == y).mean():.4f}")
print(f"kappa     {cohen_kappa_score(y, pred):.4f}")
print(f"flagged   {pred.sum():,} of {len(y):,}   (true positives in data: {y.sum():,})")
print(f"imbalance {(y==0).sum()/(y==1).sum():.2f} to 1")
print("\\nHigh accuracy, near-zero kappa: the model is mostly saying 'no' to everyone.")""")

    co("""rows = []
for t in (0.50, 0.30, 0.20, 0.15, 0.10):
    pr = (prob >= t).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pr).ravel()
    rows.append(dict(cutoff=t, sensitivity=round(tp/(tp+fn), 3),
                     specificity=round(tn/(tn+fp), 3),
                     precision=round(tp/(tp+fp), 3) if (tp+fp) else 0.0,
                     kappa=round(cohen_kappa_score(y, pr), 3),
                     flagged_pct=round(100*pr.mean(), 1)))
thr = pd.DataFrame(rows)
print(thr.to_string(index=False))
print("\\nAUC is identical for every row: only the decision rule changed.")

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(thr.cutoff, thr.sensitivity*100, "o-", label="Sensitivity", color="#2a78d6")
ax.plot(thr.cutoff, thr.flagged_pct, "o-", label="% flagged", color="#eb6834")
ax.set_xlabel("decision threshold"); ax.set_ylabel("percent"); ax.legend(); ax.grid(alpha=.3)
ax.set_title("Lowering the cut-off finds more cases, at the cost of flagging more people")
plt.tight_layout(); plt.show()""")

    md("""### LASSO against ridge, and a tree

Two penalties, two different behaviors. LASSO can shrink a coefficient to exactly zero and
so drops variables; ridge shrinks everything but keeps it. If they agree, the result is not
an artifact of the penalty.""")
    co("""from sklearn.tree import DecisionTreeClassifier, plot_tree

Xstd = StandardScaler().fit_transform(df[VARS].astype(float))
coefs = {}
for tag, kw in (("LASSO", dict(solver="liblinear", l1_ratio=1)),
                ("Ridge", dict(solver="lbfgs", l1_ratio=0))):
    coefs[tag] = LogisticRegression(C=1.0, max_iter=2000, **kw).fit(Xstd, y).coef_[0]

comp = pd.DataFrame(coefs, index=VARS).sort_values("LASSO", key=abs, ascending=False)
print(comp.round(3).to_string())
print("\\nVariables LASSO dropped entirely:", [v for v in VARS if abs(comp.loc[v,"LASSO"]) < 1e-6] or "none")

fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
yv = np.arange(len(comp))
ax[0].barh(yv-0.2, comp.LASSO, 0.4, label="LASSO", color="#2a78d6")
ax[0].barh(yv+0.2, comp.Ridge, 0.4, label="Ridge", color="#eb6834")
ax[0].set_yticks(yv); ax[0].set_yticklabels(comp.index, fontsize=8); ax[0].invert_yaxis()
ax[0].axvline(0, color="#8b95a6", lw=1); ax[0].legend(); ax[0].set_xlabel("standardized coefficient")
ax[0].set_title("What predicts depression")

tree = DecisionTreeClassifier(max_depth=3, min_samples_leaf=500, random_state=SEED).fit(df[VARS], y)
plot_tree(tree, feature_names=VARS, class_names=["No","Yes"], filled=True,
          impurity=False, proportion=True, fontsize=6, ax=ax[1])
ax[1].set_title("Classification tree (depth 3)")
plt.tight_layout(); plt.show()
print("\\nFirst split:", VARS[tree.tree_.feature[0]], "<=", round(tree.tree_.threshold[0], 2))""")

    md("""## Part 5. What the design does to the standard errors

Respondents are drawn in clusters, so they carry less information than the same number of
independent draws. A model that ignores that reports standard errors which are too small.""")
    co("""Xd = sm.add_constant(df[VARS].astype(float))
naive = sm.GLM(y, Xd, family=sm.families.Binomial()).fit()

# With the real data, cluster on the stratum-replicate combination:
#   groups = (df.VESTR_C.astype(str) + "_" + df.VEREP.astype(str)).values
# The synthetic data has no such structure, so age band stands in as a stub.
groups = df.CATAG6.values
design = sm.GLM(y, Xd, family=sm.families.Binomial(), var_weights=df.WT.values).fit(
    cov_type="cluster", cov_kwds={"groups": groups})

comp = pd.DataFrame({"naive_se": naive.bse, "design_se": design.bse})
comp["ratio"] = (comp.design_se / comp.naive_se).round(2)
print(comp.round(5).to_string())
print("\\nOn the real data these ratios run about 1.7 to 2.0: naive intervals are roughly")
print("half the width they should be.")""")

    se = [d["se_ratio"] for d in A["design_effect"] if d["term"] != "const"]
    md(f"""## What the real analysis found

On the real files: {A['n']:,} adults, MDE {A['prevalence'][3]['weighted']}% weighted against
{A['prevalence'][3]['unweighted']}% unweighted, AUC {A['model']['auc']},
accuracy {A['model']['accuracy']*100:.1f}% with kappa {A['model']['kappa']}, and design-adjusted
standard errors {min(se):.2f}x to {max(se):.2f}x
the naive ones.

Full write-up: [{SITE}/analysis.html]({SITE}/analysis.html)""")

    nb["cells"] = C
    nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                      "language_info": {"name": "python", "version": "3.11"},
                      "colab": {"provenance": [], "toc_visible": True}}
    NOTEBOOKS.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, str(NOTEBOOKS / "nsduh_mde_analysis.ipynb"))
    print(f"  cells: {len(C)}  ->  notebooks/nsduh_mde_analysis.ipynb")

if __name__ == "__main__":
    main()

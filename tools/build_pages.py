import sys, json, html
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from paths import DERIVED, TEMPLATES, PUBLIC, SITE, BASE_URL, SAMHSA
from rhl import highlight
e = html.escape

A = json.load(open(DERIVED / "analysis.json"))
F = {n: (DERIVED / f"{n}.svg").read_text() for n in ["f1","f2","f3","f4","f5"]}
REPO = "https://github.com/johnfisher-ai/fisher-nsduh-analysis"
S, M = A["sample"], A["model"]

NAV = [("./","Overview"),("analysis.html","The analysis"),("code.html","The code"),
       ("writeup.html","The write-up"),(REPO,"Repository")]
def nav(cur):
    return "\n".join(f'    <a href="{h}"{" aria-current=\"page\"" if h==cur else ""}>{l}</a>' for h,l in NAV)

def meta(title, desc, path):
    url = f"{BASE_URL}/{path}" if path else f"{BASE_URL}/"
    img = f"{BASE_URL}/assets/img/social-card.png"
    return f'''<link rel="canonical" href="{url}">
<meta name="author" content="John Fisher">
<meta name="theme-color" content="#2f5d94">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Depression and Substance Use in the NSDUH">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="627">
<meta property="og:image:alt" content="Depression and substance use in the National Survey on Drug Use and Health, 2022 to 2024. 134,897 adults.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{img}">'''

def prev_rows():
    out=""
    for r in A["prevalence"]:
        d = r["unweighted"] - r["weighted"]
        out += (f'<tr><td class="item">{e(r["measure"])}</td>'
                f'<td class="num">{r["unweighted"]:.2f}%</td><td class="num">{r["weighted"]:.2f}%</td>'
                f'<td class="num">{d:+.2f}</td></tr>')
    return out

def mde_rows():
    out=""
    for b in A["mde_by"]:
        out += f'<tr class="tag-row"><td class="item" colspan="4"><strong>{e(b["name"])}</strong></td></tr>'
        for r in b["rows"]:
            out += (f'<tr><td class="item">&nbsp;&nbsp;{e(r["level"])}</td><td class="num">{r["n"]:,}</td>'
                    f'<td class="num">{r["unweighted"]:.2f}%</td><td class="num">{r["weighted"]:.2f}%</td></tr>')
    return out

def cluster_rows():
    out=""
    for i,c in enumerate(A["clusters"],1):
        out += (f'<tr><td class="item">Cluster {i}</td><td class="num">{c["n"]:,}</td>'
                f'<td class="num">{c["pct"]}%</td><td class="num">{c["alc"]}%</td>'
                f'<td class="num">{c["mj"]}%</td><td class="num">{c["cig"]}%</td>'
                f'<td class="num">{c["mde"]}%</td></tr>')
    return out

def thresh_rows():
    out=""
    for t in A["thresholds"]:
        tag=' class="tag-row"' if t["t"]==0.50 else ""
        out += (f'<tr{tag}><td class="num">{t["t"]:.2f}</td>'
                f'<td class="num">{t["sensitivity"]*100:.1f}%</td>'
                f'<td class="num">{t["specificity"]*100:.1f}%</td>'
                f'<td class="num">{t["precision"]*100:.1f}%</td>'
                f'<td class="num">{t["kappa"]:.3f}</td>'
                f'<td class="num">{t["flagged"]:,} ({t["flagged_pct"]:.0f}%)</td></tr>')
    return out

def se_rows():
    out=""
    for d in A["design_effect"]:
        if d["term"]=="const": continue
        out += (f'<tr><td class="item">{e(d["term"])}</td>'
                f'<td class="num">{d["naive_se"]:.5f}</td><td class="num">{d["design_se"]:.5f}</td>'
                f'<td class="num">&times;{d["se_ratio"]:.2f}</td></tr>')
    return out

def pca_rows():
    out=""
    for i,v in enumerate(A["pca"]["explained"][:5],1):
        out += (f'<tr><td class="item">PC{i}</td><td class="num">{v:.2f}%</td>'
                f'<td class="num">{A["pca"]["cumulative"][i-1]:.2f}%</td></tr>')
    return out

CTX = dict(
    f1=F["f1"], f2=F["f2"], f3=F["f3"], f4=F["f4"], f5=F["f5"], repo=REPO, samhsa=SAMHSA,
    prev_rows=prev_rows(), mde_rows=mde_rows(), cluster_rows=cluster_rows(),
    thresh_rows=thresh_rows(), se_rows=se_rows(), pca_rows=pca_rows(),
    n=f'{A["n"]:,}', pooled=f'{S["pooled"]:,}', adolescents=f'{S["adolescents_excluded"]:,}',
    adults_missing=f'{S["adults_missing_outcome"]:,}',
    mde_u=f'{A["prevalence"][3]["unweighted"]:.2f}', mde_w=f'{A["prevalence"][3]["weighted"]:.2f}',
    mj_u=f'{A["prevalence"][1]["unweighted"]:.2f}', mj_w=f'{A["prevalence"][1]["weighted"]:.2f}',
    auc=M["auc"], acc=f'{M["accuracy"]*100:.1f}', kappa=M["kappa"],
    pos=f'{M["predicted_positive"]:,}', imb=M["imbalance_ratio"],
    pca3=f'{A["pca"]["cumulative"][2]:.1f}',
    mj_cluster_pct=A["clusters"][0]["pct"], mj_cluster_mj=A["clusters"][0]["mj"],
    mj_cluster_mde=A["clusters"][0]["mde"],
    se_min=min(d["se_ratio"] for d in A["design_effect"] if d["term"]!="const"),
    se_max=max(d["se_ratio"] for d in A["design_effect"] if d["term"]!="const"),
    stab=", ".join(f'{m:.0f}%' for m in A["cluster_stability"]["sorted_sizes_mean"]),
    stab_sd=max(A["cluster_stability"]["sorted_sizes_sd"]),
    r_lines=len((SITE/"R"/"nsduh_mde_analysis.R").read_text().splitlines()),
    r_source=highlight((SITE/"R"/"nsduh_mde_analysis.R").read_text()),
    colab=("https://colab.research.google.com/github/johnfisher-ai/"
           "fisher-nsduh-analysis/blob/main/notebooks/nsduh_mde_analysis.ipynb"),
    sens50=f'{A["thresholds"][0]["sensitivity"]*100:.1f}',
    sens20=f'{[t for t in A["thresholds"] if t["t"]==0.20][0]["sensitivity"]*100:.0f}',
    flag20=f'{[t for t in A["thresholds"] if t["t"]==0.20][0]["flagged_pct"]:.0f}',
)

PAGES = [
 ("index.html","","Depression and Substance Use in the NSDUH",
  "Three years of the National Survey on Drug Use and Health, 134,897 adults, analysed for the link between substance use and major depressive episode."),
 ("analysis.html","analysis.html","The Statistical Analysis",
  "Descriptives computed weighted and unweighted, PCA and clustering with a stability check, and a classifier whose accuracy hides that it never predicts the outcome."),
 ("code.html","code.html","The Code",
  "The R pipeline behind the analysis, with a Python notebook that reproduces it."),
 ("writeup.html","writeup.html","The Write-Up",
  "A plain-language walkthrough of what was done, why, and what the results support."),
]

if __name__ == "__main__":
    for f, path, title, desc in PAGES:
        t = (TEMPLATES / f).read_text()
        (PUBLIC / f).write_text(t.format(meta=meta(title, desc, path), nav=nav(path or "./"), **CTX),
                                encoding="utf-8")
        print(f"  {f:16s} {len((PUBLIC/f).read_text()):7,d} bytes")

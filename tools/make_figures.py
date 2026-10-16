"""Site charts as inline SVG, so they follow the reader's light/dark setting.
    derived/analysis.json -> derived/f1..f5.svg"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from paths import DERIVED
import chart
from chart import T, esc

A = json.load(open(DERIVED / "analysis.json"))

def _axis(s, x0, x1, y0, y1, ticks, X, label, H):
    for v, lab in ticks:
        gx = X(v)
        s.append(f'<line class="grid" x1="{gx:.1f}" y1="{y1}" x2="{gx:.1f}" y2="{y0}"/>')
        s.append(T(gx, H - 16, lab, "ax", "middle"))
    s.append(T((x0 + x1) / 2, H - 2, label, "ax", "middle"))

def legend_right(items, right, y=7, size=11.5, gap=18):
    """Legend swatches and labels laid out leftward from `right`, spaced by label length.

    Widths are estimated at 0.62 em a character, wider than the site's fonts set them, so a
    long label such as "Unweighted (sample)" never runs into the next swatch."""
    out, x = [], right
    for label, cls in reversed(items):
        tx = x - len(label) * size * 0.62
        out.append(f'<rect x="{tx-14:.1f}" y="{y}" width="10" height="10" rx="2" class="{cls}"/>'
                   + T(tx, y + 9, label, "leg"))
        x = tx - 14 - gap
    return out[::-1]

def paired_bars(rows, title, sub, axis_label, hi, legend, W=800, L=250, R=110, TOP=64, ROW=34):
    """rows: [(label, value_a, value_b)] drawn as two bars per row."""
    H = TOP + ROW * len(rows) + 34
    x0, x1, y1 = L, W - R, TOP - 14
    y0 = TOP + ROW * len(rows) - 18
    X = lambda v: x0 + v / hi * (x1 - x0)
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}">',
         T(0, 16, title, "ttl"), T(0, 33, sub, "sub"),
         *legend_right([(legend[0], "m2f"), (legend[1], "m1f")], W - 8)]
    step = max(5, int(hi / 5 // 5 * 5))
    _axis(s, x0, x1, y0, y1, [(v, f"{v}%") for v in range(0, int(hi) + 1, step)], X, axis_label, H)
    for i, (lab, u, w) in enumerate(rows):
        y = TOP + i * ROW
        s.append(T(L - 14, y + 4, lab, "lab", "end"))
        s.append(f'<rect class="m2f" x="{x0}" y="{y-11}" width="{max(X(u)-x0,1):.1f}" height="10" rx="2"/>')
        s.append(f'<rect class="m1f" x="{x0}" y="{y+2}" width="{max(X(w)-x0,1):.1f}" height="10" rx="2"/>')
        s.append(T(max(X(u), X(w)) + 10, y + 6, f"{u:.1f}%  /  {w:.1f}%", "val halo"))
    s.append(f'<line class="axis" x1="{x0}" y1="{y1}" x2="{x0}" y2="{y0}"/>')
    return "\n".join(s) + "\n</svg>"

def fig_prevalence():
    rows = [(r["measure"].split(",")[0], r["unweighted"], r["weighted"]) for r in A["prevalence"]]
    return paired_bars(rows, "What the survey design changes",
        "Every estimate computed two ways from the same respondents. Weighted is the population estimate.",
        "Percent", 60, ("Unweighted (sample)", "Weighted (population)"))

def fig_mde_by_age():
    b = next(x for x in A["mde_by"] if x["name"] == "Age band")
    rows = [(r["level"], r["unweighted"], r["weighted"]) for r in b["rows"]]
    return paired_bars(rows, "Depression by age, both ways",
        "Within an age band the two agree. The overall rate does not, because the sample over-represents the young.",
        "Percent with past-year MDE", 20, ("Unweighted", "Weighted"), L=150, ROW=32)

def fig_clusters():
    C = A["clusters"]
    W, H, L, R, TOP, ROW = 820, 300, 210, 150, 74, 44
    x0, x1 = L, W - R
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-label="Substance use by cluster">',
         T(0, 16, "Four groups, and what separates them", "ttl"),
         T(0, 33, "Past-month use within each cluster. One group is defined almost entirely by marijuana.", "sub")]
    keys = [("alc", "Alcohol", "m1f"), ("mj", "Marijuana", "m2f"), ("cig", "Cigarettes", "m3f")]
    for j, (k, lab, cls) in enumerate(keys):
        cx = x1 - 250 + j * 88
        s.append(f'<rect x="{cx}" y="7" width="10" height="10" rx="2" class="{cls}"/>{T(cx+14,16,lab,"leg")}')
    for v in (0, 25, 50, 75, 100):  # gridlines first, so the bars sit on top of them
        gx = x0 + v / 100 * (x1 - x0)
        s.append(f'<line class="grid" x1="{gx:.1f}" y1="{TOP-16}" x2="{gx:.1f}" y2="{TOP+ROW*len(C)-30}"/>')
        s.append(T(gx, H - 16, f"{v}%", "ax", "middle"))
    for i, c in enumerate(C):
        y = TOP + i * ROW
        s.append(T(L - 14, y + 2, f'Cluster {i+1}', "lab bold", "end"))
        s.append(T(L - 14, y + 15, f'{c["pct"]}% of sample, n={c["n"]:,}', "ax", "end"))
        for j, (k, lab, cls) in enumerate(keys):
            v = c[k]; yy = y - 9 + j * 9
            s.append(f'<rect class="{cls}" x="{x0}" y="{yy}" width="{max(v/100*(x1-x0),1):.1f}" height="7" rx="2"/>')
        s.append(T(x1 + 10, y + 6, f'MDE {c["mde"]}%', "val"))
    s.append(T((x0 + x1) / 2, H - 2, "Percent of cluster reporting past-month use", "ax", "middle"))
    return "\n".join(s) + "\n</svg>"

def fig_threshold():
    Tt = A["thresholds"]
    W, H, L, R, TOP, ROW = 800, 290, 130, 150, 70, 36
    x0, x1 = L, W - R
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-label="Sensitivity by decision threshold">',
         T(0, 16, "The model ranks well; the default cut-off throws that away", "ttl"),
         T(0, 33, "Same model, same AUC. Only the probability at which a case is flagged changes.", "sub"),
         f'<rect x="{x1-186}" y="7" width="10" height="10" rx="2" class="m1f"/>{T(x1-172,16,"Sensitivity","leg")}',
         f'<rect x="{x1-86}" y="7" width="10" height="10" rx="2" class="m2f"/>{T(x1-72,16,"% flagged","leg")}']
    for v in (0, 25, 50, 75, 100):  # gridlines first, so the bars sit on top of them
        gx = x0 + v / 100 * (x1 - x0)
        s.append(f'<line class="grid" x1="{gx:.1f}" y1="{TOP-16}" x2="{gx:.1f}" y2="{TOP+ROW*len(Tt)-22}"/>')
        s.append(T(gx, H - 16, f"{v}%", "ax", "middle"))
    for i, t in enumerate(Tt):
        y = TOP + i * ROW
        s.append(T(L - 14, y + 4, f'cut at {t["t"]:.2f}', "lab", "end"))
        s.append(f'<rect class="m1f" x="{x0}" y="{y-11}" width="{max(t["sensitivity"]*(x1-x0),1):.1f}" height="10" rx="2"/>')
        s.append(f'<rect class="m2f" x="{x0}" y="{y+2}" width="{max(t["flagged_pct"]/100*(x1-x0),1):.1f}" height="10" rx="2"/>')
        s.append(T(x1 + 10, y + 6, f'sens {t["sensitivity"]*100:.0f}%, flags {t["flagged_pct"]:.0f}%', "val"))
    s.append(T((x0 + x1) / 2, H - 2, "Percent", "ax", "middle"))
    return "\n".join(s) + "\n</svg>"

def fig_se():
    D = [d for d in A["design_effect"] if d["term"] != "const"]
    W, H, L, R, TOP, ROW = 800, 320, 190, 130, 68, 32
    x0, x1 = L, W - R
    hi = 2.2
    X = lambda v: x0 + v / hi * (x1 - x0)
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-label="Standard error inflation">',
         T(0, 16, "How far out the standard errors are when the design is ignored", "ttl"),
         T(0, 33, "Ratio of design-adjusted to naive standard error. 1.0 would mean no difference.", "sub")]
    # Gridlines go behind the bars. The dashed 1.0 reference line is drawn over them, and the
    # value labels carry a halo, so no line runs through a label.
    ticks = [(1.0, "1.0 (no effect)"), (1.5, "1.5"), (2.0, "2.0")]
    for v, lab in ticks[1:]:
        gx = X(v)
        s.append(f'<line class="grid" x1="{gx:.1f}" y1="{TOP-16}" x2="{gx:.1f}" y2="{TOP+ROW*len(D)-10}"/>')
    for i, d in enumerate(D):
        y = TOP + i * ROW
        s.append(T(L - 14, y + 4, d["term"], "lab", "end"))
        s.append(f'<rect class="m1f" x="{x0}" y="{y-8}" width="{max(X(d["se_ratio"])-x0,1):.1f}" height="16" rx="3"/>')
    gx = X(1.0)
    s.append(f'<line class="zero" x1="{gx:.1f}" y1="{TOP-16}" x2="{gx:.1f}" y2="{TOP+ROW*len(D)-10}"/>')
    for i, d in enumerate(D):
        s.append(T(X(d["se_ratio"]) + 10, TOP + i * ROW + 5, f'x{d["se_ratio"]:.2f}', "val halo"))
    for v, lab in ticks:
        s.append(T(X(v), TOP + ROW*len(D) + 8, lab, "ax", "middle"))
    s.append(T((x0 + x1) / 2, H - 8, "Standard error, design-adjusted relative to naive", "ax", "middle"))
    return "\n".join(s) + "\n</svg>"



# ---------------------------------------------------------------------------
# Descriptive figures
# ---------------------------------------------------------------------------
def fig_missing():
    M = [m for m in A["missing"]]
    W, H, L, R, TOP, ROW = 800, 300, 150, 150, 66, 24
    x0, x1 = L, W - R
    hi = max(m["missing"] for m in M) * 1.05 or 1
    X = lambda v: x0 + v / hi * (x1 - x0)
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-label="Missing values by variable">',
         T(0, 16, "Where the data is missing", "ttl"),
         T(0, 33, "Records with no value, out of the pooled file. Two variables account for almost all of it.", "sub")]
    for i, m in enumerate(M):
        y = TOP + i * ROW
        s.append(T(L - 14, y + 4, m["var"], "lab", "end"))
        w = max(X(m["missing"]) - x0, 1)
        s.append(f'<rect class="{"m2f" if m["missing"] > 1000 else "m1f"}" x="{x0}" y="{y-7}" width="{w:.1f}" height="14" rx="2"/>')
        s.append(T(x0 + w + 10, y + 5, f'{m["missing"]:,}' if m["missing"] else "none", "val"))
    s.append(f'<line class="axis" x1="{x0}" y1="{TOP-14}" x2="{x0}" y2="{TOP+ROW*len(M)-14}"/>')
    s.append(T((x0 + x1) / 2, H - 6, "Records with a missing value", "ax", "middle"))
    return "\n".join(s) + "\n</svg>"

def fig_by_year():
    P = A["prevalence"]; years = [y["year"] for y in P[0]["by_year"]]
    W, H, L, R, TOP, B = 800, 330, 60, 20, 74, 60
    x0, x1, y0, y1 = L, W - R, H - B, TOP
    Y = lambda v: y0 - v / 60 * (y0 - y1)
    slot = (x1 - x0) / len(P)
    cls = ["m1f", "m2f", "m3f", "m4f"]
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-label="Prevalence by year">',
         T(0, 16, "Substance use and depression, by survey year", "ttl"),
         T(0, 33, "Weighted to the population. Three years, and very little movement between them.", "sub")]
    for j, y in enumerate(years):
        cx = x1 - 200 + j * 66
        s.append(f'<rect x="{cx}" y="7" width="10" height="10" rx="2" class="{cls[j]}"/>{T(cx+14,16,str(y),"leg")}')
    for v in range(0, 61, 15):
        s.append(f'<line class="grid" x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}"/>')
        s.append(T(x0 - 8, Y(v) + 4, f"{v}%", "ax", "end"))
    for i, m in enumerate(P):
        cx = x0 + i * slot + slot / 2
        bw = min(26, (slot - 30) / len(years))
        for j, yr in enumerate(m["by_year"]):
            bx = cx - (len(years) * bw) / 2 + j * bw
            s.append(f'<rect class="{cls[j]}" x="{bx:.1f}" y="{Y(yr["weighted"]):.1f}" '
                     f'width="{bw-3:.1f}" height="{y0-Y(yr["weighted"]):.1f}" rx="2"/>')
        s.append(T(cx, y0 + 20, m["measure"].split(",")[0], "ax", "middle"))
        s.append(T(cx, y0 + 34, f'{m["weighted"]:.1f}% overall', "ax", "middle"))
    s.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}"/>')
    return "\n".join(s) + "\n</svg>"

def fig_who():
    """MDE by sex and by income, weighted. Age has its own figure."""
    groups = [b for b in A["mde_by"] if b["name"] in ("Sex", "Household income")]
    W, L, R, TOP, ROW = 800, 200, 130, 66, 30
    rows = sum(len(g["rows"]) for g in groups) + len(groups)
    H = TOP + ROW * rows + 30
    x0, x1 = L, W - R
    hi = 20
    X = lambda v: x0 + v / hi * (x1 - x0)
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-label="Depression by sex and income">',
         T(0, 16, "Who reports depression", "ttl"),
         T(0, 33, "Weighted percent with a past-year major depressive episode.", "sub")]
    for v in range(0, 21, 5):  # gridlines first, so the bars and labels sit on top of them
        s.append(f'<line class="grid" x1="{X(v):.1f}" y1="{TOP-14}" x2="{X(v):.1f}" y2="{TOP+ROW*rows-16}"/>')
        s.append(T(X(v), H - 12, f"{v}%", "ax", "middle"))
    i = 0
    for g in groups:
        s.append(T(L - 14, TOP + i * ROW + 4, g["name"], "lab bold", "end")); i += 1
        for r in g["rows"]:
            y = TOP + i * ROW
            s.append(T(L - 14, y + 4, r["level"], "lab", "end"))
            w = max(X(r["weighted"]) - x0, 1)
            s.append(f'<rect class="m1f" x="{x0}" y="{y-8}" width="{w:.1f}" height="16" rx="2"/>')
            s.append(T(x0 + w + 10, y + 5, f'{r["weighted"]:.1f}%   n={r["n"]:,}', "val halo")); i += 1
    return "\n".join(s) + "\n</svg>"

def fig_balance():
    B = A["balance"]
    W, H = 800, 210
    x0, x1, y = 60, 740, 108
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-label="Outcome class balance">',
         T(0, 16, "The outcome is rare, and that is the whole problem", "ttl"),
         T(0, 33, "Adults in the analysis sample, by whether they reported a past-year episode.", "sub")]
    total = B["no"] + B["yes"]
    wno = (B["no"] / total) * (x1 - x0)
    s.append(f'<rect class="m1f" x="{x0}" y="{y-26}" width="{wno:.1f}" height="52" rx="4"/>')
    s.append(f'<rect class="m2f" x="{x0+wno:.1f}" y="{y-26}" width="{(x1-x0)-wno:.1f}" height="52" rx="4"/>')
    s.append(T(x0 + wno / 2, y + 5, f'No  {B["no"]:,}  ({B["pct_no"]}%)', "val", "middle"))
    s.append(T(x0 + wno + ((x1 - x0) - wno) / 2, y + 5, f'{B["pct_yes"]}%', "val", "middle"))
    s.append(T(x1, y + 46, f'Yes: {B["yes"]:,} people', "ax", "end"))
    s.append(T(x0, y + 46, "A model that answers \u201cno\u201d to everyone is right 88.7% of the time.", "ax"))
    return "\n".join(s) + "\n</svg>"

# ---------------------------------------------------------------------------
# PCA and clustering
# ---------------------------------------------------------------------------
def fig_scree():
    E = A["pca"]["explained"]; Cu = A["pca"]["cumulative"]
    W, H, L, R, TOP, B = 800, 300, 56, 24, 66, 54
    x0, x1, y0, y1 = L, W - R, H - B, TOP
    Y = lambda v: y0 - v / 100 * (y0 - y1)
    slot = (x1 - x0) / len(E)
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-label="Scree plot">',
         T(0, 16, "How much each component carries", "ttl"),
         T(0, 33, f"Bars are variance per component, the line is the running total. Three reach {Cu[2]:.0f}%.", "sub")]
    for v in range(0, 101, 25):
        s.append(f'<line class="grid" x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}"/>')
        s.append(T(x0 - 8, Y(v) + 4, f"{v}%", "ax", "end"))
    pts = []
    for i, v in enumerate(E):
        cx = x0 + i * slot + slot / 2
        s.append(f'<rect class="m1f" x="{cx-16:.1f}" y="{Y(v):.1f}" width="32" height="{y0-Y(v):.1f}" rx="2"/>')
        s.append(T(cx, Y(v) - 7, f"{v:.0f}%", "val halo", "middle"))
        s.append(T(cx, y0 + 20, f"PC{i+1}", "ax", "middle"))
        pts.append(f"{cx:.1f},{Y(Cu[i]):.1f}")
    s.append(f'<polyline class="ci" fill="none" points="{" ".join(pts)}"/>')
    for i, pt in enumerate(pts):
        cx, cy = pt.split(",")
        s.append(f'<circle cx="{cx}" cy="{cy}" r="3.5" class="m3"/>')
    s.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}"/>')
    return "\n".join(s) + "\n</svg>"

def fig_circle():
    Ld = A["pca"]["loadings"]; E = A["pca"]["explained"]
    W, H = 800, 420
    cx, cy, rad = 400, 215, 150
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-label="PCA correlation circle">',
         T(0, 16, "What the first two components mean", "ttl"),
         T(0, 33, "Each arrow is one variable. Arrows pointing the same way move together; opposite ways, apart.", "sub")]
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{rad}" fill="none" class="axis"/>')
    s.append(f'<line class="grid" x1="{cx-rad}" y1="{cy}" x2="{cx+rad}" y2="{cy}"/>')
    s.append(f'<line class="grid" x1="{cx}" y1="{cy-rad}" x2="{cx}" y2="{cy+rad}"/>')
    for v in Ld:
        ex, ey = cx + v["pc1"] * rad, cy - v["pc2"] * rad
        s.append(f'<line class="ci" x1="{cx}" y1="{cy}" x2="{ex:.1f}" y2="{ey:.1f}"/>')
        s.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="3.5" class="m1"/>')
        anchor = "start" if ex >= cx else "end"
        off = 8 if ex >= cx else -8
        s.append(T(ex + off, ey + (4 if ey > cy else -6), v["var"], "val", anchor))
    s.append(T(cx, cy + rad + 30, f"PC1  ({E[0]:.0f}% of variance)", "ax", "middle"))
    s.append(f'<text class="ax" transform="rotate(-90 {cx-rad-26} {cy})" x="{cx-rad-26}" y="{cy}" text-anchor="middle">PC2  ({E[1]:.0f}%)</text>')
    return "\n".join(s) + "\n</svg>"

def fig_elbow():
    E = A["elbow"]
    W, H, L, R, TOP, B = 800, 300, 70, 30, 66, 54
    x0, x1, y0, y1 = L, W - R, H - B, TOP
    hi = max(e["wss"] for e in E)
    X = lambda k: x0 + (k - 1) / (len(E) - 1) * (x1 - x0)
    Y = lambda v: y0 - v / hi * (y0 - y1)
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-label="K-means elbow plot">',
         T(0, 16, "Choosing how many groups", "ttl"),
         T(0, 33, "Tightness of the clusters as k increases. The bend is where extra groups stop paying.", "sub")]
    for f in (0, .25, .5, .75, 1):
        s.append(f'<line class="grid" x1="{x0}" y1="{Y(hi*f):.1f}" x2="{x1}" y2="{Y(hi*f):.1f}"/>')
    pts = " ".join(f"{X(e['k']):.1f},{Y(e['wss']):.1f}" for e in E)
    s.append(f'<polyline class="ci" fill="none" points="{pts}"/>')
    for e in E:
        acc = e["k"] == 4
        s.append(f'<circle cx="{X(e["k"]):.1f}" cy="{Y(e["wss"]):.1f}" r="{6 if acc else 4}" class="{"m3" if acc else "m1"}"/>')
        s.append(T(X(e["k"]), y0 + 20, e["k"], "ax", "middle"))
    s.append(T(X(4), Y(next(e["wss"] for e in E if e["k"] == 4)) - 16, "k = 4 chosen", "val", "middle"))
    s.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}"/>')
    s.append(T((x0 + x1) / 2, H - 6, "Number of clusters (k)", "ax", "middle"))
    s.append(f'<text class="ax" transform="rotate(-90 18 {(y0+y1)/2:.0f})" x="18" y="{(y0+y1)/2:.0f}" text-anchor="middle">Within-cluster spread</text>')
    return "\n".join(s) + "\n</svg>"

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
def fig_penalised():
    P = A["penalised"]
    W, L, R, TOP, ROW = 800, 160, 150, 70, 34
    H = TOP + ROW * len(P) + 34
    mid = L + (W - R - L) / 2
    half = (W - R - L) / 2
    hi = max(max(abs(p["lasso"]), abs(p["ridge"])) for p in P) * 1.15
    X = lambda v: mid + v / hi * half
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-label="LASSO against ridge coefficients">',
         T(0, 16, "What predicts depression, and how the two penalties compare", "ttl"),
         T(0, 33, "Standardized coefficients. Right of the line raises risk, left lowers it.", "sub"),
         f'<rect x="{W-R+4}" y="7" width="10" height="10" rx="2" class="m1f"/>{T(W-R+18,16,"LASSO","leg")}',
         f'<rect x="{W-R+72}" y="7" width="10" height="10" rx="2" class="m2f"/>{T(W-R+86,16,"Ridge","leg")}']
    for i, p in enumerate(P):
        y = TOP + i * ROW
        s.append(T(L - 14, y + 4, p["var"], "lab", "end"))
        for j, (k, cls) in enumerate((("lasso", "m1f"), ("ridge", "m2f"))):
            v = p[k]; x = X(v); yy = y - 11 + j * 12
            s.append(f'<rect class="{cls}" x="{min(mid,x):.1f}" y="{yy}" width="{abs(x-mid):.1f}" height="10" rx="2"/>')
        s.append(T(X(max(p["lasso"], p["ridge"], key=abs)) + (12 if p["lasso"] >= 0 else -12),
                   y + 5, f'{p["lasso"]:+.2f}', "val", "start" if p["lasso"] >= 0 else "end"))
    s.append(f'<line class="zero" x1="{mid:.1f}" y1="{TOP-16}" x2="{mid:.1f}" y2="{TOP+ROW*len(P)-18}"/>')
    s.append(T(mid, H - 8, "Standardized coefficient (log-odds)", "ax", "middle"))
    return "\n".join(s) + "\n</svg>"

def fig_tree():
    root = A["tree"]["structure"]
    W, H = 860, 390
    lvl_y = [66, 152, 244, 336]

    # Collect nodes by depth, then space each level evenly across the width. Recursive
    # halving crowds the deepest level badly once there are eight boxes.
    levels = {}
    def walk(nd, depth):
        levels.setdefault(depth, []).append(nd)
        if "left" in nd and depth + 1 < len(lvl_y):
            walk(nd["left"], depth + 1); walk(nd["right"], depth + 1)
    walk(root, 0)

    pos = {}
    for depth, nodes in levels.items():
        n = len(nodes)
        for i, nd in enumerate(nodes):
            pos[id(nd)] = ((i + 0.5) * W / n, lvl_y[depth])

    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-label="Classification tree">',
         T(0, 16, "The classification tree, top three splits", "ttl"),
         T(0, 33, "Each box shows the share of people reaching it and how many of them reported depression.", "sub")]
    for depth, nodes in levels.items():
        for nd in nodes:
            x, y = pos[id(nd)]
            for side in ("left", "right"):
                if side in nd and id(nd[side]) in pos:
                    x2, y2 = pos[id(nd[side])]
                    s.append(f'<line class="conn" x1="{x:.1f}" y1="{y+17}" x2="{x2:.1f}" y2="{y2-17}"/>')
    for depth, nodes in levels.items():
        bw = min(112, W / len(nodes) - 8)
        for nd in nodes:
            x, y = pos[id(nd)]
            cls = "m2f" if nd["p_yes"] >= 18 else ("m1f" if nd["p_yes"] >= 11 else "")
            fill = f'class="{cls}" opacity="0.45"' if cls else 'fill="none"'
            s.append(f'<rect x="{x-bw/2:.1f}" y="{y-17}" width="{bw:.1f}" height="34" rx="5" '
                     f'{fill} stroke="var(--fig-axis)"/>')
            s.append(T(x, y - 3, nd.get("split", f'{nd["pct"]}%'), "val", "middle",
                       size=11 if depth == 3 else None))
            s.append(T(x, y + 11, f'{nd["p_yes"]}% dep.', "ax", "middle", size=10 if depth == 3 else None))
    s.append(T(W / 2, H - 6, "Shaded boxes have above-average depression rates", "ax", "middle"))
    return "\n".join(s) + "\n</svg>"


if __name__ == "__main__":
    for n, fn in [("f1", fig_prevalence), ("f2", fig_mde_by_age), ("f3", fig_clusters),
                  ("f4", fig_threshold), ("f5", fig_se), ("f6", fig_missing),
                  ("f7", fig_by_year), ("f8", fig_who), ("f9", fig_balance),
                  ("f10", fig_scree), ("f11", fig_circle), ("f12", fig_elbow),
                  ("f13", fig_penalised), ("f14", fig_tree)]:
        svg = fn(); (DERIVED / f"{n}.svg").write_text(svg)
        print(f"  {n}.svg  {len(svg):6d} chars")

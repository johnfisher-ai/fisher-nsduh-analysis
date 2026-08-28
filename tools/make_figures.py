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

def paired_bars(rows, title, sub, axis_label, hi, legend, W=800, L=250, R=110, TOP=64, ROW=34):
    """rows: [(label, value_a, value_b)] drawn as two bars per row."""
    H = TOP + ROW * len(rows) + 34
    x0, x1, y1 = L, W - R, TOP - 14
    y0 = TOP + ROW * len(rows) - 18
    X = lambda v: x0 + v / hi * (x1 - x0)
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}">',
         T(0, 16, title, "ttl"), T(0, 33, sub, "sub"),
         f'<rect x="{x1-120}" y="7" width="10" height="10" rx="2" class="m2f"/>{T(x1-106,16,legend[0],"leg")}',
         f'<rect x="{x1-40}" y="7" width="10" height="10" rx="2" class="m1f"/>{T(x1-26,16,legend[1],"leg")}']
    step = max(5, int(hi / 5 // 5 * 5))
    _axis(s, x0, x1, y0, y1, [(v, f"{v}%") for v in range(0, int(hi) + 1, step)], X, axis_label, H)
    for i, (lab, u, w) in enumerate(rows):
        y = TOP + i * ROW
        s.append(T(L - 14, y + 4, lab, "lab", "end"))
        s.append(f'<rect class="m2f" x="{x0}" y="{y-11}" width="{max(X(u)-x0,1):.1f}" height="10" rx="2"/>')
        s.append(f'<rect class="m1f" x="{x0}" y="{y+2}" width="{max(X(w)-x0,1):.1f}" height="10" rx="2"/>')
        s.append(T(max(X(u), X(w)) + 10, y + 6, f"{u:.1f}%  /  {w:.1f}%", "val"))
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
    for i, c in enumerate(C):
        y = TOP + i * ROW
        s.append(T(L - 14, y + 2, f'Cluster {i+1}', "lab bold", "end"))
        s.append(T(L - 14, y + 15, f'{c["pct"]}% of sample, n={c["n"]:,}', "ax", "end"))
        for j, (k, lab, cls) in enumerate(keys):
            v = c[k]; yy = y - 9 + j * 9
            s.append(f'<rect class="{cls}" x="{x0}" y="{yy}" width="{max(v/100*(x1-x0),1):.1f}" height="7" rx="2"/>')
        s.append(T(x1 + 10, y + 6, f'MDE {c["mde"]}%', "val"))
    for v in (0, 25, 50, 75, 100):
        gx = x0 + v / 100 * (x1 - x0)
        s.append(f'<line class="grid" x1="{gx:.1f}" y1="{TOP-16}" x2="{gx:.1f}" y2="{TOP+ROW*len(C)-30}"/>')
        s.append(T(gx, H - 16, f"{v}%", "ax", "middle"))
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
    for i, t in enumerate(Tt):
        y = TOP + i * ROW
        s.append(T(L - 14, y + 4, f'cut at {t["t"]:.2f}', "lab", "end"))
        s.append(f'<rect class="m1f" x="{x0}" y="{y-11}" width="{max(t["sensitivity"]*(x1-x0),1):.1f}" height="10" rx="2"/>')
        s.append(f'<rect class="m2f" x="{x0}" y="{y+2}" width="{max(t["flagged_pct"]/100*(x1-x0),1):.1f}" height="10" rx="2"/>')
        s.append(T(x1 + 10, y + 6, f'sens {t["sensitivity"]*100:.0f}%, flags {t["flagged_pct"]:.0f}%', "val"))
    for v in (0, 25, 50, 75, 100):
        gx = x0 + v / 100 * (x1 - x0)
        s.append(f'<line class="grid" x1="{gx:.1f}" y1="{TOP-16}" x2="{gx:.1f}" y2="{TOP+ROW*len(Tt)-22}"/>')
        s.append(T(gx, H - 16, f"{v}%", "ax", "middle"))
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
    for i, d in enumerate(D):
        y = TOP + i * ROW
        s.append(T(L - 14, y + 4, d["term"], "lab", "end"))
        s.append(f'<rect class="m1f" x="{x0}" y="{y-8}" width="{max(X(d["se_ratio"])-x0,1):.1f}" height="16" rx="3"/>')
        s.append(T(X(d["se_ratio"]) + 10, y + 5, f'x{d["se_ratio"]:.2f}', "val"))
    for v, lab in [(1.0, "1.0 (no effect)"), (1.5, "1.5"), (2.0, "2.0")]:
        gx = X(v)
        s.append(f'<line class="{"zero" if v==1.0 else "grid"}" x1="{gx:.1f}" y1="{TOP-16}" x2="{gx:.1f}" y2="{TOP+ROW*len(D)-10}"/>')
        s.append(T(gx, TOP + ROW*len(D) + 8, lab, "ax", "middle"))
    s.append(T((x0 + x1) / 2, H - 8, "Standard error, design-adjusted relative to naive", "ax", "middle"))
    return "\n".join(s) + "\n</svg>"

if __name__ == "__main__":
    for n, fn in [("f1", fig_prevalence), ("f2", fig_mde_by_age), ("f3", fig_clusters),
                  ("f4", fig_threshold), ("f5", fig_se)]:
        svg = fn(); (DERIVED / f"{n}.svg").write_text(svg)
        print(f"  {n}.svg  {len(svg):6d} chars")

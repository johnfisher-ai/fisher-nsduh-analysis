"""SVG chart primitives.

The palette is not a matter of taste: these six values pass colorblind-separation and
contrast checks against both the light and the dark page surface. Re-validate before
substituting anything, with the dataviz skill's validate_palette.js or an equivalent.

    light  s1 #2a78d6  s2 #eb6834  s3 #1baf7a
    dark   s1 #3987e5  s2 #d95926  s3 #199e70

Charts emit inline SVG that inherits colour from CSS custom properties defined in
public/assets/css/site.css, so a chart follows the reader's light/dark setting instead of
being baked to one theme. That is why these are hand-built rather than matplotlib PNGs.
"""
def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def T(x, y, t, cls="lab", anchor="start", size=None):
    st = f' font-size="{size}"' if size else ""
    return f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}"{st}>{esc(t)}</text>'

def dumbbell(rows, title, subtitle, axis_label, lo, hi, legend=("Before", "After"),
             W=780, L=282, R=40, TOP=54, ROW=30):
    """rows: [(label, value_a, value_b, annotation)] — a paired before/after comparison."""
    H = TOP + ROW * len(rows) + 34
    x0, x1 = L, W - R
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}">',
         T(0, 16, title, "ttl"), T(0, 33, subtitle, "sub"),
         f'<circle cx="{x1-150}" cy="12" r="5" class="m1"/>{T(x1-140,16,legend[0],"leg")}',
         f'<circle cx="{x1-95}" cy="12" r="5" class="m2"/>{T(x1-85,16,legend[1],"leg")}']
    step = max(1, round((hi - lo) / 4))
    for g in range(int(lo), int(hi) + 1, step):
        gx = X(g)
        s.append(f'<line class="grid" x1="{gx:.1f}" y1="{TOP-12}" x2="{gx:.1f}" y2="{TOP+ROW*len(rows)-14}"/>')
        s.append(T(gx, H - 16, g, "ax", "middle"))
    s.append(T((x0 + x1) / 2, H - 2, axis_label, "ax", "middle"))
    for i, (label, a, b, note) in enumerate(rows):
        y = TOP + i * ROW
        s.append(T(L - 14, y + 4, label, "lab", "end"))
        s.append(f'<line class="conn" x1="{X(a):.1f}" y1="{y}" x2="{X(b):.1f}" y2="{y}"/>')
        s.append(f'<circle cx="{X(a):.1f}" cy="{y}" r="5.5" class="m1"/>')
        s.append(f'<circle cx="{X(b):.1f}" cy="{y}" r="5.5" class="m2"/>')
        s.append(T(X(b) + 12, y + 4, note, "val"))
    return "\n".join(s) + "\n</svg>"

def forest(rows, title, subtitle, axis_label, lo, hi, ticks, ref=0, accent_marks=True,
           W=780, L=282, R=52, TOP=58, ROW=29):
    """rows: [(label, estimate, low, high, highlight)] — estimates with intervals.

    ref is the comparison value the intervals are judged against; it is drawn dashed.
    Ticks with an empty label draw no line, so they can pad the axis without clutter.

    The fifth element of each row flags a row that starts a group: it draws a rule above
    and bolds the label. Set accent_marks=False when that flag means "group head" rather
    than "this estimate is special", so the marker colour does not imply significance the
    row does not have.
    """
    H = TOP + ROW * len(rows) + 40
    x0, x1 = L, W - R
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    s = [f'<svg class="fig" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}">',
         T(0, 16, title, "ttl"), T(0, 33, subtitle, "sub")]
    for v, lbl in ticks:
        gx = X(v)
        if lbl:
            s.append(f'<line class="{"zero" if v == ref else "grid"}" x1="{gx:.1f}" y1="{TOP-14}" '
                     f'x2="{gx:.1f}" y2="{TOP+ROW*len(rows)-16}"/>')
            s.append(T(gx, H - 16, lbl, "ax", "middle"))
    for i, (label, est, low, high, hi_lite) in enumerate(rows):
        y = TOP + i * ROW
        if hi_lite:
            s.append(f'<line class="grid" x1="0" y1="{y-14}" x2="{W}" y2="{y-14}"/>')
        s.append(T(L - 14, y + 4, label, "lab bold" if hi_lite else "lab", "end"))
        a, b, c = X(low), X(high), X(est)
        s.append(f'<line class="ci" x1="{a:.1f}" y1="{y}" x2="{b:.1f}" y2="{y}"/>')
        for e in (a, b):
            s.append(f'<line class="ci" x1="{e:.1f}" y1="{y-4}" x2="{e:.1f}" y2="{y+4}"/>')
        accent = hi_lite and accent_marks
        s.append(f'<circle cx="{c:.1f}" cy="{y}" r="{6 if accent else 5}" '
                 f'class="{"m3" if accent else "m1"}"/>')
        s.append(T(b + 11, y + 4, f"{est:.2f}", "val"))
    s.append(T((x0 + x1) / 2, H - 2, axis_label, "ax", "middle"))
    return "\n".join(s) + "\n</svg>"

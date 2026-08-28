"""Build-time R syntax highlighter, so the code page needs no CDN script."""
import re, html

KW = ("if|else|for|while|repeat|function|return|break|next|TRUE|FALSE|NULL|NA|Inf|NaN|in|"
      "library|require|set\\.seed|c|data\\.frame|list|matrix|factor|as\\.integer|as\\.numeric|"
      "as\\.factor|is\\.na|ifelse|apply|sapply|lapply|tapply|table|mean|median|sd|sum|nrow|ncol|"
      "head|summary|print|cat|paste|paste0|names|colnames|rownames|seq|rep|round|scale|prcomp|"
      "kmeans|glm|predict|rpart|train|bind_rows|mutate|filter|select|group_by|summarise|across|"
      "pivot_longer|ggplot|aes|geom_bar|geom_point|labs|theme_minimal|barplot|plot|par")

def highlight(src):
    kw = re.compile(r"\b(?:" + KW + r")\b", re.I)
    out, i, n, pending = [], 0, len(src), False
    esc = html.escape
    while i < n:
        if c0 := (src[i] if i < n else ""):
            pass
        if src[i] == "#":                       # R comments run to end of line
            j = src.find("\n", i); j = n if j < 0 else j
            out.append(f'<span class="sas-c">{esc(src[i:j])}</span>'); i = j; continue
        c = src[i]
        if c in "'\"":
            j = i + 1
            while j < n and src[j] != c: j += 1
            j = min(j + 1, n)
            out.append(f'<span class="sas-s">{esc(src[i:j])}</span>'); i = j; continue
        if c.isdigit() and (i == 0 or not (src[i-1].isalnum() or src[i-1] == "_")):
            j = i
            while j < n and (src[j].isdigit() or src[j] == "."): j += 1
            out.append(f'<span class="sas-n">{esc(src[i:j])}</span>'); i = j; continue
        if c.isalpha() or c == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"): j += 1
            w = src[i:j]
            nxt = src[j:j+1]
            if kw.fullmatch(w):
                out.append(f'<span class="sas-k">{esc(w)}</span>')
            elif nxt == "(":                    # a call: highlight the function name
                out.append(f'<span class="sas-p">{esc(w)}</span>')
            else:
                out.append(esc(w))
            pending = False
            i = j; continue
        if c == ";": pending = False
        out.append(esc(c)); i += 1
    return "".join(out)

"""True redaction: remove the text objects for ipaddress and responseid, paint black."""
import fitz, re, sys, shutil

IP  = re.compile(r'^(?:\d{1,3}\.){3}\d{1,3}$')
RID = re.compile(r'^R_[A-Za-z0-9]{10,}$')

def redact(path):
    doc = fitz.open(path)
    total = {"ip": 0, "responseid": 0}
    for page in doc:
        rects = []
        for w in page.get_text("words"):
            tok = w[4]
            if IP.match(tok):
                rects.append(fitz.Rect(w[:4])); total["ip"] += 1
            elif RID.match(tok):
                rects.append(fitz.Rect(w[:4])); total["responseid"] += 1
        if not rects:
            continue
        for r in rects:
            page.add_redact_annot(r + (-1, -1, 1, 1), fill=(0, 0, 0))
        page.apply_redactions(
            images=fitz.PDF_REDACT_IMAGE_NONE,
            graphics=fitz.PDF_REDACT_LINE_ART_NONE,
            text=fitz.PDF_REDACT_TEXT_REMOVE,
        )
    # scrub the WCU account id out of the document metadata
    md = doc.metadata or {}
    md["author"] = "John Fisher"
    md["title"]  = path.split("/")[-1].replace(".pdf", "").replace("_", " ")
    doc.set_metadata(md)
    out = path + ".redacted"
    doc.save(out, garbage=4, deflate=True, clean=True)
    doc.close()
    shutil.move(out, path)
    return total

for p in sys.argv[1:]:
    print(p, redact(p))

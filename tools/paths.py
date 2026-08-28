"""Shared paths and study constants."""
from pathlib import Path

SITE      = Path(__file__).resolve().parents[1]
WORKSPACE = SITE.parent
SOURCE    = WORKSPACE / "source"
DERIVED   = SITE / "tools" / "derived"
TEMPLATES = SITE / "tools" / "templates"
PUBLIC    = SITE / "public"
NOTEBOOKS = SITE / "notebooks"

BASE_URL = "https://johnfisher-ai.github.io/fisher-nsduh-analysis"
SAMHSA   = "https://www.samhsa.gov/data/data-we-collect/nsduh-national-survey-drug-use-and-health"

YEARS = (2022, 2023, 2024)
FILES = {y: f"NSDUH_{y}_Tab.txt" for y in YEARS}

# Analysis variables, and the complex-survey design variables the original omitted.
ANALYSIS_VARS = ["IRSEX", "CATAG6", "INCOME", "HEALTH2",
                 "IRALCRC", "IRMJRC", "CIGMON", "AMDEYR", "AMIPY"]
DESIGN_VARS   = ["ANALWT2_C", "VESTR_C", "VEREP"]

LABELS = {
    "ALC_PASTMO": "Alcohol, past month",
    "MJ_PASTMO":  "Marijuana, past month",
    "CIG_PASTMO": "Cigarettes, past month",
    "MDE":        "Major depressive episode, past year",
}
SEX    = {1: "Male", 2: "Female"}
# CATAG6: 1 = 12-17, which the adult depression question is never asked of. The analysis
# population is therefore adults 18 and over, by construction rather than by choice.
AGE    = {1: "12-17", 2: "18-25", 3: "26-34", 4: "35-49", 5: "50-64", 6: "65+"}
ADULT_CODES = (2, 3, 4, 5, 6)
INCOME = {1: "<$20K", 2: "$20-49K", 3: "$50-74K", 4: "$75K+"}
HEALTH = {1: "Excellent", 2: "Very good", 3: "Good", 4: "Fair or poor"}

def require_raw():
    missing = [f for f in FILES.values() if not (SOURCE / f).exists()]
    if missing:
        raise SystemExit(
            f"NSDUH files not found in {SOURCE}\n  missing: {', '.join(missing)}\n"
            "They are about 1.1 GB and are not committed. Download the public-use files\n"
            f"from SAMHSA: {SAMHSA}\n"
            "The aggregate files in tools/derived/ let every later step run without them.")

def load_pooled():
    """Pool the survey years, keeping only the analysis and design variables.

    Reads just the needed columns: the full files carry about 2,650 each.
    """
    import pandas as pd
    require_raw()
    keep = ANALYSIS_VARS + DESIGN_VARS
    frames = []
    for y, f in FILES.items():
        d = pd.read_csv(SOURCE / f, sep="\t", usecols=lambda c: c in keep, low_memory=False)
        d["YEAR"] = y
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)

    # Recode to the binary indicators the analysis uses.
    df["ALC_PASTMO"] = (df.IRALCRC == 1).astype(int)
    df["MJ_PASTMO"]  = (df.IRMJRC  == 1).astype(int)
    df["CIG_PASTMO"] = (df.CIGMON  == 1).astype(int)
    df["MDE"] = df.AMDEYR.where(df.AMDEYR.isin([1, 2])).map({1: 1, 2: 0})
    df["AMI"] = df.AMIPY.where(df.AMIPY.isin([1, 2])).map({1: 1, 2: 0})
    df["HEALTH"] = df.HEALTH2.where(df.HEALTH2.isin([1, 2, 3, 4]))

    # Pooling three years: the weight must be divided by the number of years, or the
    # pooled estimates imply a population three times too large.
    df["WT"] = df.ANALWT2_C / len(FILES)
    return df

def analysis_frame(df):
    """The modelling sample: complete on outcome and self-rated health."""
    return df[df.MDE.notna() & df.HEALTH.notna()].copy()

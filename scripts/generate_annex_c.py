"""Generate annex_c.py from the FIFA 2026 regulations PDF (pages 80-97)."""
import pdfplumber
import re
from pathlib import Path

pdf = pdfplumber.open(Path(__file__).parent.parent / "FWC26_regulations_EN.pdf")

# Header in Annex C: option | 1A | 1B | 1D | 1E | 1G | 1I | 1K | 1L
# Each column header identifies the 1st-place team in that R32 matchup.
# Mapping to our slot codes:
SLOTS = ["R32_7", "R32_15", "R32_11", "R32_1", "R32_12", "R32_2", "R32_16", "R32_8"]

rows = []
for page_idx in range(79, 97):  # PDF pages 80-97
    text = pdf.pages[page_idx].extract_text()
    if not text:
        continue
    for line in text.splitlines():
        m = re.match(
            r"^\s*\d+\s+(3[A-L])\s+(3[A-L])\s+(3[A-L])\s+(3[A-L])"
            r"\s+(3[A-L])\s+(3[A-L])\s+(3[A-L])\s+(3[A-L])\s*$",
            line,
        )
        if m:
            groups = [m.group(i)[1] for i in range(1, 9)]  # strip "3" prefix
            rows.append((frozenset(groups), dict(zip(SLOTS, groups))))

assert len(rows) == 495, f"Expected 495 rows, got {len(rows)}"
assert len({tuple(sorted(k)) for k, _ in rows}) == 495, "Duplicate keys found"

out = Path(__file__).parent.parent / "annex_c.py"
with out.open("w", encoding="utf-8") as f:
    f.write("# FIFA 2026 Annex C: 495 combinations for the 8 best 3rd-place teams.\n")
    f.write("# Key  : frozenset of 8 qualifying group letters (A-L).\n")
    f.write("# Value: {slot: group_letter} — exact slot assignment per FIFA regulations.\n")
    f.write("# Source PDF columns: 1A->R32_7, 1B->R32_15, 1D->R32_11, 1E->R32_1,\n")
    f.write("#                     1G->R32_12, 1I->R32_2, 1K->R32_16, 1L->R32_8\n")
    f.write("ANNEX_C: dict = {\n")
    for key, val in rows:
        key_str = "'" + "', '".join(sorted(key)) + "'"
        val_str = ", ".join(f'"{s}": "{val[s]}"' for s in SLOTS)
        f.write(f"    frozenset({{{key_str}}}): {{{val_str}}},\n")
    f.write("}\n")

print(f"Written {len(rows)} entries to annex_c.py")

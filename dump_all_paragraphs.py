import docx
import sys

sys.stdout.reconfigure(encoding='utf-8')
doc = docx.Document('JURNAL BETRIK .docx')
print(f'Total tables: {len(doc.tables)}')
with open('paragraphs_dump.txt', 'w', encoding='utf-8') as f:
    for idx, p in enumerate(doc.paragraphs):
        txt = p.text.strip()
        f.write(f'[{idx:03d}]: {txt}\n')
print("Dumped to paragraphs_dump.txt")

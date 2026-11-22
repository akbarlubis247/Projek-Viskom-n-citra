import docx
import sys

doc = docx.Document('JURNAL BETRIK .docx')
print('Paragraph count:', len(doc.paragraphs))
for i in range(25, min(33, len(doc.paragraphs))):
    p = doc.paragraphs[i]
    print(f'p[{i}] text: "{p.text}", runs: {len(p.runs)}')
    for r in p.runs:
        if r._element.xpath('.//a:blip'):
            print(f'  -> RUN HAS IMAGE!')

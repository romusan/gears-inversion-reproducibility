"""Rasterize native Word-exported PDFs for local visual QA."""
from pathlib import Path
import re,json
from pdf2image import convert_from_path,pdfinfo_from_path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'revision_14_2026-11-01'
def main():
    counts={}
    for kind in ['main','supplement','highlights','cover']:
        folder=OUT/f'render_{kind}';pdfs=list(folder.glob('*.pdf'));assert len(pdfs)==1
        counts[kind]=int(pdfinfo_from_path(str(pdfs[0]))['Pages'])
        images=convert_from_path(str(pdfs[0]),dpi=122,thread_count=4)
        for i,page in enumerate(images):page.save(folder/f'page-{i+1}.png')
        pages=sorted(folder.glob('page-*.png'),key=lambda p:int(re.search(r'page-(\d+)',p.name)[1]))
        for start in range(0,len(pages),4):
            sheet=Image.new('RGB',(1240,1800),'#ddd');draw=ImageDraw.Draw(sheet)
            for index,path in enumerate(pages[start:start+4]):
                im=Image.open(path).convert('RGB');im.thumbnail((600,850));x=(index%2)*620+10;y=(index//2)*900+32
                sheet.paste(im,(x,y));draw.text((x,y-22),f'{kind} page {start+index+1}',fill='black')
            sheet.save(OUT/f'contact_{kind}_{start//4+1:02}.png')
    (OUT/'render_page_counts.json').write_text(json.dumps(counts,indent=2));print(counts)
if __name__=='__main__':main()

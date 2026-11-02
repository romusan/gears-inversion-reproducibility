"""Contact sheets of every rendered page for layout inspection."""
from pathlib import Path
import re
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'revision_12_2026-10-23'
def main():
    for kind in ['main','supplement','highlights']:
        folder=OUT/f'render_{kind}';pages=sorted(folder.glob('page-*.png'),key=lambda p:int(re.search(r'page-(\d+)',p.name)[1]))
        for start in range(0,len(pages),4):
            sheet=Image.new('RGB',(1240,1800),'#ddd');draw=ImageDraw.Draw(sheet)
            for index,path in enumerate(pages[start:start+4]):
                image=Image.open(path).convert('RGB');image.thumbnail((600,850))
                x=(index%2)*620+10;y=(index//2)*900+32;sheet.paste(image,(x,y));draw.text((x,y-22),f'{kind} page {start+index+1}',fill='black')
            dest=OUT/f'contact_{kind}_{start//4+1:02}.png';sheet.save(dest);print(dest)
if __name__=='__main__':main()

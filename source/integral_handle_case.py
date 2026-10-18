"""Pi400 case: integral planar pull loop at removable-L-hook end, open-top end vents.
mm, CadQuery 2.8. Base prints flat with original outside floor on bed.
"""
from pathlib import Path
import runpy,json
import cadquery as cq
HERE=Path(__file__).resolve().parent
G=runpy.run_path(str(HERE/'raised_guide_cap.py'));D=G['D'];C=G['C'];P=C['P'];box=C['box']

def handle():
    # 4mm rim, 1mm above next dock's 26.5mm post, within case's 74mm top.
    # Upright opening: width 22 (X), height 38.5 (Z); external projection 26mm.
    outer=C['rounded_box'](239,0,0,34,46.5,9,6)
    opening=C['rounded_box'](247,4,-1,22,38.5,11,4)
    return outer.cut(opening).clean()

def make_case():
    b,l=D['make_case']()
    # Coordinates here are upright. Y is the original base's print-height axis.
    # Extend each existing vent to the lid edge at Y=26; preserve hook-bearing Z edges.
    for x in (-1,243):
        for z in (20,34,44,54,60):
            w=3.2
            b=b.cut(box(x,14.3,z-w/2,6,12.7,w))
    b=b.union(D['upright'](handle())).clean()
    return b,l


if __name__=='__main__':
    raise SystemExit('Use build_all.py to regenerate the final package.')

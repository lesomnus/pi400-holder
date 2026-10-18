"""Four-lane rack dock: 0.25mm per-side wing clearance, six wings per case.
mm; CadQuery 2.8. Run to export printable dock and compatibility assemblies.
"""
from pathlib import Path
import runpy,json
import cadquery as cq
HERE=Path(__file__).resolve().parent
D=runpy.run_path(str(HERE/'single_dock_core.py'))
N=runpy.run_path(str(HERE/'integral_handle_case.py'))
C=D['C'];box=D['box'];PITCH=55.6;GROUP_PITCH=222.4;END_PITCH=277.
HOLES=[(x,y+i*PITCH) for i in range(4) for x in (-5,258) for y in (-4,36)]
HOLES += [(x,y) for x in (50,197) for y in (-4,202.8)]

def make_quad():
    unit=D['make_dock'](drill=False);p=unit
    for i in range(1,4):p=p.union(unit.translate((0,i*PITCH,0)))
    for i in range(3):
        for x,w in ((-10,10),(12,12),(117.5,12),(223,12),(247,16)):
            p=p.union(box(x,39+i*PITCH,0,w,9.6,6))
    for x,y in HOLES:p=p.cut(D['cyl'](x,y,-.1,2.5,6.2)).cut(D['cyl'](x,y,-.1,4.5,2.8))
    return p.clean()

def fit_coupon():
    p=D['make_dock']().intersect(box(237,-9,0,26,50,35))
    return p.union(box(237,0,0,10,28.6,10)).translate((-237,9,0)).clean()


if __name__=='__main__':
    raise SystemExit('Use build_all.py to regenerate the final package.')

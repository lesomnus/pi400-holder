"""Replacement tie-guide cap: outer roof and inner ceiling raised by 1mm.
Original floor ramp, tie slots, external locating faces and PCB supports unchanged.
mm; Python 3.12 / CadQuery 2.8. Run this file to regenerate.
"""
from pathlib import Path
import json,runpy
import cadquery as cq
HERE=Path(__file__).resolve().parent
D=runpy.run_path(str(HERE/'single_dock_core.py'));C=D['C'];P=C['P']
LIFT=1.;TOP=C['GUIDE_TOP']+LIFT

def make_cap(x,y):
    old=C['guide_parts'](0,0)[1]
    a=P['guide_cap_half_length'];w=P['guide_channel_width'];t=P['guide_wall']
    extra=C['cross_shape'](C['box'](-a,-w/2-t,C['GUIDE_TOP']-.05,2*a,w+2*t,LIFT+.05))
    ceiling=C['cross_shape'](C['arc_fill'](C['GUIDE_R']+P['guide_channel_height']/2,w)).translate((0,0,LIFT))
    # Re-cut only the cap interior. The base's original ramp and slot cutters are untouched.
    return old.union(extra).cut(ceiling).translate((x,y,0)).clean()

def print_cap():
    return make_cap(15,15).rotate((0,15,0),(1,15,0),180).translate((0,0,TOP)).clean()


if __name__=='__main__':
    raise SystemExit('Use build_all.py to regenerate the final package.')

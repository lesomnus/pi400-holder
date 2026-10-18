"""Pi400 case: one extra Y-direction tie path, 50mm inboard of handle-side cross.
Coordinates in the flat printed case: extra center (146,32), existing (196,32).
Run with CadQuery 2.8. No dock, PCB mount, handle or end-vent changes.
"""
from pathlib import Path
import runpy,json
import cadquery as cq
HERE=Path(__file__).resolve().parent
N=runpy.run_path(str(HERE/'integral_handle_case.py'));D=N['D'];C=N['C'];G=N['G'];P=C['P'];box=C['box']
CENTER=(146.,32.);TOP=G['TOP']

def single_parts(x=146.,y=32.):
    # Same proven arc/legs as one arm of the existing cross, rotated to the short-side axis.
    w=P['guide_channel_width'];h=P['guide_channel_height'];t=P['guide_wall']
    a=P['guide_cap_half_length'];floor=P['floor'];fit=P['guide_leg_side_clearance']
    lower=C['arc_fill'](C['GUIDE_R']-h/2,w)
    upper=C['arc_fill'](C['GUIDE_R']+h/2,w)
    tunnel=upper.cut(lower)
    shell=box(-a,-w/2-t,floor,2*a,w+2*t,C['GUIDE_TOP']-floor)
    cap=shell.cut(upper)
    leg_clearance=box(-a,-w/2,0,2*a,w,floor).cut(upper)
    legs=box(-a+fit,-w/2+fit,0,2*(a-fit),w-2*fit,floor).cut(upper)
    cap=cap.union(legs)
    extra=box(-a,-w/2-t,C['GUIDE_TOP']-.05,2*a,w+2*t,1.05)
    ceiling=upper.translate((0,0,1))
    cap=cap.union(extra).cut(ceiling).clean()
    ramp=lower.intersect(box(-a,-a,floor,2*a,2*a,C['GUIDE_TOP']-floor)).cut(tunnel).clean()
    cutter=tunnel.union(leg_clearance).clean()
    return tuple(p.rotate((0,0,0),(0,0,1),90).translate((x,y,0)) for p in (ramp,cap,cutter))

def make_case():
    b,l=N['make_case']();flat=D['flat'](b)
    ramp,cap,cutter=single_parts(*CENTER)
    flat=flat.union(ramp).cut(cutter).clean()
    return D['upright'](flat),l

def cap_print():
    cap=single_parts(0,0)[1]
    cap=cap.rotate((0,0,0),(1,0,0),180)
    bb=cap.val().BoundingBox()
    return cap.translate((-bb.xmin,-bb.ymin,-bb.zmin))


if __name__=='__main__':
    raise SystemExit('Use build_all.py to regenerate the final package.')

"""Identical quad docks, keyed gap-filling connector below cases. Units mm."""
from pathlib import Path
import runpy,json
import cadquery as cq
HERE=Path(__file__).resolve().parent
Q=runpy.run_path(str(HERE/'quad_core_v6.py'));D=Q['D'];N=Q['N'];box=D['box']
PITCH=55.6;OFFSET=222.4;SEAM=210.6;LINK_X=(50.,197.)

def make_universal():
    p=Q['make_quad']()
    # Square rail corners without changing original 273 x 216.8 bounding box.
    for y,hy in [(-9,-4),(197.8,202.8)]:
        p=p.union(box(-10,y,0,273,10,6))
        for x in (-5,50,197,258):
            p=p.cut(D['cyl'](x,hy,-.1,2.5,6.2)).cut(D['cyl'](x,hy,-.1,4.5,2.8))
        for x in LINK_X:p=p.cut(box(x-6,hy-4,4,12,8,3))
    return p.clean()

def bridge():
    # Assembled local coordinates: bolt centers (0,0) and (0,15.6).
    p=D['rounded'](-9,-6,6,18,27.6,4,2)
    for y in (0,15.6):
        p=p.union(box(-6,y-4,4,12,8,2.1))
        p=p.cut(D['cyl'](0,y,3,2.5,8)).cut(D['hexagon'](0,y,8.2,5.1,1.9))
    return p.clean()

def connector():
    # Full-length spine fills the gap and joins both keyed bridges into one part.
    # Everything is at or below the Z=10 case seat.
    p=box(-10,207.8,0,273,5.6,10)
    for x in LINK_X:p=p.union(bridge().translate((x,202.8,0)))
    return p.clean()

def connector_print():
    # Continuous spine/bridge top on bed, keys and central spine point upward.
    p=connector().rotate((0,0,0),(1,0,0),180)
    bb=p.val().BoundingBox()
    return p.translate((-bb.xmin,-bb.ymin,-bb.zmin))

def depth_link():
    # 8mm width avoids the widened case-end wall at the front/back outer holes.
    p=D['rounded'](-5,-4,0,24,8,4,2)
    for x in (0,14):p=p.cut(D['cyl'](x,0,-1,2.5,6)).cut(D['hexagon'](x,0,2.2,5.1,1.9))
    return p.clean()


if __name__=='__main__':
    raise SystemExit('Use build_all.py to regenerate the final package.')

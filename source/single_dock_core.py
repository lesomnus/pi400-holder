"""Pi400 dock: zero end gap, wings 0.25mm outward per side, bosses extended 1mm.
Units mm. Python 3.12 / CadQuery 2.8. Use snug_quad_dock.py to generate v6.
Case assembly coords (x,y,z) -> upright (x,z,74-y), ports up.
"""
from pathlib import Path
import json,math,runpy
import cadquery as cq
HERE=Path(__file__).resolve().parent
C=runpy.run_path(str(HERE/'v6_case_core.py'))
box=C['box'];rounded=C['rounded_box'];cyl=C['cyl'];slot=C['slot']
SEAT=10.;END_PITCH=277.;SIDE_PITCH=60.
HOLES=[(x,y) for x in (-5,50,197,258) for y in (-4,36)]

def upright(p):return p.rotate((0,0,0),(1,0,0),-90).translate((0,0,74))
def flat(p):return p.translate((0,0,-74)).rotate((0,0,0),(1,0,0),90)
def hexagon(x,y,z,af,h):
    return cq.Workplane('XY').center(x,y).polygon(6,2*af/math.sqrt(3)).extrude(h).translate((0,0,z))
def end_slot(x,z,width=3.2):
    return cq.Workplane('YZ').center(14.3,z).slot2D(16,width,0).extrude(6).translate((x,0,0))

def make_case():
    # Start with the physically successful v6; v7 broad-face additions are omitted.
    b=upright(C['make_base']());l=upright(C['make_lid_assembled']())
    # Reinforce the single fixed-hook slot inward, clear of the lid alignment lip.
    b=b.union(box(2.3,4.8,18.5,1.3,18.7,11))
    for x in (-1,243):
        for z in (20,34,44,54,60):
            b=b.cut(end_slot(x,z,3.2))
    return b.clean(),l

def round_boss():
    # Keep the original rounded nose and 3.2mm vent section; extend it by 1mm.
    # Moving the whole sphere would widen the root and obstruct the vent.
    body=cq.Workplane('XZ').center(253.3,20).circle(6.5).extrude(6.9,both=True).translate((0,17.5,0))
    for y in (10.6,24.4):
        body=body.union(cq.Workplane('XY').sphere(6.5).translate((253.3,y,20)))
    original=body.intersect(box(246.7,0,0,1.3,28.6,22.5))
    nose=original.intersect(box(246.7,0,0,.3,28.6,22.5)).translate((-1,0,0))
    extension=cq.Workplane('YZ').center(17.5,20).slot2D(17,3.2,0).extrude(1.05).translate((246,0,0))
    return original.union(extension).union(nose).clean()

def locating_emboss():
    # Matches left vent outline in its outer wall plane X=0:
    # 3.2mm high, lower round end Y=6.3, open upper end Y=26.
    body=end_slot(-.55,20,3.2).union(box(-.55,14.3,18.4,6,11.7,3.2))
    body=body.intersect(box(-.55,0,0,2.15,28.6,40))
    return body.faces('>X').edges().fillet(.4).clean()

def make_dock(drill=True):
    p=rounded(-10,-9,0,273,50,6,2).cut(rounded(0,1,-1,247,30,8,1))
    for x in (12,117.5,223):
        # Fill each 0.25mm seat-to-wing slit only up to the seat top Z=10.
        p=p.union(box(x,0,0,12,32,6)).union(box(x,-.25,5.9,12,29.1,4.1))
        # User-requested outward shift of 0.25mm per side; thickness remains 3mm.
        p=p.union(box(x,-3.25,5.9,12,3,12.1))
        p=p.union(box(x,28.85,5.9,12,3,12.1))
    # No old triangle: shallow locating emboss follows the opposite vent.
    # Inner face exactly X=0: no longitudinal allowance.
    p=p.union(box(-4.5,0,5.9,4.5,28.6,16.6)).union(locating_emboss())
    # Raise the handle-side wall to support the rounded boss at Z=20, clipped flush at Z=22.5.
    # Inner face exactly X=247; preserve the original external footprint.
    p=p.union(box(247,0,0,5.75,28.6,22.5)).union(round_boss())
    for x,y in (HOLES if drill else []):
        p=p.cut(cyl(x,y,-.1,2.5,6.2)).cut(cyl(x,y,-.1,4.5,2.8))
    return p.clean()

def make_clip():
    # Vent is z=22.4..25.6: the 2.4mm arm has 0.4mm clearance above and below.
    # 3.6mm penetration through the 2.4mm case wall leaves a 1.2mm inner overlap.
    arm=box(243.4,10.3,22.8,12.7,8,2.4)
    leg=box(253.1,10.3,14.8,3,8,10.4)
    return arm.union(leg).clean()

def make_fit_fixture():
    return make_dock().intersect(box(237,-9,0,26,50,35)).union(box(237,0,0,10,28.6,10)).clean()

def clip_print(p):
    p=p.rotate((0,0,0),(1,0,0),90)
    bb=p.val().BoundingBox()
    return p.translate((-bb.xmin,-bb.ymin,-bb.zmin))

def make_link(distance):
    p=rounded(-5,-5,0,distance+10,10,4,2)
    for x in (0,distance):p=p.cut(cyl(x,0,-1,3.4,6))
    return p.clean()

def export(name,p):
    s=p.val();assert s.isValid() and len(s.Solids())==1,(name,len(s.Solids()))
    cq.exporters.export(p,str(HERE/(name+'.stl')),tolerance=.025,angularTolerance=.08)
    # OCC sphere tessellation emits zero-area pole triangles; remove these only.
    import trimesh
    m=trimesh.load(HERE/(name+'.stl'),force='mesh')
    m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices()
    assert m.is_watertight and len(m.split())==1
    m.export(HERE/(name+'.stl'))
    cq.exporters.export(p,str(HERE/(name+'.step')))
    b=s.BoundingBox()
    return dict(bounds_mm=[b.xlen,b.ylen,b.zlen],volume_mm3=s.Volume(),brep_valid=True)


if __name__=='__main__':
    raise SystemExit('Use build_all.py to regenerate the final package.')

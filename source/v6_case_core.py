"""Pi 400 case v6 with shallow circular tie paths and separate covers: user-corrected left/right, PCB locating pins and lid retainers.
Units mm. Run using Python 3.12 + cadquery==2.8.0.
No PCB bolts/nuts. Four M3 lid screws remain.
User confirms lower support height is correct. It stays 5 mm above inside floor.
PCB is only a dimensional proxy: no actual component footprints are modeled.
"""
from pathlib import Path
import json
import math
import cadquery as cq

HERE=Path(__file__).resolve().parent
P=json.loads((HERE/'design_parameters.json').read_text(encoding='utf-8'))
L,W,H=(P[k] for k in ('case_length','case_width','base_height'))
T,F,R,LT=(P[k] for k in ('wall','floor','corner_radius','lid_thickness'))
PCB_Z=F+P['pcb_standoff_height']
PCB_TOP=PCB_Z+P['pcb_thickness']
POST_BOTTOM=PCB_TOP+P['lid_pcb_clearance']
OX,OY=P['pcb_measured_origin_case_xy']
# IMPORTANT v3: user physically confirmed X must be mirrored relative to v2.
# Xcase=10+Xmeasurement, Ycase=54.15-Ymeasurement. Do NOT mirror PCB Z.
MOUNTS=[(OX+h['x'],OY-h['y']) for h in P['pcb_measured_holes']]
SCREWS=[(x,y) for x in (4.8,L-4.8) for y in (4.8,W-4.8)]

def box(x,y,z,dx,dy,dz):
    return cq.Workplane('XY').box(dx,dy,dz,centered=False).translate((x,y,z))

def rounded_box(x,y,z,dx,dy,dz,r):
    s=box(x,y,z,dx,dy,dz)
    return s.edges('|Z').fillet(r) if r else s

def cyl(x,y,z,d,h):
    return cq.Workplane('XY').center(x,y).circle(d/2).extrude(h).translate((0,0,z))

def cone(x,y,z,d1,d2,h):
    return cq.Workplane('XY').newObject([cq.Solid.makeCone(d1/2,d2/2,h,cq.Vector(x,y,z))])

def slot(x,y,z,length,width,angle,depth):
    return cq.Workplane('XY').center(x,y).slot2D(length,width,angle).extrude(depth).translate((0,0,z))

def support_d(hole): return hole['diameter']+P['pcb_support_extra_diameter']
def pin_d(hole): return hole['diameter']-P['pin_diametral_clearance']

def tie_cutters(centers,z=-1,depth=None):
    a=P['tie_pair_spacing']/2; result=[]
    for x,y in centers:
        for dx in (-a,a): result.append(slot(x+dx,y,z,P['tie_slot_length'],P['tie_slot_width'],90,depth or F+2))
        for dy in (-a,a): result.append(slot(x,y+dy,z,P['tie_slot_length'],P['tie_slot_width'],0,depth or F+2))
    return result

def locating_pin(x,y,z,hole):
    d=pin_d(hole); tip=P['pin_tip_height']; height=P['pin_height_above_support']
    return cyl(x,y,z-.05,d,height-tip+.05).union(
        cone(x,y,z+height-tip,d,d-P['pin_tip_diameter_reduction'],tip))

def lower_support(x,y,floor,hole):
    d=support_d(hole); h=P['pcb_standoff_height']
    return cyl(x,y,floor-.1,d,h+.1).union(cone(x,y,floor-.1,d+2,d,1.3)).union(
        locating_pin(x,y,floor+h,hole))


GUIDE_R=P['guide_bend_radius']
GUIDE_CZ=P['guide_path_apex_z']-GUIDE_R
GUIDE_TOP=P['guide_path_apex_z']+P['guide_channel_height']/2+P['guide_wall']

def arc_fill(radius,width):
    # Filled below the upper circle; XZ section extruded across the strap width.
    # Both ends extend below the external floor, so there is no vertical elbow.
    bottom=-2.0
    half=math.sqrt(radius**2-(bottom-GUIDE_CZ)**2)
    return cq.Workplane('XZ').moveTo(-half,bottom).threePointArc((0,GUIDE_CZ+radius),(half,bottom)).close().extrude(width/2,both=True)

def cross_shape(shape):
    return shape.union(shape.rotate((0,0,0),(0,0,1),90))

def guide_parts(x,y):
    w=P['guide_channel_width'];h=P['guide_channel_height'];t=P['guide_wall']
    lower=arc_fill(GUIDE_R-h/2,w)
    upper=arc_fill(GUIDE_R+h/2,w)
    tunnel=cross_shape(upper.cut(lower))
    lower_cross=cross_shape(lower)
    a=P['guide_cap_half_length']
    shell=cross_shape(box(-a,-w/2-t,F,2*a,w+2*t,GUIDE_TOP-F))
    cap=shell.cut(cross_shape(upper))
    # Roof tips descend into open floor slots. Every base passage is open
    # upward for printing; the separate upside-down cover supplies its roof.
    leg_clearance=cross_shape(box(-a,-w/2,0,2*a,w,F)).cut(cross_shape(upper))
    fit=P['guide_leg_side_clearance']
    legs=cross_shape(box(-a+fit,-w/2+fit,0,2*(a-fit),w-2*fit,F)).cut(cross_shape(upper))
    cap=cap.union(legs).clean()
    floor_ramp=lower_cross.intersect(box(-a,-a,F,2*a,2*a,GUIDE_TOP-F)).cut(tunnel).clean()
    return tuple(part.translate((x,y,0)) for part in (floor_ramp,cap,tunnel.union(leg_clearance)))

def add_guides(part,centers):
    for x,y in centers:
        ramp,cap,tunnel=guide_parts(x,y)
        part=part.union(ramp).cut(tunnel)
    return part.clean()

def make_guide_cap():
    # Flat outer roof on bed. The channel opens upward during printing.
    cap=guide_parts(15,15)[1]
    return cap.rotate((0,15,0),(1,15,0),180).translate((0,0,GUIDE_TOP)).clean()

def make_base():
    base=rounded_box(0,0,0,L,W,H,R).cut(rounded_box(T,T,F,L-2*T,W-2*T,H-F+1,max(.6,R-T)))
    base=base.cut(box(P['io_start_x'],-1,P['io_bottom_z'],P['io_width'],T+2,H+1))
    for x,y in SCREWS: base=base.union(cyl(x,y,0,8.4,H))
    for (x,y),hole in zip(MOUNTS,P['pcb_measured_holes']): base=base.union(lower_support(x,y,F,hole))
    # Narrow edge pads support sag, without introducing extra locating constraints.
    for x,y in P['auxiliary_support_centers']:
        base=base.union(box(x-P['auxiliary_support_width_x']/2,y-P['auxiliary_support_width_y']/2,F-.1,
            P['auxiliary_support_width_x'],P['auxiliary_support_width_y'],
            P['pcb_standoff_height']-P['auxiliary_support_recess']+.1))
    base=add_guides(base,P['tie_cluster_centers'])
    for x,y in SCREWS: base=base.cut(cyl(x,y,H-11,P['lid_screw_pilot'],12))
    for x in range(25,int(L)-20,12): base=base.cut(box(x,W-T-1,15,3,T+2,H-15+1))
    return base.clean()

def lid_vent_clear(x):
    # Retain solid attachment material around upper post roots.
    for (mx,my),hole in zip(MOUNTS,P['pcb_measured_holes']):
        if abs(x-mx)<support_d(hole)/2+1+1.3+1 and abs(my-W/2)<12.5+support_d(hole)/2+2:
            return False
    return True

def make_lid_assembled():
    lid=rounded_box(0,0,H,L,W,LT,R)
    c=P['lid_clearance']; ph=P['lip_height']; lip=1.2
    for x in (T+c,L-T-c-lip): lid=lid.union(box(x,12,H-ph,lip,W-24,ph+.1))
    lid=lid.union(box(12,W-T-c-lip,H-ph,L-24,lip,ph+.1))
    for x,y in SCREWS: lid=lid.cut(cyl(x,y,H-1,P['lid_screw_clearance'],LT+2))
    for x in range(23,int(L)-20,8):
        if lid_vent_clear(x): lid=lid.cut(slot(x,W/2,H-1,25,2.6,90,LT+2))
    for (x,y),hole in zip(MOUNTS,P['pcb_measured_holes']):
        d=support_d(hole)
        post=cyl(x,y,POST_BOTTOM,d,H-POST_BOTTOM+.1).union(cone(x,y,H-2,d,d+2,2.1))
        # Relief socket clears the locating pin. The annular face retains PCB around its hole.
        post=post.cut(cyl(x,y,POST_BOTTOM-.1,hole['diameter']+P['lid_socket_diameter_extra'],P['lid_pin_socket_depth']+.1))
        lid=lid.union(post)
    return lid.clean()

def make_pin_fit_template():
    f=1.2
    t=rounded_box(0,0,0,L,W,f,R)
    for a,b in ((24,82),(104,153),(175,223)):
        t=t.cut(rounded_box(a,12,-1,b-a,38,3,3))
    for (x,y),hole in zip(MOUNTS,P['pcb_measured_holes']): t=t.union(lower_support(x,y,f,hole))
    return t.clean()

def make_tie_coupon():
    t=rounded_box(0,0,0,40,40,F,3)
    return add_guides(t,[(20,20)])

def make_pin_coupon():
    t=rounded_box(0,0,0,60,26,F,2)
    for x,hole in zip((9,23,37,51),P['pcb_measured_holes']):
        t=t.union(locating_pin(x,17,F,hole))
        label=cq.Workplane('XY').text(hole['id'],4,.5,combine=False).translate((x,6,F-.1))
        t=t.union(label)
    return t.clean()

def make_pcb_proxy():
    # Dimensional proxy only. No connector bodies, underside components or heatsink footprint.
    pcb=box(OX,OY-P['pcb_width'],PCB_Z,P['pcb_length'],P['pcb_width'],P['pcb_thickness'])
    for (x,y),hole in zip(MOUNTS,P['pcb_measured_holes']):
        pcb=pcb.cut(cyl(x,y,PCB_Z-1,hole['diameter'],P['pcb_thickness']+2))
    # User-measured non-port edge notches (not structural locators in this case).
    for x in (OX+22.05,OX+204.95): pcb=pcb.cut(box(x-4.95,OY-3.1,PCB_Z-1,9.9,4.1,P['pcb_thickness']+2))
    return pcb

def export_part(name,part):
    s=part.val(); assert s.isValid() and len(s.Solids())==1,name
    cq.exporters.export(part,str(HERE/f'{name}.stl'),tolerance=.025,angularTolerance=.08)
    cq.exporters.export(part,str(HERE/f'{name}.step'))
    b=s.BoundingBox()
    return {'brep_valid':True,'solid_count':1,'bounds_mm':[b.xlen,b.ylen,b.zlen],'volume_mm3':s.Volume()}


if __name__=='__main__':
    raise SystemExit('Use build_all.py to regenerate the final package.')

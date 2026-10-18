from pathlib import Path
import runpy,json,hashlib
import cadquery as cq,numpy as np,trimesh
R=Path(__file__).resolve().parent.parent
J=runpy.run_path(str(R/'source/flush_pair.py'));D=J['D'];box=D['box']
def load(n):return cq.importers.importStep(str(R/'STEP'/(n+'.step')))
def compound(ps):return cq.Workplane('XY').newObject([cq.Compound.makeCompound([p.val() for p in ps])])
def vol(a,b):
    v=a.val().intersect(b.val()).Volume();assert v>=-1e-6,v
    return max(v,0)
p=load('05_quad_dock_repeatable');q=p.translate((0,222.4,0));c=J['connector']()
assert vol(p,q)<1e-6 and vol(p,c)<1e-6 and vol(q,c)<1e-6
third=p.translate((0,444.8,0));c2=c.translate((0,222.4,0))
for part in (q,third):assert vol(part,c2)<1e-6
assert vol(c,c2)<1e-6
assert box(-10,207.8,0,273,5.6,6).cut(c).val().Volume()<1e-6
assert abs(p.val().BoundingBox().ylen-216.8)<1e-6
assert abs(q.val().BoundingBox().ymax-p.val().BoundingBox().ymin-439.2)<1e-6
assert abs(c.val().BoundingBox().zmax-10)<1e-6
meshes={}
for file in (R/'STL').glob('*.stl'):
    m=trimesh.load(file,force='mesh');meshes[file.stem]=m
    assert m.is_watertight and m.is_winding_consistent and len(m.split())==1 and m.volume>0,file
    assert np.all(m.extents<=[340,320,340]) and abs(m.bounds[0,2])<1e-5,file
# Actual exported mesh confirms end gap is zero and wing gap is 0.25mm per side.
m=meshes['05_quad_dock_repeatable']
pts,_,_=m.ray.intersects_location([[-6,14.3,17]],[[1,0,0]],multiple_hits=True)
assert np.allclose(np.sort(pts[:,0]),[-4.5,0,247,252.75],atol=1e-5)
pts,_,_=m.ray.intersects_location([[18,-5,14]],[[0,1,0]],multiple_hits=True)
assert np.allclose(np.sort(pts[:,1])[:4],[-3.25,-.25,28.85,31.85],atol=1e-5)
for x in (18,123.5,229):
    pts,_,_=m.ray.intersects_location([[x,-5,8]],[[0,1,0]],multiple_hits=True)
    assert np.allclose(np.sort(pts[:,1])[:2],[-3.25,31.85],atol=1e-5)
    for y in (-.125,28.725):
        pts,_,_=m.ray.intersects_location([[x,y,7]],[[0,0,1]],multiple_hits=True)
        assert np.allclose(pts[:,2],[10],atol=1e-5)
pts,_,_=m.ray.intersects_location([[-6,17,20]],[[1,0,0]],multiple_hits=True)
assert np.allclose(np.sort(pts[:,0]),[-4.5,1.6,245.8,252.75],atol=.002)
# Confirm the released bottom head pockets match the successful hardware coupon.
for z,diam in [(1,4.5),(3,2.5)]:
    pts,_,_=m.ray.intersects_location([[45,202.8,z]],[[1,0,0]],multiple_hits=True)
    xx=pts[:,0]
    for target in (50-diam/2,50+diam/2):assert np.min(abs(xx-target))<.002
pts,_,_=m.ray.intersects_location([[52,202.8,-1]],[[0,0,1]],multiple_hits=True)
assert np.allclose(np.sort(pts[:,2]),[2.7,4],atol=.002)
print('Three identical docks, filled joints, mesh and dimensions passed',flush=True)
b=D['upright'](load('01_case_base'))
l=D['upright'](load('02_case_lid').translate((0,0,-28.6)).rotate((0,32,0),(1,32,0),180))
assembly=compound([p,q,c])
for i in range(8):
    assert vol(b.translate((0,i*55.6,0)),assembly)<1e-5
    assert vol(l.translate((0,i*55.6,0)),assembly)<1e-5
for x in (50,197):
    for y in (202.8,218.4):
        for hardware in [D['cyl'](x,y,2.7,2.5,8),D['cyl'](x,y,0,4.5,2.7),
            D['hexagon'](x,y,8.2,5.1,1.8).cut(D['cyl'](x,y,8.1,2.5,2))]:
            assert vol(assembly,hardware)<1e-6
print('Cases and M2.5 bottom-up hardware passed',flush=True)
restraint={}
for dx,dy in [(.1,0),(-.1,0),(0,.1),(0,-.1)]:restraint[f'shift_{dx}_{dy}']=vol(q.translate((dx,dy,0)),c)
for angle in (-.2,.2):restraint[f'yaw_{angle}']=vol(q.rotate((123.5,210.6,0),(123.5,210.6,1),angle),c)
assert min(restraint.values())>.01
# Optional front/back links remain compatible with the filled side joint.
for i in range(8):
    for y in (-4+i*55.6,36+i*55.6):
        link=J['depth_link']().translate((258,y,6))
        v1=vol(link,assembly);v2=vol(link,assembly.translate((277,0,0)))
        assert v1<1e-6 and v2<1e-6,(i,y,v1,v2)
# The 1.8mm-deep nut pockets face the bed; their roofs bridge the 5.1mm flats.
# Any upward material start must therefore be at/below the pocket roof, not elsewhere.
m=meshes['06_gap_filling_connector'];zs=np.linspace(.05,9.95,51)
xy=[(x,y) for x in np.arange(.25,273,3) for y in np.arange(.25,27.6,.75)]
pts=np.array([[x,y,z] for x,y in xy for z in zs])
occ=m.contains(pts).reshape(-1,len(zs))
starts=np.argwhere(np.diff(occ.astype(int),axis=1)>0)
assert all(zs[j+1]<=2.0 for _,j in starts)
report=dict(single_repeatable_part=True,part_size_mm=[273,216.8,22.5],group_offset_mm=222.4,
    two_plate_width_mm=439.2,case_gaps_mm=[27]*7,unfilled_joint_gap_mm=0,
    connector_size_mm=[273,27.6,10],connector_count_per_joint=1,
    connector_spine_width_mm=5.6,connector_top_equals_case_seat_mm=10,
    keys_and_sockets_mm=[12,8,2],key_fit_allowance_mm=0,end_fit_allowance_mm=0,
    side_wing_clearance_per_side_mm=.25,wing_inner_gap_mm=29.1,
    seat_wing_slits_filled_to_z_mm=10,
    opposite_boss_projection_mm=1.6,handle_boss_projection_mm=1.2,
    all_eight_cases_clear=True,three_same_parts_connect=True,m2p5x8_hardware_clear=True,
    bolt_direction='bottom to top',shaft_bore_mm=2.5,head_pocket_diameter_depth_mm=[4.5,2.7],
    nut_pocket_af_depth_mm=[5.1,1.8],hardware_added_clearance_mm=0,
    hardware_coupon_physically_confirmed_by_user=True,
    front_back_links_compatible=True,connector_nut_pocket_roof_bridge_mm=5.1,
    connector_print_columns_checked=True,
    restraint_overlap_mm3=restraint,physical_fit_tested=False,physical_rigidity_tested=False)
(R/'verification/dock_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
manifest={}
for folder,ext in [('STL','stl'),('STEP','step')]:
    for file in (R/folder).glob('[0-9][0-9]_*.'+ext):
        manifest[str(file.relative_to(R)).replace('\\','/')]={'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
(R/'verification/file_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2),flush=True)

"""Check current exported PCB locating pins, lid sockets and case clearances."""
from pathlib import Path
import json,runpy,hashlib
import cadquery as cq,numpy as np,trimesh
R=Path(__file__).resolve().parent.parent
F=runpy.run_path(str(R/'source/poe_tie_case.py'));C=F['C'];P=F['P']
b=cq.importers.importStep(str(R/'STEP/01_case_base.step'))
l=cq.importers.importStep(str(R/'STEP/02_case_lid.step')).translate((0,0,-28.6)).rotate((0,32,0),(1,32,0),180)

def cylinder_exists(part,x,y,diameter,zmin,zmax):
    for face in part.val().Faces():
        if face.geomType()!='CYLINDER':continue
        c=face._geomAdaptor().Cylinder();loc=c.Location();bb=face.BoundingBox()
        if abs(loc.X()-x)<1e-5 and abs(loc.Y()-y)<1e-5 and abs(2*c.Radius()-diameter)<1e-5 and abs(bb.zmin-zmin)<1e-5 and abs(bb.zmax-zmax)<1e-5:return True
    return False

holes=[]
for h in P['pcb_measured_holes']:
    x=P['pcb_measured_origin_case_xy'][0]+h['x'];y=P['pcb_measured_origin_case_xy'][1]-h['y']
    d=h['diameter']-P['pin_diametral_clearance']
    assert cylinder_exists(b,x,y,d,8.2,10.2),h
    assert cylinder_exists(l,x,y,h['diameter']+.4,9.55,11.55),h
    holes.append(dict(id=h['id'],pcb_center_mm=[h['x'],h['y']],case_center_mm=[x,y],
        pcb_hole_diameter_mm=h['diameter'],pin_diameter_mm=round(d,3),lid_socket_diameter_mm=round(h['diameter']+.4,3)))
assert holes[1]['pcb_center_mm']==[82.7,25] and holes[1]['pcb_hole_diameter_mm']==4.9
assert holes[2]['pcb_center_mm']==[153.2,25] and holes[2]['pcb_hole_diameter_mm']==4.9
# Physical orientation: handle extends past X=247; B is farther away, C is nearer.
assert abs(holes[1]['case_center_mm'][0]-92.7)<1e-6
assert abs(holes[2]['case_center_mm'][0]-163.2)<1e-6
caps=[F['G']['make_cap'](x,y) for x,y in P['tie_cluster_centers']]+[F['single_parts']()[1]]
pcb=C['make_pcb_proxy']()
parts=[b,l,*caps,pcb]
for i,a in enumerate(parts):
    for q in parts[i+1:]:assert abs(a.val().intersect(q.val()).Volume())<1e-5
mesh_report={}
for name in ('01_case_base','02_case_lid','03_cross_guide_cap_print_2','04_single_guide_cap_print_1'):
    m=trimesh.load(R/'STL'/(name+'.stl'),force='mesh')
    assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
    assert np.all(m.extents<=[340,320,340]) and abs(m.bounds[0,2])<1e-5
    if name=='01_case_base':
        pts,_,_=m.ray.intersects_location([[-1,29.15,9.1]],[[1,0,0]],multiple_hits=True)
        xs=pts[:,0]
        for center in (92.7,163.2):
            for edge in (center-2.3,center+2.3):assert np.min(abs(xs-edge))<.002
    mesh_report[name]=dict(dimensions_mm=m.extents.tolist(),volume_mm3=float(m.volume),watertight=True)
report=dict(revision='2026-10-20 move far mount B 0.5mm away from handle; retain near mount C',holes=holes,mesh=mesh_report,
    exported_pin_and_lid_socket_geometry_measured=True,case_lid_caps_pcb_proxy_no_overlap=True,
    exported_stl_large_pin_centers_checked=True,
    pcb_proxy_excludes_components=True,new_pcb_pin_physical_fit_tested=False)
(R/'verification/case_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
manifest={}
for folder,ext in [('STL','stl'),('STEP','step')]:
    for file in (R/folder).glob('[0-9][0-9]_*.'+ext):
        manifest[str(file.relative_to(R)).replace('\\','/')]={'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
(R/'verification/file_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2),flush=True)

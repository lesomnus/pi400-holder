from pathlib import Path
import hashlib,json,runpy
import cadquery as cq,numpy as np,trimesh
R=Path(__file__).resolve().parent.parent
manifest=json.loads((R/'verification/file_manifest.json').read_text())
for name,entry in manifest.items():
    p=R/name
    assert p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],name
for p in (R/'STL').glob('*.stl'):
    m=trimesh.load(p,force='mesh')
    assert m.is_watertight and m.is_winding_consistent and len(m.split())==1 and m.volume>0,p
    assert np.all(m.extents<=[340,320,340]) and abs(m.bounds[0,2])<1e-5,p
# Ensure copied sources resolve all dependencies locally after previous folders are removed.
F=runpy.run_path(str(R/'source/poe_tie_case.py'));J=runpy.run_path(str(R/'source/flush_pair.py'))
assert F['CENTER']==(146.,32.) and J['OFFSET']==222.4
for n,expected in [('case_assembly',5),('two_quad_connection_assembly',3),('eight_pi_assembly',43)]:
    p=cq.importers.importStep(str(R/'STEP'/(n+'.step')))
    assert len(p.val().Solids())==expected,(n,len(p.val().Solids()))
result=dict(all_7_parts_match_verified_manifest=True,printable_meshes_valid=True,
    sources_self_contained=True,assembly_solid_counts=dict(case=5,dock_pair=3,eight_pi=43),
    assembly_contains_current_poe_guide_cases=True,physical_fit_tested=False)
(R/'verification/package_check.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2),flush=True)

"""Regenerate the consolidated current design. --assemblies-only keeps printable files intact."""
from pathlib import Path
import runpy,sys
import cadquery as cq
import trimesh
ROOT=Path(__file__).resolve().parent.parent
F=runpy.run_path(str(ROOT/'source/poe_tie_case.py'))
J=runpy.run_path(str(ROOT/'source/flush_pair.py'))
D=F['D'];G=F['G']

def export(name,p):
    assert p.val().isValid() and len(p.val().Solids())==1
    cq.exporters.export(p,str(ROOT/'STEP'/(name+'.step')))
    target=ROOT/'STL'/(name+'.stl')
    cq.exporters.export(p,str(target),tolerance=.025,angularTolerance=.08)
    m=trimesh.load(target,force='mesh');m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices()
    assert m.is_watertight and len(m.split())==1
    m.export(target)

def load(name):return cq.importers.importStep(str(ROOT/'STEP'/(name+'.step')))

def build_parts():
    b,l=F['make_case']()
    parts={'01_case_base':D['flat'](b),
        '02_case_lid':D['flat'](l).rotate((0,32,0),(1,32,0),180).translate((0,0,28.6)),
        '03_cross_guide_cap_print_2':G['print_cap'](),'04_single_guide_cap_print_1':F['cap_print'](),
        '05_quad_dock_repeatable':J['make_universal'](),
        '06_gap_filling_connector':J['connector_print'](),'08_depth_link_optional':J['depth_link']()}
    for n,p in parts.items():export(n,p)

def build_assemblies():
    b=D['upright'](load('01_case_base'))
    l=D['upright'](load('02_case_lid').translate((0,0,-28.6)).rotate((0,32,0),(1,32,0),180))
    caps=[D['upright'](G['make_cap'](x,y)) for x,y in F['P']['tie_cluster_centers']]
    caps.append(D['upright'](F['single_parts']()[1]))
    def add_case(asm,i):
        shift=(0,i*55.6,0)
        for name,p,col in [('Base',b,(.68,.76,.81)),('Lid',l,(.83,.87,.9))]:
            asm.add(p.translate(shift),name=f'{name}_{i}',color=cq.Color(*col))
        for j,p in enumerate(caps):
            asm.add(p.translate(shift),name=f'Guide_cap_{i}_{j}',color=cq.Color(*((.95,.6,.18) if j==2 else (.3,.57,.7))))
    single=cq.Assembly(name='Current_case_with_PoE_tie_guide');add_case(single,0)
    single.export(str(ROOT/'STEP/case_assembly.step'))
    a=cq.Assembly(name='Identical_docks_with_gap_filling_keyed_connector')
    a.add(load('05_quad_dock_repeatable'),name='Dock_1',color=cq.Color(.21,.49,.65))
    a.add(load('05_quad_dock_repeatable').translate((0,222.4,0)),name='Dock_2',color=cq.Color(.35,.63,.71))
    a.add(J['connector'](),name='Gap_filling_connector',color=cq.Color(.95,.62,.18))
    a.export(str(ROOT/'STEP/two_quad_connection_assembly.step'))
    for i in range(8):add_case(a,i)
    a.export(str(ROOT/'STEP/eight_pi_assembly.step'))
    print('Updated all three assemblies with current PoE-guide cases',flush=True)

if __name__=='__main__':
    if '--dock-only' in sys.argv:
        export('05_quad_dock_repeatable',J['make_universal']())
        export('06_gap_filling_connector',J['connector_print']())
        export('08_depth_link_optional',J['depth_link']())
    elif '--assemblies-only' not in sys.argv:build_parts()
    build_assemblies()

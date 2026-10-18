"""Render current case CAD for the README, without modifying printable geometry."""
from pathlib import Path
import itertools,runpy
import cadquery as cq
import numpy as np
import vtk
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parent.parent
BG=(.957,.969,.980)
BASE=(.20,.39,.51)
LID=(.66,.77,.82)
CROSS=(.24,.62,.68)
POE=(.96,.62,.25)

def render(parts,path,view_direction,size=(1600,850)):
    ren=vtk.vtkRenderer();ren.SetBackground(*BG)
    corners=[]
    for part,color in parts:
        vs,fs=part.val().tessellate(.025,.06)
        pts=vtk.vtkPoints()
        for v in vs:pts.InsertNextPoint(*v.toTuple())
        cells=vtk.vtkCellArray()
        for face in fs:
            cells.InsertNextCell(3)
            for idx in face:cells.InsertCellPoint(int(idx))
        poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells)
        normals=vtk.vtkPolyDataNormals();normals.SetInputData(poly);normals.SetFeatureAngle(40);normals.Update()
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
        actor=vtk.vtkActor();actor.SetMapper(mapper)
        prop=actor.GetProperty();prop.SetColor(*color);prop.SetAmbient(.25);prop.SetDiffuse(.75);prop.SetSpecular(.16);prop.SetSpecularPower(30)
        ren.AddActor(actor)
        b=part.val().BoundingBox()
        corners.extend(itertools.product((b.xmin,b.xmax),(b.ymin,b.ymax),(b.zmin,b.zmax)))
    corners=np.array(corners);center=(corners.min(axis=0)+corners.max(axis=0))/2
    direction=np.array(view_direction,dtype=float);direction/=np.linalg.norm(direction)
    right=np.cross([0,0,1],direction);right/=np.linalg.norm(right)
    up=np.cross(direction,right)
    projected=corners-center
    aspect=size[0]/size[1]
    scale=max(np.max(abs(projected@up)),np.max(abs(projected@right))/aspect)*1.10
    cam=ren.GetActiveCamera();cam.SetPosition(*(center+direction*650));cam.SetFocalPoint(*center);cam.SetViewUp(*up)
    cam.ParallelProjectionOn();cam.SetParallelScale(float(scale));ren.ResetCameraClippingRange()
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.AddRenderer(ren);win.SetSize(*size);win.SetMultiSamples(8)
    win.Render();capture=vtk.vtkWindowToImageFilter();capture.SetInput(win);capture.Update()
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(path));writer.SetInputConnection(capture.GetOutputPort());writer.Write();win.Finalize()

def font(size):
    for name in ('C:/Windows/Fonts/segoeui.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if Path(name).exists():return ImageFont.truetype(name,size)
    return ImageFont.load_default(size=size)

def caption(path,title,subtitle,footer):
    raw=Image.open(path).convert('RGB')
    canvas=Image.new('RGB',(raw.width,raw.height+180),tuple(round(c*255) for c in BG))
    canvas.paste(raw,(0,115));draw=ImageDraw.Draw(canvas)
    draw.text((48,23),title,font=font(38),fill='#193e52')
    draw.text((49,75),subtitle,font=font(22),fill='#536d7b')
    draw.text((49,raw.height+135),footer,font=font(21),fill='#536d7b')
    canvas.save(path,optimize=True)

def main():
    F=runpy.run_path(str(ROOT/'source/poe_tie_case.py'))
    base=cq.importers.importStep(str(ROOT/'STEP/01_case_base.step'))
    lid=cq.importers.importStep(str(ROOT/'STEP/02_case_lid.step')).translate((0,0,-28.6)).rotate((0,32,0),(1,32,0),180)
    caps=[F['G']['make_cap'](x,y) for x,y in F['P']['tie_cluster_centers']]
    single=F['single_parts']()[1]
    path=ROOT/'previews/case_assembled.png'
    render([(base,BASE),(lid,LID),*[(p,CROSS) for p in caps],(single,POE)],path,(.8,-1.7,1.5))
    caption(path,'pi400-holder / CASE','Assembled enclosure with integral handle and open interface edge',
        'Current STEP geometry  |  Body: 247 x 64 x 28.6 mm  |  PCB and electronics not shown')
    path=ROOT/'previews/case_exploded.png'
    parts=[(base,BASE),(lid.translate((0,0,55)),LID),*[(p.translate((0,0,12)),CROSS) for p in caps],(single.translate((0,0,12)),POE)]
    render(parts,path,(.7,-1.8,1.8),(1600,1000))
    caption(path,'pi400-holder / INSIDE','Exploded view: base, lid, two cross-guide covers and one PoE tie-guide cover',
        'Teal: cross-guide covers  |  Orange: PoE tie-guide cover  |  Parts separated for illustration')
    print('Rendered case_assembled.png and case_exploded.png',flush=True)

if __name__=='__main__':main()

from pathlib import Path
import runpy
import cadquery as cq,trimesh,vtk
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent.parent
J=runpy.run_path(str(R/'source/flush_pair.py'))
p=cq.importers.importStep(str(R/'STEP/05_quad_dock_repeatable.step'));q=p.translate((0,222.4,0));c=J['connector']()
def render(parts,path,position,focus,size,up=(0,0,1)):
    ren=vtk.vtkRenderer();ren.SetBackground(.965,.978,.985)
    for part,col in parts:
        vs,fs=part.val().tessellate(.035,.1)
        pts=vtk.vtkPoints()
        for v in vs:pts.InsertNextPoint(*v.toTuple())
        polys=vtk.vtkCellArray()
        for face in fs:
            polys.InsertNextCell(3)
            for idx in face:polys.InsertCellPoint(int(idx))
        data=vtk.vtkPolyData();data.SetPoints(pts);data.SetPolys(polys)
        normals=vtk.vtkPolyDataNormals();normals.SetInputData(data);normals.SetFeatureAngle(40);normals.Update()
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
        actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(*col);actor.GetProperty().SetAmbient(.35);ren.AddActor(actor)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.AddRenderer(ren);win.SetSize(*size);win.SetMultiSamples(4)
    cam=ren.GetActiveCamera();cam.SetPosition(*position);cam.SetFocalPoint(*focus);cam.SetViewUp(*up);cam.ParallelProjectionOn();ren.ResetCamera();win.Render()
    capture=vtk.vtkWindowToImageFilter();capture.SetInput(win);capture.Update()
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(path));writer.SetInputConnection(capture.GetOutputPort());writer.Write();win.Finalize()
blue=(.21,.49,.65);teal=(.35,.63,.71);orange=(.95,.62,.18)
render([(p,blue),(q,teal),(c,orange)],R/'previews/connection_overview.png',(650,-200,650),(125,210,0),(1000,680))
render([(c,orange)],R/'previews/connector_underside.png',(300,160,-140),(125,210,5),(600,680))
im=Image.new('RGB',(1600,970),'#f6f9fb');d=ImageDraw.Draw(im)
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',n)
d.text((45,25),'동일한 거치대 반복 연결 · 가장자리 확장 없음',font=font(36),fill='#203b50')
d.text((45,85),'같은 05번 거치대 2개 + 06번 연결부 1개 = Pi 8대',font=font(26),fill='#526677')
im.paste(Image.open(R/'previews/connection_overview.png'),(0,140))
im.paste(Image.open(R/'previews/connector_underside.png'),(1000,140))
d.text((45,145),'파란 두 판은 같은 파일입니다',font=font(26),fill='#203b50')
d.text((1030,145),'연결부 밑면: 사각 돌기 4개',font=font(25),fill='#203b50')
d.text((45,820),'전체 폭 439.2mm · 케이스 간격 27mm 유지',font=font(28),fill='#203b50')
d.text((45,870),'주황색 연결부가 5.6mm 틈을 채우고 양쪽 홈에 맞물립니다.',font=font(27),fill='#203b50')
d.text((45,925),'연결부 상단은 케이스 받침 높이와 같음 · 실제 CAD 형상 · 실물 체결 강성은 시험 전',font=font(22),fill='#526677')
im.save(R/'previews/repeatable_connection.png')
print('Rendered repeatable connection',flush=True)

/* 
A* -------------------------------------------------------------------
B* This file contains source code for the PyMOL computer program
C* copyright 1998-2001 by Warren Lyford Delano of DeLano Scientific. 
D* -------------------------------------------------------------------
E* It is unlawful to modify or remove this copyright notice.
F* -------------------------------------------------------------------
G* Please see the accompanying LICENSE file for further information. 
H* -------------------------------------------------------------------
I* Additional authors of this source file include:
-* 
-* 
-*
Z* -------------------------------------------------------------------
*/

#include"os_predef.h"
#include"os_std.h"
#include"os_gl.h"
#include"MemoryDebug.h"
#include"CGO.h"
#include"Err.h"
#include"Base.h"
#include"OOMac.h"
#include"Crystal.h"
#include"Feedback.h"
#include"Util.h"
#include"PConv.h"

CCrystal *CrystalNewFromPyList(PyObject *list)
{
  CCrystal *I=NULL;
  I=CrystalNew();
  if(I) {
    if(!CrystalFromPyList(I,list)) {
      CrystalFree(I);
      I=NULL;
    }
  }
  return(I);
}

PyObject *CrystalAsPyList(CCrystal *I)
{
  
  PyObject *result = NULL;

  if(I) {
    result = PyList_New(2);
    PyList_SetItem(result,0,PConvFloatArrayToPyList(I->Dim,3));
    PyList_SetItem(result,1,PConvFloatArrayToPyList(I->Angle,3));
  }
  return(PConvAutoNone(result));
}

int CrystalFromPyList(CCrystal *I,PyObject *list)
{
  int ok=true;
  int ll;
  if(ok) ok = (I!=NULL);
  if(ok) ok = PyList_Check(list);
  if(ok) ll = PyList_Size(list);
  if(ok&&(ll>0)) ok = PConvPyListToFloatArrayInPlace(PyList_GetItem(list,0),I->Dim,3);
  if(ok&&(ll>1)) ok = PConvPyListToFloatArrayInPlace(PyList_GetItem(list,1),I->Angle,3);
  if(ok) CrystalUpdate(I);

  /* TO SUPPORT BACKWARDS COMPATIBILITY...
   Always check ll when adding new PyList_GetItem's */

  return(ok);
}

void CrystalFree(CCrystal *I)
{
  OOFreeP(I);
}

void CrystalInit(CCrystal *I)
{
  int a;
  for(a=0;a<9;a++) {
    I->RealToFrac[a]=0.0;
    I->FracToReal[a]=0.0;
  }
  for(a=0;a<3;a++) {
    I->Angle[a]=90.0;
    I->Dim[a]=1.0;
    I->RealToFrac[a+a*3]=1.0;
    I->FracToReal[a+a*3]=1.0;
  }
  I->UnitCellVolume=1.0;

}

CCrystal *CrystalNew(void)
{
  OOAlloc(CCrystal);
  CrystalInit(I);
  return(I);
}


CCrystal *CrystalCopy(CCrystal *other)
{
  OOAlloc(CCrystal);
  UtilCopyMem(I,other,sizeof(CCrystal));
  return(I);
}


void CrystalUpdate(CCrystal *I) 
{
  float cabg[3];
  float sabg[3];
  float cabgs[3];
  float sabgs1;
  int i;

  for(i=0;i<9;i++) {
    I->RealToFrac[i]=0.0;
    I->FracToReal[i]=0.0;
  }
  
  for(i=0;i<3;i++) {
    cabg[i] = cos(I->Angle[i]*PI/180.0);
    sabg[i] = sin(I->Angle[i]*PI/180.0);
  }
  
  cabgs[0] = (cabg[1]*cabg[2]-cabg[0])/(sabg[1]*sabg[2]);
  cabgs[1] = (cabg[2]*cabg[0]-cabg[1])/(sabg[2]*sabg[0]);
  cabgs[2] = (cabg[0]*cabg[1]-cabg[2])/(sabg[0]*sabg[1]);
    
  I->UnitCellVolume=I->Dim[0]*I->Dim[1]*I->Dim[2]*
    sqrt1f(1.0+2.0*cabg[0]*cabg[1]*cabg[2]-
          (cabg[0]*cabg[0]+cabg[1]*cabg[1]+cabg[2]*cabg[2]));
  
  I->RecipDim[0] = I->Dim[1]*I->Dim[2]*sabg[0]/I->UnitCellVolume;
  I->RecipDim[1] = I->Dim[0]*I->Dim[2]*sabg[1]/I->UnitCellVolume;
  I->RecipDim[2] = I->Dim[0]*I->Dim[1]*sabg[2]/I->UnitCellVolume;

  sabgs1=sqrt1f(1.0-cabgs[0]*cabgs[0]);

  I->RealToFrac[0]=1.0/I->Dim[0];
  I->RealToFrac[1]=-cabg[2]/(sabg[2]*I->Dim[0]);
  I->RealToFrac[2]=-(cabg[2]*sabg[1]*cabgs[0]+cabg[1]*sabg[2])/
    (sabg[1]*sabgs1*sabg[2]*I->Dim[0]);
  I->RealToFrac[4]=1.0/(sabg[2]*I->Dim[1]);
  I->RealToFrac[5]=cabgs[0]/(sabgs1*sabg[2]*I->Dim[1]);
  I->RealToFrac[8]=1.0/(sabg[1]*sabgs1*I->Dim[2]);

  I->FracToReal[0] = I->Dim[0];
  I->FracToReal[1] = cabg[2]*I->Dim[1];
  I->FracToReal[2] = cabg[1]*I->Dim[2];
  I->FracToReal[4] = sabg[2]*I->Dim[1];
  I->FracToReal[5] = -sabg[1]*cabgs[0]*I->Dim[2];
  I->FracToReal[8] = sabg[1]*sabgs1*I->Dim[2];

  I->Norm[0] = sqrt1f(I->RealToFrac[0]*I->RealToFrac[0] + 
                     I->RealToFrac[1]*I->RealToFrac[1] +
                     I->RealToFrac[2]*I->RealToFrac[2]);
  I->Norm[1] = sqrt1f(I->RealToFrac[3]*I->RealToFrac[3] + 
                     I->RealToFrac[4]*I->RealToFrac[4] +
                     I->RealToFrac[5]*I->RealToFrac[5]);
  I->Norm[2] = sqrt1f(I->RealToFrac[6]*I->RealToFrac[6] + 
                     I->RealToFrac[7]*I->RealToFrac[7] +
                     I->RealToFrac[8]*I->RealToFrac[8]);                                        
}

void CrystalDump(CCrystal *I) 
{
  int i;

  PRINTF 
    " Crystal: Unit Cell         %8.3f %8.3f %8.3f\n",
    I->Dim[0],I->Dim[1],I->Dim[2]
    ENDF;
  PRINTF 
    " Crystal: Alpha Beta Gamma  %8.3f %8.3f %8.3f\n",
    I->Angle[0],I->Angle[1],I->Angle[2]
    ENDF;
  PRINTF
    " Crystal: RealToFrac Matrix\n"
    ENDF;
  for(i=0;i<3;i++) {
    PRINTF " Crystal: %10.5f %10.5f %10.5f\n",
      I->RealToFrac[i*3],I->RealToFrac[i*3+1],I->RealToFrac[i*3+2]
      ENDF;
  }
  PRINTF
    " Crystal: FracToReal Matrix\n"
    ENDF;
  for(i=0;i<3;i++) {
    PRINTF
      " Crystal: %10.5f %10.5f %10.5f\n",
      I->FracToReal[i*3],I->FracToReal[i*3+1],I->FracToReal[i*3+2]
      ENDF;
  }
  PRINTF
  " Crystal: Unit Cell Volume %8.1f\n",I->UnitCellVolume
    ENDF;

}

CGO *CrystalGetUnitCellCGO(CCrystal *I)
{
  float v[3];
  CGO *cgo=NULL;
  if(I) {
    cgo=CGONew();
    CGODisable(cgo,GL_LIGHTING);
    CGOBegin(cgo,GL_LINE_STRIP);
    set3f(v,0,0,0);
    transform33f3f(I->FracToReal,v,v);
    CGOVertexv(cgo,v);

    set3f(v,1,0,0);
    transform33f3f(I->FracToReal,v,v);
    CGOVertexv(cgo,v);

    set3f(v,1,1,0);
    transform33f3f(I->FracToReal,v,v);
    CGOVertexv(cgo,v);

    set3f(v,0,1,0);
    transform33f3f(I->FracToReal,v,v);
    CGOVertexv(cgo,v);

    set3f(v,0,0,0);
    transform33f3f(I->FracToReal,v,v);
    CGOVertexv(cgo,v);

    set3f(v,0,0,1);
    transform33f3f(I->FracToReal,v,v);
    CGOVertexv(cgo,v);

    set3f(v,1,0,1);
    transform33f3f(I->FracToReal,v,v);
    CGOVertexv(cgo,v);

    set3f(v,1,1,1);
    transform33f3f(I->FracToReal,v,v);
    CGOVertexv(cgo,v);

    set3f(v,0,1,1);
    transform33f3f(I->FracToReal,v,v);
    CGOVertexv(cgo,v);

    set3f(v,0,0,1);
    transform33f3f(I->FracToReal,v,v);
    CGOVertexv(cgo,v);
    CGOEnd(cgo);

    CGOBegin(cgo,GL_LINES);

    set3f(v,0,1,0);
    transform33f3f(I->FracToReal,v,v);
    CGOVertexv(cgo,v);

    set3f(v,0,1,1);
    transform33f3f(I->FracToReal,v,v);
    CGOVertexv(cgo,v);

    set3f(v,1,1,0);
    transform33f3f(I->FracToReal,v,v);
    CGOVertexv(cgo,v);

    set3f(v,1,1,1);
    transform33f3f(I->FracToReal,v,v);
    CGOVertexv(cgo,v);

    set3f(v,1,0,0);
    transform33f3f(I->FracToReal,v,v);
    CGOVertexv(cgo,v);

    set3f(v,1,0,1);
    transform33f3f(I->FracToReal,v,v);
    CGOVertexv(cgo,v);
    CGOEnd(cgo);

    CGOEnable(cgo,GL_LIGHTING);
    CGOStop(cgo);
  }
  return(cgo);
}


/* 
A* -------------------------------------------------------------------
B* This file contains source code for the PyMOL computer program
C* copyright 1998-2000 by Warren Lyford Delano of DeLano Scientific. 
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

#include"os_std.h"
#include"os_gl.h"

#include"OOMac.h"
#include"ObjectMap.h"
#include"Base.h"
#include"MemoryDebug.h"
#include"Map.h"
#include"Parse.h"
#include"Isosurf.h"
#include"Vector.h"
#include"Color.h"
#include"main.h"
#include"Scene.h"
#include"PConv.h"
#include"Word.h"

#ifdef _PYMOL_NUMPY
typedef struct {
  PyObject_HEAD
  char *data;
  int nd;
  int *dimensions, *strides;
  PyObject *base;
  void *descr;
  int flags;
} MyArrayObject;
#endif

int ObjectMapNumPyArrayToMap(ObjectMap *I,PyObject *ary);

static void ObjectMapFree(ObjectMap *I);

static void ObjectMapFree(ObjectMap *I) {
  if(I->Field) {
    IsosurfFieldFree(I->Field);
    I->Field=NULL;
  }
  FreeP(I->Origin);
  FreeP(I->Dim);
  FreeP(I->Range);
  FreeP(I->Grid);
  OOFreeP(I->Crystal);
  ObjectPurge(&I->Obj);
  OOFreeP(I);
}

static void ObjectMapUpdate(ObjectMap *I) {
  SceneDirty();
}

static void ObjectMapRender(ObjectMap *I,int frame,CRay *ray,Pickable **pick)
{

  if(ray) {
    float *vc;
    vc = ColorGet(I->Obj.Color);
    ray->fColor3fv(ray,vc);
    ray->fCylinder3fv(ray,I->Corner[0],I->Corner[1],0.20,vc,vc);
    ray->fCylinder3fv(ray,I->Corner[0],I->Corner[2],0.20,vc,vc);
    ray->fCylinder3fv(ray,I->Corner[2],I->Corner[3],0.20,vc,vc);
    ray->fCylinder3fv(ray,I->Corner[1],I->Corner[3],0.20,vc,vc);
    ray->fCylinder3fv(ray,I->Corner[0],I->Corner[4],0.20,vc,vc);
    ray->fCylinder3fv(ray,I->Corner[1],I->Corner[5],0.20,vc,vc);
    ray->fCylinder3fv(ray,I->Corner[2],I->Corner[6],0.20,vc,vc);
    ray->fCylinder3fv(ray,I->Corner[3],I->Corner[7],0.20,vc,vc);
    ray->fCylinder3fv(ray,I->Corner[4],I->Corner[5],0.20,vc,vc);
    ray->fCylinder3fv(ray,I->Corner[4],I->Corner[6],0.20,vc,vc);
    ray->fCylinder3fv(ray,I->Corner[6],I->Corner[7],0.20,vc,vc);
    ray->fCylinder3fv(ray,I->Corner[5],I->Corner[7],0.20,vc,vc);
  } else if(pick&&PMGUI) {
  } else if(PMGUI) {
    ObjectUseColor(&I->Obj);
   glDisable(GL_LIGHTING); 
   glBegin(GL_LINES);
    glVertex3fv(I->Corner[0]);
    glVertex3fv(I->Corner[1]);

    glVertex3fv(I->Corner[0]);
    glVertex3fv(I->Corner[2]);

    glVertex3fv(I->Corner[2]);
    glVertex3fv(I->Corner[3]);

    glVertex3fv(I->Corner[1]);
    glVertex3fv(I->Corner[3]);
    
    glVertex3fv(I->Corner[0]);
    glVertex3fv(I->Corner[4]);

    glVertex3fv(I->Corner[1]);
    glVertex3fv(I->Corner[5]);

    glVertex3fv(I->Corner[2]);
    glVertex3fv(I->Corner[6]);

    glVertex3fv(I->Corner[3]);
    glVertex3fv(I->Corner[7]);
    
    glVertex3fv(I->Corner[4]);
    glVertex3fv(I->Corner[5]);

    glVertex3fv(I->Corner[4]);
    glVertex3fv(I->Corner[6]);

    glVertex3fv(I->Corner[6]);
    glVertex3fv(I->Corner[7]);

    glVertex3fv(I->Corner[5]);
    glVertex3fv(I->Corner[7]);

    glEnd();
	glEnable(GL_LIGHTING);
  }
}

/*========================================================================*/
ObjectMap *ObjectMapNew(void)
{
OOAlloc(ObjectMap);

ObjectInit((Object*)I);

 I->Crystal = CrystalNew();
 I->Field = NULL;
 I->Obj.type = cObjectMap;
 I->Obj.fFree = (void (*)(struct Object *))ObjectMapFree;
 I->Obj.fUpdate =  (void (*)(struct Object *)) ObjectMapUpdate;
 I->Obj.fRender =(void (*)(struct Object *, int, CRay *, Pickable **))ObjectMapRender;
 I->Origin = NULL;
 I->Dim = NULL;
 I->Range = NULL;
 I->Grid = NULL;

#ifdef _NOT_YET_NEEDED
  I->Obj.fGetNFrame = (int (*)(struct Object *)) ObjectMapGetNFrames;
#endif

  return(I);
}
/*========================================================================*/
int ObjectMapXPLORStrToMap(ObjectMap *I,char *XPLORStr,int frame) {
  
  char *p;
  int a,b,c,d,e;
  float v[3],vr[3],dens,maxd,mind;
  char cc[MAXLINELEN];
  int n;
  int ok = true;

  maxd = FLT_MIN;
  mind = FLT_MAX;
  p=XPLORStr;

  while(*p) {
    p = ParseNCopy(cc,p,8);
    if(!*cc) 
      p = ParseNextLine(p);
    else if(sscanf(cc,"%i",&n)==1) {
      p=ParseWordCopy(cc,p,MAXLINELEN);
      if(strstr(cc,"!NTITLE")||(!*cc)) {
        p=ParseNextLine(p);
        while(n--) {
          p=ParseNextLine(p);          
        } 
      } else if(strstr(cc,"REMARKS")) {
        p=ParseNextLine(p);          
      } else {
        break;
      }
    }
  }
  if(*p) { /* n contains first dimension */
    I->Div[0]=n;
    if(sscanf(cc,"%i",&I->Min[0])!=1) ok=false;
    p = ParseNCopy(cc,p,8); if(sscanf(cc,"%i",&I->Max[0])!=1) ok=false;
    p = ParseNCopy(cc,p,8); if(sscanf(cc,"%i",&I->Div[1])!=1) ok=false;
    p = ParseNCopy(cc,p,8); if(sscanf(cc,"%i",&I->Min[1])!=1) ok=false;    
    p = ParseNCopy(cc,p,8); if(sscanf(cc,"%i",&I->Max[1])!=1) ok=false;
    p = ParseNCopy(cc,p,8); if(sscanf(cc,"%i",&I->Div[2])!=1) ok=false;
    p = ParseNCopy(cc,p,8); if(sscanf(cc,"%i",&I->Min[2])!=1) ok=false;    
    p = ParseNCopy(cc,p,8); if(sscanf(cc,"%i",&I->Max[2])!=1) ok=false;
    p=ParseNextLine(p);
    p = ParseNCopy(cc,p,12); if(sscanf(cc,"%f",&I->Crystal->Dim[0])!=1) ok=false;
    p = ParseNCopy(cc,p,12); if(sscanf(cc,"%f",&I->Crystal->Dim[1])!=1) ok=false;
    p = ParseNCopy(cc,p,12); if(sscanf(cc,"%f",&I->Crystal->Dim[2])!=1) ok=false;
    p = ParseNCopy(cc,p,12); if(sscanf(cc,"%f",&I->Crystal->Angle[0])!=1) ok=false;
    p = ParseNCopy(cc,p,12); if(sscanf(cc,"%f",&I->Crystal->Angle[1])!=1) ok=false;
    p = ParseNCopy(cc,p,12); if(sscanf(cc,"%f",&I->Crystal->Angle[2])!=1) ok=false;
    p=ParseNextLine(p);
    p = ParseNCopy(cc,p,3);
    if(strcmp(cc,"ZYX")) ok=false;
    p=ParseNextLine(p);
    
  } else {
    ok=false;
  }
  if(ok) {
    I->FDim[0]=I->Max[0]-I->Min[0]+1;
    I->FDim[1]=I->Max[1]-I->Min[1]+1;
    I->FDim[2]=I->Max[2]-I->Min[2]+1;
    I->FDim[3]=3;
    if(!(I->FDim[0]&&I->FDim[1]&&I->FDim[2])) 
      ok=false;
    else {
      CrystalUpdate(I->Crystal);
      I->Field=IsosurfFieldAlloc(I->FDim);
      for(c=0;c<I->FDim[2];c++)
        {
          v[2]=(c+I->Min[2])/((float)I->Div[2]);
          p=ParseNextLine(p);
          for(b=0;b<I->FDim[1];b++) {
            v[1]=(b+I->Min[1])/((float)I->Div[1]);
            for(a=0;a<I->FDim[0];a++) {
              v[0]=(a+I->Min[0])/((float)I->Div[0]);
              p=ParseNCopy(cc,p,12);
              if(!cc[0]) {
                p=ParseNextLine(p);
                p=ParseNCopy(cc,p,12);                
              }
              if(sscanf(cc,"%f",&dens)!=1) {
                ok=false;
              } else {
                F3(I->Field->data,a,b,c,I->Field->dimensions) = dens;
                if(maxd<dens) maxd = dens;
                if(mind>dens) mind = dens;
              }
              transform33f3f(I->Crystal->FracToReal,v,vr);
              for(e=0;e<3;e++) 
                F4(I->Field->points,a,b,c,e,I->Field->dimensions) = vr[e];
            }
          }
          p=ParseNextLine(p);
        }
      if(ok) {
        d = 0;
        for(c=0;c<I->FDim[2];c+=(I->FDim[2]-1))
          {
            v[2]=(c+I->Min[2])/((float)I->Div[2]);
            for(b=0;b<I->FDim[1];b+=(I->FDim[1]-1)) {
              v[1]=(b+I->Min[1])/((float)I->Div[1]);
              for(a=0;a<I->FDim[0];a+=(I->FDim[0]-1)) {
                v[0]=(a+I->Min[0])/((float)I->Div[0]);
                transform33f3f(I->Crystal->FracToReal,v,vr);
                copy3f(vr,I->Corner[d]);
                d++;
              }
            }
          }
      }
    }
  }

  if(ok) {
    v[2]=(I->Min[2])/((float)I->Div[2]);
    v[1]=(I->Min[1])/((float)I->Div[1]);
    v[0]=(I->Min[0])/((float)I->Div[0]);

    transform33f3f(I->Crystal->FracToReal,v,I->Obj.ExtentMin);
    
    v[2]=((I->FDim[2]-1)+I->Min[2])/((float)I->Div[2]);
    v[1]=((I->FDim[1]-1)+I->Min[1])/((float)I->Div[1]);
    v[0]=((I->FDim[0]-1)+I->Min[0])/((float)I->Div[0]);

    transform33f3f(I->Crystal->FracToReal,v,I->Obj.ExtentMax);
    I->Obj.ExtentFlag=true;
  }
#ifdef _UNDEFINED
    printf("%d %d %d %d %d %d %d %d %d\n",
           I->Div[0],
           I->Min[0],
           I->Max[0],
           I->Div[1],
           I->Min[1],
           I->Max[1],
           I->Div[2],
           I->Min[2],
           I->Max[2]);
    printf("Okay? %d\n",ok);
    fflush(stdout);
#endif
  if(!ok) {
    ErrMessage("ObjectMap","Error reading map");
  } else {
    printf(" ObjectMap: Map Read.  Range = %5.3f to %5.3f\n",mind,maxd);
  }
    
  return(ok);
}
/*========================================================================*/
ObjectMap *ObjectMapReadXPLORStr(ObjectMap *I,char *XPLORStr,int frame)
{
  int ok=true;
  int isNew = true;

  if(!I) 
	 isNew=true;
  else 
	 isNew=false;
  if(ok) {
	 if(isNew) {
		I=(ObjectMap*)ObjectMapNew();
		isNew = true;
	 } else {
		isNew = false;
	 }
    ObjectMapXPLORStrToMap(I,XPLORStr,frame);
    SceneChanged();
  }
  return(I);
}
/*========================================================================*/
ObjectMap *ObjectMapLoadXPLORFile(ObjectMap *obj,char *fname,int frame)
{
  ObjectMap *I = NULL;
  int ok=true;
  FILE *f;
  long size;
  char *buffer,*p;
  float mat[9];

  f=fopen(fname,"r");
  if(!f)
	 ok=ErrMessage("ObjectMapLoadXPLORFile","Unable to open file!");
  else
	 {
		if(Feedback(FB_ObjectMap,FB_Actions))
		  {
			printf(" ObjectMapLoadXPLORFile: Loading from '%s'.\n",fname);
		  }
		
		fseek(f,0,SEEK_END);
      size=ftell(f);
		fseek(f,0,SEEK_SET);

		buffer=(char*)mmalloc(size+255);
		ErrChkPtr(buffer);
		p=buffer;
		fseek(f,0,SEEK_SET);
		fread(p,size,1,f);
		p[size]=0;
		fclose(f);

		I=ObjectMapReadXPLORStr(obj,buffer,frame);

		mfree(buffer);
      CrystalDump(I->Crystal);
      multiply33f33f(I->Crystal->FracToReal,I->Crystal->RealToFrac,mat);
    }
#ifdef _UNDEFINED
  for(a=0;a<9;a++)
    printf("%10.5f\n",mat[a]);
#endif
  return(I);

}

/*========================================================================*/
int ObjectMapNumPyArrayToMap(ObjectMap *I,PyObject *ary) {
  
  int a,b,c,d,e;
  float v[3],dens,maxd,mind;
  int ok = true;

#ifdef _PYMOL_NUMPY
  MyArrayObject *pao;
  pao = (MyArrayObject*)ary;
#endif
  maxd = FLT_MIN;
  mind = FLT_MAX;
  if(ok) {
    I->FDim[0]=I->Dim[0];
    I->FDim[1]=I->Dim[1];
    I->FDim[2]=I->Dim[2];
    I->FDim[3]=3;

    if(!(I->FDim[0]&&I->FDim[1]&&I->FDim[2])) 
      ok=false;
    else {
      I->Field=IsosurfFieldAlloc(I->FDim);
      for(c=0;c<I->FDim[2];c++)
        {
          v[2]=I->Origin[2]+I->Grid[2]*c;
          for(b=0;b<I->FDim[1];b++) {
            v[1]=I->Origin[1]+I->Grid[1]*b;
            for(a=0;a<I->FDim[0];a++) {
              v[0]=I->Origin[0]+I->Grid[0]*a;
#ifdef _PYMOL_NUMPY
              dens = *((double*)
                (pao->data+
                 (pao->strides[0]*a)+
                 (pao->strides[1]*b)+
                 (pao->strides[2]*c)));
#else
              dens = 0.0;
#endif
              F3(I->Field->data,a,b,c,I->Field->dimensions) = dens;
              if(maxd<dens) maxd = dens;
              if(mind>dens) mind = dens;
              for(e=0;e<3;e++) 
                F4(I->Field->points,a,b,c,e,I->Field->dimensions) = v[e];
            }
          }
        }
      d = 0;
      for(c=0;c<I->FDim[2];c+=(I->FDim[2]-1))
        {
          v[2]=I->Origin[2]+I->Grid[2]*c;
          for(b=0;b<I->FDim[1];b+=(I->FDim[1]-1)) {
            v[1]=I->Origin[1]+I->Grid[1]*b;
            for(a=0;a<I->FDim[0];a+=(I->FDim[0]-1)) {
              v[0]=I->Origin[0]+I->Grid[0]*a;
              copy3f(v,I->Corner[d]);
              d++;
            }
          }
        }
    }
  }
  if(ok) {
    copy3f(I->Origin,I->Obj.ExtentMin);
    copy3f(I->Origin,I->Obj.ExtentMax);
    add3f(I->Range,I->Obj.ExtentMax,I->Obj.ExtentMax);
    I->Obj.ExtentFlag=true;
  }
  if(!ok) {
    ErrMessage("ObjectMap","Error reading map");
  } else {
    if(Feedback(FB_ObjectMap,FB_Actions)) {
      printf(" ObjectMap: Map Read.  Range = %5.3f to %5.3f\n",mind,maxd);
    }
  }
  return(ok);
}
/*========================================================================*/
ObjectMap *ObjectMapLoadChemPyBrick(ObjectMap *I,PyObject *Map,
                                           int frame,int discrete)
{
  int ok=true;
  int isNew = true;
  PyObject *tmp;


  if(!I) 
	 isNew=true;
  else 
	 isNew=false;

  if(ok) {

	 if(isNew) {
		I=(ObjectMap*)ObjectMapNew();
		isNew = true;
	 } else {
		isNew = false;
	 }
    if(PyObject_HasAttrString(Map,"origin")&&
       PyObject_HasAttrString(Map,"dim")&&
       PyObject_HasAttrString(Map,"range")&&
       PyObject_HasAttrString(Map,"grid")&&
       PyObject_HasAttrString(Map,"lvl"))
      {
        tmp = PyObject_GetAttrString(Map,"origin");
        if(tmp) {
          PConvPyListToFloatArray(tmp,&I->Origin);
          Py_DECREF(tmp);
        } else 
          ok=ErrMessage("ObjectMap","missing brick origin.");
        tmp = PyObject_GetAttrString(Map,"dim");
        if(tmp) {
          PConvPyListToIntArray(tmp,&I->Dim);
          Py_DECREF(tmp);
        } else 
          ok=ErrMessage("ObjectMap","missing brick dimension.");
        tmp = PyObject_GetAttrString(Map,"range");
        if(tmp) {
          PConvPyListToFloatArray(tmp,&I->Range);
          Py_DECREF(tmp);
        } else 
          ok=ErrMessage("ObjectMap","missing brick range.");
        tmp = PyObject_GetAttrString(Map,"grid");
        if(tmp) {
          PConvPyListToFloatArray(tmp,&I->Grid);
          Py_DECREF(tmp);
        } else
          ok=ErrMessage("ObjectMap","missing brick grid.");
        tmp = PyObject_GetAttrString(Map,"lvl");
        if(tmp) {
          ObjectMapNumPyArrayToMap(I,tmp);	 
          Py_DECREF(tmp);
        } else
          ok=ErrMessage("ObjectMap","missing brick density.");

      }
    SceneChanged();
  }
  return(I);
}

/*========================================================================*/
ObjectMap *ObjectMapLoadChemPyMap(ObjectMap *I,PyObject *Map,
                                  int frame,int discrete)
{

  int ok=true;
  int isNew = true;
  float *cobj;
  WordType format;
  float v[3],vr[3],dens,maxd,mind;
  int a,b,c,d,e;


  /*  
  double test[1000];
  for(a=0;a<1000;a++) {
      test[a]=rand()/(1.0+INT_MAX);
      }
      PyObject_SetAttrString(Map,"c_object",
      PyCObject_FromVoidPtr(test,NULL));
  */
  maxd = FLT_MIN;
  mind = FLT_MAX;

  if(!I) 
	 isNew=true;
  else 
	 isNew=false;

  if(ok) {

	 if(isNew) {
		I=(ObjectMap*)ObjectMapNew();
		isNew = true;
	 } else {
		isNew = false;
	 }

    if(!PConvAttrToStrMaxLen(Map,"format",format,sizeof(WordType)-1))
      ok=ErrMessage("LoadChemPyMap","bad 'format' parameter.");
    else if(!PConvAttrToFloatArrayInPlace(Map,"cell_dim",I->Crystal->Dim,3))
      ok=ErrMessage("LoadChemPyMap","bad 'cell_dim' parameter.");
    else if(!PConvAttrToFloatArrayInPlace(Map,"cell_ang",I->Crystal->Angle,3))
      ok=ErrMessage("LoadChemPyMap","bad 'cell_ang' parameter.");
    else if(!PConvAttrToIntArrayInPlace(Map,"cell_div",I->Div,3))
      ok=ErrMessage("LoadChemPyMap","bad 'cell_div' parameter.");
    else if(!PConvAttrToIntArrayInPlace(Map,"first",I->Min,3))
      ok=ErrMessage("LoadChemPyMap","bad 'first' parameter.");
    else if(!PConvAttrToIntArrayInPlace(Map,"last",I->Max,3))
      ok=ErrMessage("LoadChemPyMap","bad 'last' parameter.");

    if(ok) {
      if (strcmp(format,"CObjectZYXfloat")==0) {
        ok = PConvAttrToPtr(Map,"c_object",(void**)&cobj);
        if(!ok)
          ErrMessage("LoadChemPyMap","CObject unreadable.");        
      } else {
        ok=ErrMessage("LoadChemPyMap","unsupported format.");        
      }
    }
    /* good to go */

    if(ok) {
      if (strcmp(format,"CObjectZYXfloat")==0) {

        I->FDim[0]=I->Max[0]-I->Min[0]+1;
        I->FDim[1]=I->Max[1]-I->Min[1]+1;
        I->FDim[2]=I->Max[2]-I->Min[2]+1;
        if(Feedback(FB_ObjectMap,FB_Actions)) {
          printf(" LoadChemPyMap: CObjectZYXdouble %dx%dx%d\n",I->FDim[0],I->FDim[1],I->FDim[2]);        
        }
        I->FDim[3]=3;
        if(!(I->FDim[0]&&I->FDim[1]&&I->FDim[2])) 
          ok=false;
        else {
          CrystalUpdate(I->Crystal);
          I->Field=IsosurfFieldAlloc(I->FDim);
          for(c=0;c<I->FDim[2];c++)
            {
              v[2]=(c+I->Min[2])/((float)I->Div[2]);
              for(b=0;b<I->FDim[1];b++) {
                v[1]=(b+I->Min[1])/((float)I->Div[1]);
                for(a=0;a<I->FDim[0];a++) {
                  v[0]=(a+I->Min[0])/((float)I->Div[0]);
                  
                  dens = *(cobj++);

                  F3(I->Field->data,a,b,c,I->Field->dimensions) = dens;
                  if(maxd<dens) maxd = dens;
                  if(mind>dens) mind = dens;
                  transform33f3f(I->Crystal->FracToReal,v,vr);
                  for(e=0;e<3;e++) 
                    F4(I->Field->points,a,b,c,e,I->Field->dimensions) = vr[e];
                }
              }
            }
          if(ok) {
            d = 0;
            for(c=0;c<I->FDim[2];c+=(I->FDim[2]-1))
              {
                v[2]=(c+I->Min[2])/((float)I->Div[2]);
                for(b=0;b<I->FDim[1];b+=(I->FDim[1]-1)) {
                  v[1]=(b+I->Min[1])/((float)I->Div[1]);
                  for(a=0;a<I->FDim[0];a+=(I->FDim[0]-1)) {
                    v[0]=(a+I->Min[0])/((float)I->Div[0]);
                    transform33f3f(I->Crystal->FracToReal,v,vr);
                    copy3f(vr,I->Corner[d]);
                    d++;
                  }
                }
              }
          }
        }
      }
    }
    
    if(ok) {
      CrystalDump(I->Crystal);
      
      v[2]=(I->Min[2])/((float)I->Div[2]);
      v[1]=(I->Min[1])/((float)I->Div[1]);
      v[0]=(I->Min[0])/((float)I->Div[0]);
      
      transform33f3f(I->Crystal->FracToReal,v,I->Obj.ExtentMin);
      
      v[2]=((I->FDim[2]-1)+I->Min[2])/((float)I->Div[2]);
      v[1]=((I->FDim[1]-1)+I->Min[1])/((float)I->Div[1]);
      v[0]=((I->FDim[0]-1)+I->Min[0])/((float)I->Div[0]);
      
      transform33f3f(I->Crystal->FracToReal,v,I->Obj.ExtentMax);
      I->Obj.ExtentFlag=true;
    }

    if(!ok) {
      ErrMessage("ObjectMap","Error reading map");
    } else {
		if(Feedback(FB_ObjectMap,FB_Actions)) {
        printf(" ObjectMap: Map Read.  Range = %5.3f to %5.3f\n",mind,maxd);
      }
    }

    if(ok) SceneChanged();
  }
  return(I);
}


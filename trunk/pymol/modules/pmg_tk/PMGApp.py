#A* -------------------------------------------------------------------
#B* This file contains source code for the PyMOL computer program
#C* copyright 1998-2000 by Warren Lyford Delano of DeLano Scientific. 
#D* -------------------------------------------------------------------
#E* It is unlawful to modify or remove this copyright notice.
#F* -------------------------------------------------------------------
#G* Please see the accompanying LICENSE file for further information. 
#H* -------------------------------------------------------------------
#I* Additional authors of this source file include:
#-*
#-* NOTE: Based on code by John E. Grayson which was in turn 
#-* based on code written by Doug Hellmann. 
#Z* -------------------------------------------------------------------

from Tkinter import *
from tkFileDialog import *

from AbstractApp import AbstractApp
from Setting import Setting
from SetEditor import SetEditor
from ColorEditor import ColorEditor

import Pmw
import sys, string
import pymol
from pymol import cmd
from pymol import util
import re
import thread
import threading
import os
from glob import glob
import __builtin__
import traceback
import Queue

class PMGApp(AbstractApp):

   appversion     = '0.72'
   appname       = 'PyMOL Molecular Graphics System'
   copyright      = 'Copyright (C) 1998-2001 by Warren DeLano of\nDeLano Scientific. All rights reserved.'
   contactweb     = 'http://www.pymol.org'
   contactemail   = 'warren@delanoscientific.com'

   def appInit(self): # create a global variable for the external gui
      pymol._ext_gui = self
      self.fifo = Queue.Queue(0)

   def execute(self,cmmd): 
      self.fifo.put(cmmd)

   def buttonAdd(self,frame,text,cmd):
      newBtn=self.createcomponent('button', (), None,
         Button,frame,text=text,highlightthickness=0,
         command=cmd,padx=0,pady=0)
      newBtn.pack(side=LEFT,fill=BOTH,expand=YES)
      
   def createButtons(self):
      
      row2 = self.createcomponent('row2', (), None,
         Frame,self.get_commandFrame(),bd=0)
      row2.pack(side=TOP,fill=BOTH,expand=YES)
      btn_reset = self.buttonAdd(row2,'Reset',lambda: cmd.do("_ reset"))
      btn_rtrace = self.buttonAdd(row2,'Ray Trace',lambda : cmd.do("_ ray"))
      btn_reset = self.buttonAdd(row2,'Rock',lambda :cmd.do("_ rock"))

      row3 = self.createcomponent('row3', (), None,
         Frame,self.get_commandFrame(),bd=0)
      row3.pack(side=TOP,fill=BOTH,expand=YES)
      btn_unpick = self.buttonAdd(row3,'Unpick',lambda : cmd.do("_ unpick"))
      btn_hidesele = self.buttonAdd(row3,'Hide Sele',self.hide_sele)
      btn_getview = self.buttonAdd(row3,'Get View',lambda : cmd.get_view()) # doesn't get logged

#      row3 = self.createcomponent('row3', (), None,
#         Frame,self.get_commandFrame(),bd=0)
#      row3.pack(side=TOP,fill=BOTH,expand=YES)
#      btn_reset = self.buttonAdd(row3,'Barf',self.quit)
#      btn_reset = self.buttonAdd(row3,'Now',self.quit)
#      btn_reset = self.buttonAdd(row3,'Eat',self.quit)
#      btn_reset = self.buttonAdd(row3,'Shrimp',self.quit)

      row1 = self.createcomponent('row1', (), None,
         Frame,self.get_commandFrame(),bd=0)
      row1.pack(side=TOP,fill=BOTH,expand=YES)
      btn_rewind = self.buttonAdd(row1,'|<',lambda : cmd.do("_ rewind"))
      btn_back = self.buttonAdd(row1,'<',lambda : cmd.do("_ backward"))
      btn_stop = self.buttonAdd(row1,'Stop',lambda : cmd.do("_ mstop"))
      btn_play = self.buttonAdd(row1,'Play',lambda : cmd.do("_ mplay"))
      btn_forward = self.buttonAdd(row1,'>',lambda : cmd.do("_ forward"))
      btn_last = self.buttonAdd(row1,'>|',lambda : cmd.do("_ ending"))
      btn_ccache = self.buttonAdd(row1,'MClear',lambda : cmd.do("_ mclear"))

   def my_show(self,win,center=1):
      if sys.platform!='linux2':
         win.show()
      else: # autocenter, deiconify, and run mainloop
         # this is a workaround for a bug in the
         # interaction between Tcl/Tk and common Linux
         # window managers (namely KDE/Gnome) which causes
         # an annoying 1-2 second delay in opening windows!
         if center:
            tw = win.winfo_reqwidth()+100
            th = win.winfo_reqheight()+100
            vw = win.winfo_vrootwidth()
            vh = win.winfo_vrootheight()
            x = max(0,(vw-tw)/2)
            y = max(0,(vh-tw)/2)
            win.geometry(newGeometry="+%d+%d"%(x,y))
         win.deiconify()
#         win.show()
         
   def my_withdraw(self,win):
      if sys.platform!='linux2':
         win.withdraw()
      else: # autocenter, deiconify, and run mainloop
         win.destroy()

   def my_activate(self,win,center=1,focus=None):
      if sys.platform!='linux2':
         win.activate()
      else: # autocenter, deiconify, and run mainloop
         # this is a workaround for a bug in the
         # interaction between Tcl/Tk and common Linux
         # window managers (namely KDE/Gnome) which causes
         # an annoying 1-2 second delay in opening windows!
         if center:
            tw = win.winfo_reqwidth()+100
            th = win.winfo_reqheight()+100
            vw = win.winfo_vrootwidth()
            vh = win.winfo_vrootheight()
            x = max(0,(vw-tw)/2)
            y = max(0,(vh-tw)/2)
            win.geometry(newGeometry="+%d+%d"%(x,y))
         win.deiconify()
         if focus!=None:
            focus.focus_set()
         win.mainloop()
         
   def my_deactivate(self,win):
      if sys.platform!='linux2':
         win.deactivate()
      else: # autocenter, deiconify, and run mainloop
         win.destroy()
      
   def createMain(self):
      self.command = StringVar()
      self.entry = self.createcomponent('entry', (), None,
                           Entry,
                           (self.get_dataArea(),),
                           justify=LEFT,
                           width=50,
                           textvariable=self.command)
      self.entry.pack(side=BOTTOM,expand=NO,fill=X)
      self.entry.bind('<Return>',lambda event,w=self.command:
         (cmd.do(w.get()),cmd.dirty(),w.set('')))

      self.output = self.createcomponent('output', (), None,
                           Pmw.ScrolledText,
                           (self.get_dataArea(),))

      text = self.output.component('text')
      if sys.platform=='linux2':
         self.my_fw_font=('lucida console',10)
      elif sys.platform[:3]=='win':
         self.my_fw_font=('lucida console',8) # Courier 9
      else:
         self.my_fw_font=('lucida console',10)
         
      text.configure(font = self.my_fw_font)
      text.configure(width=72)
      self.output.after(1000,self.flush_commands)
      self.output.after(1000,self.update_feedback)
      self.output.after(1000,self.update_menus)
      self.output.pack(side=BOTTOM,expand=YES,fill=BOTH)
      self.bind(self.entry, 'Command Input Area')
      self.initialdir = os.getcwd()
      self.log_file = "log.pml"

   def flush_commands(self):
      # flush the external GUI fifo command queue
      while not self.fifo.empty():
         try:
            cmmd = self.fifo.get(0)
            exec cmmd
         except:
            traceback.print_exc()
      self.output.after(20,self.flush_commands) # 50X a second
      
   def update_feedback(self):
      for a in cmd.get_feedback():
         self.output.insert(END,"\n")
         self.output.insert(END,a)
         self.output.see(END)
         self.lineCount = self.lineCount + 1
         if self.lineCount > 10000:
            self.output.delete('0.0','%i.%i' % (self.lineCount-5000,0))
            self.lineCount=5000
      self.output.after(100,self.update_feedback) # 10X a second

   def update_menus(self):
      self.setting.refresh()
      self.output.after(500,self.update_menus) # twice a second
      
   def createInterface(self):
         AbstractApp.createInterface(self)
         self.createButtons()
         self.createMain()
         self.lineCount = 0
         raw_list = glob(os.environ['PYMOL_PATH']+"/modules/pmg_tk/startup/*.py*")
         unique = {}
         for a in raw_list:
            unique[re.sub(r".*\/|\.py.*$","",a)] = 1
         for name in unique.keys():
            if name != "__init__":
               mod_name = "pmg_tk.startup."+name
               __builtin__.__import__(mod_name)
               mod = sys.modules[mod_name]
               mod.__init__(self)

   def quit_app(self):
      cmd.log_close()
      cmd.quit()  # avoid logging this - it is inconvenient...

   def file_open(self):
      ofile = askopenfilename(initialdir = self.initialdir,
                              filetypes=[("All Readable","*.pdb"),
                                         ("All Readable","*.ccp4"),
                                         ("All Readable","*.xplor"),
                                         ("All Readable","*.mol"),                                         
                                         ("All Readable","*.sdf"),
                                         ("All Readable","*.xyz"),                                         
                                         ("All Readable","*.r3d"),
                                         ("All Readable","*.cc1"),
                                         ("All Readable","*.cc2"),                                         
                                         ("All Readable","*.ent"),
                                         ("All Readable","*.dat"),
                                         ("All Readable","*.out"),
                                         ("All Readable","*.mmd"),
                                         ("All Readable","*.mmod"),
                                         ("PDB File","*.pdb"),
                                         ("All Files","*.*"),
                                         ("All Files","*"),                                         
                                         ("CCP4 Map","*.ccp4"),                                         
                                         ("PDB File","*.ent"),
                                         ("Macromodel File","*.dat"),
                                         ("Macromodel File","*.out"),
                                         ("Macromodel File","*.mmd"),
                                         ("Macromodel File","*.mmod"),
                                         ("MOL File","*.mol"),
                                         ("ChemPy Model","*.pkl"),
                                         ("Raster3D Scene","*.r3d"),
                                         ("SDF File","*.sdf"),
                                         ("XPLOR Map","*.xplor"),
                                         ("ChemDraw3D File","*.cc1"),
                                         ("ChemDraw3D File","*.cc2"),
                                         ("Tinker XYZ File","*.xyz")
                                         ])
      if len(ofile):
         self.initialdir = re.sub(r"[^\/\\]*$","",ofile)         
         cmd.log("load %s\n"%ofile,"cmd.load('%s')\n"%ofile)
         cmd.load(ofile)

   def log_open(self):
      sfile = asksaveasfilename(initialfile = self.log_file,
                                initialdir = self.initialdir,
                                filetypes=[
                                           ("PyMOL Script","*.pml"),
                                           ("PyMOL Program","*.pym"),
                                           ("Python Program","*.py"),
                                           ("All Files","*.*"),
                                           ("All Files","*"),
                                           ])
      if len(sfile):
         self.initialdir = re.sub(r"[^\/\\]*$","",sfile)
         self.log_file = re.sub(r"^.*[^\/\\]","",sfile)
         cmd.log_open(sfile)

   def log_resume(self,append_only=0):
      ofile = askopenfilename(initialdir = os.getcwd(),
                   filetypes=[("All Resumable","*.pml"),
                              ("All Resumable","*.pym"),
                              ("All Resumable","*.py"),
                              ("PyMOL Script","*.pml"),
                              ("PyMOL Program","*.pym"),
                              ("Python Program","*.py"),
                              ("All Files","*.*"),                                           
                              ("All Files","*"),
                              ])
      if len(ofile):
         self.initialdir = re.sub(r"[^\/\\]*$","",ofile)
         self.log_file = re.sub(r"^.*[^\/\\]","",ofile)
         os.chdir(self.initialdir)	         
         cmd.resume(ofile)

   def log_append(self,append_only=0):
      ofile = askopenfilename(initialdir = os.getcwd(),
                   filetypes=[("All Appendable","*.pml"),
                              ("All Appendable","*.pym"),
                              ("All Appendable","*.py"),
                              ("PyMOL Script","*.pml"),
                              ("PyMOL Program","*.pym"),
                              ("Python Program","*.py"),
                              ("All Files","*.*"),                                           
                              ("All Files","*"),
                              ])
      if len(ofile):
         self.initialdir = re.sub(r"[^\/\\]*$","",ofile)
         self.log_file = re.sub(r"^.*[^\/\\]","",ofile)
         os.chdir(self.initialdir)	         
         cmd.log_open(ofile,'a')

   def file_save(self):
      lst = cmd.get_names('all')
      lst = filter(lambda x:x[0]!="_",lst)
      self.dialog = Pmw.SelectionDialog(self.root,title="Save",
                          buttons = ('OK', 'Cancel'),
                                   defaultbutton='OK',
                          scrolledlist_labelpos=N,
                          label_text='Which object or selection would you like to save?',
                          scrolledlist_items = lst,
                          command = self.file_save2)
      if len(lst):
         listbox = self.dialog.component('scrolledlist')      
         listbox.selection_set(0)
      self.my_show(self.dialog)
      
   def file_save2(self,result):
      if result!='OK':
         self.my_withdraw(self.dialog)
         del self.dialog
      else:
         sels = self.dialog.getcurselection()
         if len(sels)!=0:
            sfile = sels[0]+".pdb"
            self.my_withdraw(self.dialog)
            del self.dialog
            if result=='OK':
               sfile = asksaveasfilename(initialfile = sfile,
                                         initialdir = self.initialdir,
                                         filetypes=[
                                                    ("PDB File","*.pdb"),
                                                    ("MOL File","*.mol"),
                                                    ("MMD File","*.mmd"),
                                                    ("PKL File","*.pkl"),
                                                    ])
               if len(sfile):
                  self.initialdir = re.sub(r"[^\/\\]*$","",sfile)
                  cmd.log("save %s,(%s)\n"%(sfile,sels[0]),
                          "cmd.save('%s','(%s)')\n"%(sfile,sels[0]))
                  cmd.save(sfile,"(%s)"%sels[0])
         
   def file_run(self):
      ofile = askopenfilename(initialdir = os.getcwd(),
                   filetypes=[("All Runnable","*.pml"),
                              ("All Runnable","*.pym"),
                              ("All Runnable","*.py"),
                              ("All Runnable","*.pyc"),
                              ("PyMOL Script","*.pml"),
                              ("Python Program","*.py"),
                              ("Python Program","*.pyc"),
                              ("PyMOL Program","*.pym"),
                              ("All Files","*.*"),                                           
                              ("All Files","*"),
                              ])
      if len(ofile):
         dir = re.sub(r"[^\/\\]*$","",ofile)
         os.chdir(dir)	
         if re.search("\.pym*$|\.PYM*$",ofile):
            cmd.log("run %s\n"%ofile)                     
            cmd.do("run "+ofile);      
         else:
            cmd.log("@%s\n"%ofile)                                 
            cmd.do("@"+ofile);

   def file_savepng(self):
      sfile = asksaveasfilename(initialdir = self.initialdir,
             filetypes=[("PNG File","*.png")])
      if len(sfile):
         self.initialdir = re.sub(r"[^\/\\]*$","",sfile)
         cmd.log("png %s\n"%sfile,"cmd.png('%s')\n"%sfile)
         cmd.png(sfile)
         
      
   def file_savemovie(self):
      sfile = asksaveasfilename(filetypes=[("Numbered PNG Files","*.png")])
      if len(sfile):
         self.initialdir = re.sub(r"[^\/\\]*$","",sfile)
         cmd.log("mpng %s\n"%sfile,"cmd.mpng('%s')\n"%sfile)         
         cmd.mpng(sfile)

   def demo1(self):
      cmd.disable()
      cmd.do("cd $PYMOL_PATH")
      cmd.delete("pept")
      cmd.delete("pept_dist")
      cmd.load("test/dat/pept.pdb")
      cmd.show("sticks","(pept and not i;5:7)")
      cmd.show("surface","(pept and i;5,6)")
      cmd.show("mesh","(pept and i;1,11,12,13)")
      cmd.show("spheres","(pept and i;2,12,9,4 and not n;c,n,o,ca)")
      cmd.show("dots","(i;8)")
      cmd.dist("pept_dist","(i;1&n;OD2)","(i;13&n;OG1)")
      cmd.set("dot_width","2");

   def demo2(self):
      cmd.disable()
      cmd.do("cd $PYMOL_PATH")
      cmd.delete("cgo1")
      cmd.delete("cgo2")
      cmd.do("cd $PYMOL_PATH")
      cmd.load("test/dat/pept.r3d","cgo1")
      cmd.load("test/dat/3al1.r3d","cgo2")
      cmd.zoom()

   def demo3(self):
      cmd.disable()
      cmd.do("cd $PYMOL_PATH")
      cmd.do("run examples/devel/cgo03.py")

   def demo4(self):
      cmd.disable()
      cmd.delete("arg")
      cmd.fragment("arg")
      cmd.zoom("arg",2)
      cmd.show("sticks","arg")
      cmd.feedback('dis','sel','res')
      for a in xrange(1,181):
         cmd.set("suspend_updates",1,quiet=1)
         cmd.edit("(arg and n;cd)","(arg and n;cg)")
         cmd.torsion("6")
         cmd.unpick()
         cmd.edit("(arg and n;cb)","(arg and n;ca)")
         cmd.torsion("2")
         cmd.unpick()
         cmd.set("suspend_updates",0,quiet=1)         
         cmd.refresh()
      cmd.feedback('ena','sel','res')

   def demo5(self):
      cmd.set("suspend_updates",1,quiet=1)
      cmd.disable()
      cmd.delete("1tii")      
      cmd.load("$PYMOL_PATH/test/dat/1tii.pdb")
      cmd.hide("(1tii)")
      cmd.show("cartoon","1tii")
      cmd.zoom("1tii")
      util.color_chains("1tii")
      cmd.set("suspend_updates",0,quiet=1)
      cmd.refresh()

   def demo6(self):
      cmd.set("suspend_updates",1,quiet=1)
      cmd.disable()
      cmd.delete("trans")
      cmd.load("$PYMOL_PATH/test/dat/pept.pdb","trans")
      cmd.hide("(tran)")
      cmd.show("surface","trans")
      cmd.show("sticks","trans")
      cmd.set("surface_color","white","trans")
      cmd.set("transparency",0.5,"trans")
      cmd.zoom("trans")
      cmd.set("suspend_updates",0,quiet=1)
      cmd.refresh()

   def demo7(self):
      cmd.set("suspend_updates",1,quiet=1)
      cmd.disable()
      cmd.delete("ray")
      cmd.load("$PYMOL_PATH/test/dat/il2.pdb","ray")
      cmd.remove("(ray and hydro)")
      cmd.hide("lines","ray")
      cmd.show("spheres","ray")
      cmd.orient("ray")
      cmd.turn("x",90)
      util.ray_shadows('heavy')
      cmd.set("suspend_updates",0,quiet=1)
      cmd.refresh()
      cmd.do("ray")
      
   def hide_sele(self):
      cmd.log("util.hide_sele()\n","util.hide_sele()\n")
      util.hide_sele()

   
   def createMenuBar(self):
      self.menuBar.addmenuitem('Help', 'command',
                               'Get information on application', 
                               label='About', command = lambda : cmd.do("_ splash"))

      self.menuBar.addmenuitem('Help', 'command', 'Release Notes',
                               label='Release Notes',
                               command = lambda: cmd.do("_ cmd.show_help('release')"))

      self.menuBar.addmenuitem('Help', 'separator', '')
      

      self.menuBar.addmenuitem('Help', 'command', 'Help on Commands',
                               label='Commands',
                               command = lambda: cmd.do("_ cmd.show_help('commands')"))

      self.menuBar.addmenuitem('Help', 'command', 'Help on Launching',
                               label='Launching',
                               command = lambda: cmd.do("_ cmd.show_help('launching')"))      

      self.menuBar.addmenuitem('Help', 'separator', '')

      self.menuBar.addmenuitem('Help', 'command', 'Help on Selections',
                               label='Select Command',
                               command = lambda: cmd.do("_ cmd.show_help('select')"))      

      self.menuBar.addmenuitem('Help', 'command', 'Help on Selections',
                               label='Selection Syntax',
                               command = lambda: cmd.do("_ cmd.show_help('selections')"))      

      self.menuBar.addmenuitem('Help', 'command', 'Example Selections',
                               label='Selection Examples',
                               command = lambda: cmd.do("_ cmd.show_help('examples')"))      

      self.menuBar.addmenuitem('Help', 'separator', '')
      

      self.menuBar.addmenuitem('Help', 'command', 'Help on the Mouse',
                               label='Mouse',
                               command = lambda: cmd.do("_ cmd.show_help('mouse')"))      

      self.menuBar.addmenuitem('Help', 'command', 'Help on the Keyboard',
                               label='Keyboard',
                               command = lambda: cmd.do("_ cmd.show_help('keyboard')"))      

      self.menuBar.addmenuitem('Help', 'command', 'Help on Molecular Editing',
                               label='Molecular Editing',
                               command = lambda: cmd.do("_ cmd.show_help('editing')"))      

      self.menuBar.addmenuitem('Help', 'command', 'Help on Molecular Editing',
                               label='Molecular Editing Keys',
                               command = lambda: cmd.do("_ cmd.show_help('edit_keys')"))      

      self.menuBar.addmenuitem('Help', 'command', 'Help on Stereo',
                               label='Stereo',
                               command = lambda: cmd.do("_ cmd.show_help('stereo')"))      

      self.menuBar.addmenuitem('Help', 'separator', '')
      

      self.menuBar.addmenuitem('Help', 'command', 'Help on the API',
                               label='API',
                               command = lambda: cmd.do("_ cmd.show_help('api')"))      

      self.toggleBalloonVar = IntVar()
      self.toggleBalloonVar.set(1)
      self.setting = Setting()

      self.menuBar.addmenuitem('Help', 'separator', '')
      
      self.menuBar.addmenuitem('Help', 'checkbutton',
                         'Toggle balloon help',
                         label='Balloon help',
                        variable = self.toggleBalloonVar,
                        command=self.toggleBalloon)

      self.menuBar.addmenuitem('File', 'command', 'Open structure file.',
                        label=self.pad+'Open...',
                        command=self.file_open)

      self.menuBar.addmenuitem('File', 'command', 'Save structure file.',
                        label=self.pad+'Save Molecule...',
                        command=self.file_save)

#      self.menuBar.addmenuitem('File', 'command', 'Open sequential files.',
#                        label=self.pad+'Open Sequence...',
#                        command=self.file_open)

      self.menuBar.addmenuitem('File', 'command', 'Save current image.',
                        label=self.pad+'Save Image...',
                        command=self.file_savepng)

      self.menuBar.addmenuitem('File', 'command', 'Save all frames.',
                        label=self.pad+'Save Movie...',
                        command=self.file_savemovie)

      self.menuBar.addmenuitem('File', 'separator', '')
      
      self.menuBar.addmenuitem('File', 'command', 'Open log file.',
                        label=self.pad+'Log...',
                        command=self.log_open)

      self.menuBar.addmenuitem('File', 'command', 'Resume log file.',
                        label=self.pad+'Resume...',
                        command=self.log_resume)

      self.menuBar.addmenuitem('File', 'command', 'Append log file.',
                        label=self.pad+'Append...',
                        command=self.log_append)

      self.menuBar.addmenuitem('File', 'command', 'Close log file.',
                        label=self.pad+'Close Log',
                        command=cmd.log_close)

      self.menuBar.addmenuitem('File', 'command', 'Run program or script.',
                        label=self.pad+'Run...',
                        command=self.file_run)


      self.menuBar.addmenuitem('File', 'separator', '')

      self.menuBar.addmenuitem('File', 'command', 'Quit PyMOL',
                        label=self.pad+'Quit',
                        command=self.quit)

      self.menuBar.addmenuitem('File', 'separator', '')
      
      self.menuBar.addmenuitem('File', 'checkbutton',
                         'Log Conformations.',
                         label=self.pad+'Log Conformations',
                        variable = self.setting.log_conformations,
                        command = lambda s=self: s.setting.update('log_conformations'))

      self.menuBar.addmenuitem('File', 'checkbutton',
                         'Log Box Selections.',
                         label=self.pad+'Log Box Selections',
                        variable = self.setting.log_box_selections,
                        command = lambda s=self: s.setting.update('log_box_selections'))

      self.menuBar.addmenuitem('Edit', 'command',
                         'To Copy: Use Ctrl-C',
                         label='To copy text use Ctrl-C',
                               state='disabled',
                        command =  None)

      self.menuBar.addmenuitem('Edit', 'command',
                         'To Paste, Use Ctrl-V',
                         label='To paste text use Ctrl-V',
                               state='disabled',                               
                        command =  None)


      self.menuBar.addmenuitem('Edit', 'command',
                         'Test',
                         label='Test',
                        command =  lambda s=self: s.test())

      self.menuBar.addmenu('Movies', 'Movie Control')

      self.menuBar.addmenuitem('Movies', 'checkbutton',
                         'Photorealistic images.',
                         label=self.pad+'Ray Trace Frames',
                        variable = self.setting.ray_trace_frames,
                        command = lambda s=self: s.setting.update('ray_trace_frames'))

      self.menuBar.addmenuitem('Movies', 'checkbutton',
                         'Save images in memory.',
                         label=self.pad+'Cache Frames',
                        variable = self.setting.cache_frames,
                        command = lambda s=self: s.setting.update('cache_frames'))

      self.menuBar.addmenuitem('Movies', 'command', 'Flush Image Cache',
                               label=self.pad+'Flush Image Cache',
                               command = lambda: cmd.mclear())

      self.menuBar.addmenuitem('Movies', 'separator', '')

      self.menuBar.addmenuitem('Movies', 'checkbutton',
                         'Static Singleton Objects.',
                         label=self.pad+'Static Singleton Objects',
                        variable = self.setting.static_singletons,
                        command = lambda s=self: s.setting.update('static_singletons'))

      self.menuBar.addmenuitem('Movies', 'checkbutton',
                         'Superimpose all molecular states.',
                         label=self.pad+'Show All States',
                        variable = self.setting.all_states,
                        command = lambda s=self: s.setting.update('all_states'))

      self.menuBar.addmenuitem('Movies', 'separator', '')
      
      self.menuBar.addmenuitem('Movies', 'command', 'Maximum Speed',
                               label=self.pad+'Maximum Speed',
                               command = lambda: cmd.set("movie_delay","0",log=1))

      self.menuBar.addmenuitem('Movies', 'command', '30 FPS',
                               label=self.pad+'30 FPS',
                               command = lambda: cmd.set("movie_delay","33",log=1))

      self.menuBar.addmenuitem('Movies', 'command', '15 FPS',
                               label=self.pad+'15 FPS',
                               command = lambda: cmd.set("movie_delay","66",log=1))

      self.menuBar.addmenuitem('Movies', 'command', '5 FPS',
                               label=self.pad+'5 FPS',
                               command = lambda: cmd.set("movie_delay","200",log=1))

      self.menuBar.addmenuitem('Movies', 'command', '1 FPS',
                               label=self.pad+'1 FPS',
                               command = lambda: cmd.set("movie_delay","1000",log=1))

      self.menuBar.addmenuitem('Movies', 'command', '0.3 FPS',
                               label=self.pad+'0.3 FPS',
                               command = lambda: cmd.set("movie_delay","3000",log=1))

      self.menuBar.addmenuitem('Movies', 'separator', '')

      self.menuBar.addmenuitem('Movies', 'command', 'Reset Meter',
                               label=self.pad+'Reset Meter',
                               command = lambda: cmd.do("_ meter_reset"))

      self.menuBar.addmenu('Display', 'Display Control')


      self.menuBar.addmenuitem('Display', 'command', 'Clear Text Output',
                               label='Clear Text',
                               command = lambda: cmd.do("_ cls"))

      self.menuBar.addmenuitem('Display', 'command', 'Hide Text Output',
                               label='Hide Text',
                               command = lambda: cmd.set("text","0",log=1))

      self.menuBar.addmenuitem('Display', 'command', 'Show Text Output',
                               label='Show Text',
                               command = lambda: cmd.set("text","1",log=1))

      self.menuBar.addmenuitem('Display', 'separator', '')
      
      self.menuBar.addmenuitem('Display', 'command', 'Stereo On',
                               label='Stereo On',
                               command = lambda: cmd.do("_ stereo on"))

      self.menuBar.addmenuitem('Display', 'command', 'Stereo Off',
                               label='Stereo Off',
                               command = lambda: cmd.do("_ stereo off"))

      self.menuBar.addmenuitem('Display', 'separator', '')

      self.menuBar.addmenuitem('Display', 'command', 'Maximum Performance',
                               label='Maximum Performance',
                               command = lambda : cmd.do("_ util.performance(100)"))

      self.menuBar.addmenuitem('Display', 'command', 'Reasonable Performance',
                               label='Reasonable Performance',
                               command = lambda : cmd.do("_ util.performance(66)"))
      
      self.menuBar.addmenuitem('Display', 'command', 'Reasonable Quality',
                               label='Reasonable Quality',
                               command = lambda : cmd.do("_ util.performance(33)"))

      self.menuBar.addmenuitem('Display', 'command', 'Maximum Quality',
                               label='Maximum Quality',
                               command = lambda : cmd.do("_ util.performance(0)"))

      self.menuBar.addmenuitem('Display', 'separator', '')

      self.menuBar.addmenuitem('Display', 'command', 'Light Shadows',
                               label='Light Shadows',
                               command = lambda : cmd.do("_ util.ray_shadows('light')"))

      self.menuBar.addmenuitem('Display', 'command', 'Matte Shadows',
                               label='Matte Shadows',
                               command = lambda : cmd.do("_ util.ray_shadows('matte')"))

      self.menuBar.addmenuitem('Display', 'command', 'Medium Shadows',
                               label='Medium Shadows',
                               command = lambda : cmd.do("_ util.ray_shadows('medium')"))

      self.menuBar.addmenuitem('Display', 'command', 'Heavy Shadows',
                               label='Heavy Shadows',
                               command = lambda : cmd.do("_ util.ray_shadows('heavy')"))

      self.menuBar.addmenuitem('Display', 'command', 'Black Shadows',
                               label='Black Shadows',
                               command = lambda : cmd.do("_ util.ray_shadows('black')"))

      self.menuBar.addmenu('Settings', 'Configuration Control')

      self.menuBar.addmenuitem('Settings', 'command',
                         'Edit PyMOL Settings',
                         label=self.pad+'Edit All...',
                               command = lambda s=self: SetEditor(s))

      self.menuBar.addmenuitem('Settings', 'command',
                         'Edit PyMOL Colors',
                         label=self.pad+'Colors...',
                               command = lambda s=self: ColorEditor(s))

      self.menuBar.addmenuitem('Settings', 'separator', '')
      
      self.menuBar.addmenuitem('Settings', 'checkbutton',
                         'Show Valences.',
                         label=self.pad+'Show Valences',
                        variable = self.setting.valence,
                        command = lambda s=self: s.setting.update('valence'))

      self.menuBar.addmenuitem('Settings', 'checkbutton',
                         'Disable perspective.',
                         label=self.pad+'Orthoscopic View',
                        variable = self.setting.ortho,
                        command = lambda s=self: s.setting.update('ortho'))

      self.menuBar.addmenuitem('Settings', 'checkbutton',
                         'Smooth Lines.',
                         label=self.pad+'Smooth Lines',
                        variable = self.setting.line_smooth,
                        command = lambda s=self: s.setting.update('line_smooth'))

      self.menuBar.addmenuitem('Settings', 'checkbutton',
                         'Depth Cue Fog.',
                         label=self.pad+'Depth Cue & Ray Trace Fog',
                        variable = self.setting.depth_cue,
                        command = lambda s=self: s.setting.update('depth_cue'))

      self.menuBar.addmenuitem('Settings', 'checkbutton',
                         'Two Sided Lighting.',
                         label=self.pad+'Two Sided Lighting',
                        variable = self.setting.two_sided_lighting,
                        command = lambda s=self: s.setting.update('two_sided_lighting'))

      self.menuBar.addmenuitem('Settings', 'checkbutton',
                         'Specular Reflections.',
                         label=self.pad+'Specular Reflections',
                        variable = self.setting.specular,
                        command = lambda s=self: s.setting.update('specular'))

      self.menuBar.addmenuitem('Settings', 'checkbutton',
                         'Overlay',
                         label=self.pad+'Overlay Text on Graphics',
                        variable = self.setting.overlay,
                        command = lambda s=self: s.setting.update('overlay'))

      self.menuBar.addmenuitem('Settings', 'separator', '')
      
      self.menuBar.addmenuitem('Settings', 'checkbutton',
                         'Smooth raytracing.',
                         label=self.pad+'Antialiased Rendering',
                        variable = self.setting.antialias,
                        command = lambda s=self: s.setting.update('antialias'))

      self.menuBar.addmenuitem('Settings', 'checkbutton',
                         'Cull Backfaces when Rendering',
                         label=self.pad+'Cull Backfaces when Rendering',
                        variable = self.setting.backface_cull,
                        command = lambda s=self: s.setting.update('backface_cull'))

      self.menuBar.addmenuitem('Settings', 'separator', '')

      self.menuBar.addmenuitem('Settings', 'checkbutton',
                               'Ignore PDB segi.',
                               label=self.pad+'Ignore PDB Segment Identifier',
                               variable = self.setting.ignore_pdb_segi,
                               command = lambda s=self: s.setting.update('ignore_pdb_segi'))

      self.menuBar.addmenuitem('Settings', 'checkbutton',
                         'Auto-Zoom.',
                         label=self.pad+'Auto-Zoom New Objects',
                        variable = self.setting.auto_zoom,
                        command = lambda s=self: s.setting.update('auto_zoom'))

      self.menuBar.addmenuitem('Settings', 'checkbutton',
                         'Auto-Show Selections.',
                         label=self.pad+'Auto-Show New Selections',
                        variable = self.setting.auto_show_selections,
                        command = lambda s=self: s.setting.update('auto_show_selections'))

      self.menuBar.addmenuitem('Settings', 'checkbutton',
                         'Auto-Hide Selections.',
                         label=self.pad+'Auto-Hide Selections',
                        variable = self.setting.auto_hide_selections,
                        command = lambda s=self: s.setting.update('auto_hide_selections'))

      
      self.menuBar.addmenu('Mouse', 'Mouse Configuration')

      self.menuBar.addmenuitem('Mouse', 'command', 'Visualization',
                               label='Visualization',
                               command = lambda: cmd.edit_mode("off"))

      self.menuBar.addmenuitem('Mouse', 'command', 'Editing',
                               label='Editing',
                               command = lambda: cmd.edit_mode("on"))

      self.menuBar.addmenu('Cartoons', 'Cartoon Properties')

      self.menuBar.addmenuitem('Cartoons', 'checkbutton',
                         'Round Helices',
                         label=self.pad+'Round Helices',
                        variable = self.setting.cartoon_round_helices,
                        command = lambda s=self: s.setting.update('cartoon_round_helices'))

      self.menuBar.addmenuitem('Cartoons', 'checkbutton',
                         'Fancy Helices',
                         label=self.pad+'Fancy Helices',
                        variable = self.setting.cartoon_fancy_helices,
                        command = lambda s=self: s.setting.update('cartoon_fancy_helices'))


      self.menuBar.addmenuitem('Cartoons', 'checkbutton',
                         'Flat Sheets',
                         label=self.pad+'Flat Sheets',
                        variable = self.setting.cartoon_flat_sheets,
                        command = lambda s=self: s.setting.update('cartoon_flat_sheets'))


      self.menuBar.addmenuitem('Cartoons', 'checkbutton',
                         'Fancy Sheets',
                         label=self.pad+'Fancy Sheets',
                        variable = self.setting.cartoon_fancy_sheets,
                        command = lambda s=self: s.setting.update('cartoon_fancy_sheets'))

      self.menuBar.addmenuitem('Cartoons', 'checkbutton',
                         'Smooth Loops',
                         label=self.pad+'Smooth Loops',
                        variable = self.setting.cartoon_smooth_loops,
                        command = lambda s=self: s.setting.update('cartoon_smooth_loops'))

      self.menuBar.addmenuitem('Cartoons', 'checkbutton',
                         'Discrete Colors',
                         label=self.pad+'Discrete Colors',
                        variable = self.setting.cartoon_discrete_colors,
                        command = lambda s=self: s.setting.update('cartoon_discrete_colors'))


      self.menuBar.addmenu('Wizards', 'Task Wizards')
      
      self.menuBar.addmenuitem('Wizards', 'command', 'Density Map Wizard',
                               label='Density',
                               command = lambda: cmd.do("wizard density"))

      self.menuBar.addmenuitem('Wizards', 'command', 'Distance',
                               label='Distance',
                               command = lambda: cmd.do("_ wizard distance"))

      self.menuBar.addmenuitem('Wizards', 'command', 'Mutagenesis',
                               label='Mutagenesis',
                               command = lambda: cmd.do("_ wizard mutagenesis"))

      self.menuBar.addmenuitem('Wizards', 'command', 'Pair Fitting',
                               label='Pair Fitting',
                               command = lambda: cmd.do("_ wizard pair_fit"))

      self.menuBar.addmenuitem('Wizards', 'command', 'Label',
                               label='Label',
                               command = lambda: cmd.do("_ wizard label"))

      self.menuBar.addmenuitem('Wizards', 'command', 'Charge',
                               label='Charge',
                               command = lambda: cmd.do("_ wizard charge"))


      self.menuBar.addmenu('Demos', 'Demonstrations')

      self.menuBar.addmenuitem('Demos', 'command', 'Representations',
                               label='Representations',
                               command = self.demo1)

      self.menuBar.addmenuitem('Demos', 'command', 'Cartoon Ribbons',
                               label='Cartoon Ribbons',
                               command = self.demo5)

      self.menuBar.addmenuitem('Demos', 'command', 'Transparency',
                               label='Transparency',
                               command = self.demo6)

      self.menuBar.addmenuitem('Demos', 'command', 'Ray Tracing',
                               label='Ray Tracing',
                               command = self.demo7)

      self.menuBar.addmenuitem('Demos', 'command', 'Scripted Animation',
                               label='Scripted Animation',
                               command = self.demo4)

      self.menuBar.addmenuitem('Demos', 'command', 'Molscript/Raster3D Input',
                               label='Molscript/Raster3D Input',
                               command = self.demo2)

      self.menuBar.addmenuitem('Demos', 'command', 'Compiled Graphics Objects',
                               label='Compiled Graphics Objects',
                               command = self.demo3)






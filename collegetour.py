"""Jason Wong

collegetour.py is a program that allows a user to calculate the shortest path
through a given number of places specified by Facebook IDs and generate a map.
"""

import json
import itertools
import math
import random
import sys
import tkFileDialog
from Tkinter import *
from urllib import urlopen

def calcdist(coords1=[0.0,0.0], coords2=[0.0,0.0]):
    """Calculate the distance between two coordinates.

    Keyword arguments:
    coords1 -- first coordinate (default [0.0,0.0])
    coords2 -- second coordinate (default [0.0,0.0])

    """
    ctr = 2*math.pi/360 # conversion factor for deg to rad
    y1 = (90-float(coords1[0]))*ctr
    t1 = float(coords1[1])*ctr
    y2 = (90-float(coords2[0]))*ctr
    t2 = float(coords2[1])*ctr
    return (math.acos(math.sin(y1)*math.sin(y2)*math.cos(t1-t2)+math.cos(y1)*
            math.cos(y2))*3960)

class Application(Frame):
    """GUI class"""
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()
        self.padding = 10
        self.radius = 5
        self.sidelength = 300
        self.textlength = 75
        # load the file from the appropriate place
        try:
            file = sys.argv[1]
            self.getFile(open(file))
        except IndexError:
            self.getFile(tkFileDialog.askopenfile())
        
    def createWidgets(self):
        """Create the GUI elements"""
        
        # Frames
        self.input_frame = Frame(self)
        self.tour_frame = Frame(self)
        self.map_frame = Frame(self)
        self.top_frame = Frame(self.input_frame)
        self.bot_frame = Frame(self.input_frame)
        self.coord_frame = Frame(self.top_frame)
        self.picker_frame = Frame(self.bot_frame)
        
        # Input
        self.label_lat = Label(self.coord_frame, text='Starting location: (')
        self.label_lat.pack(side='left')
        self.entry_lat = Entry(self.coord_frame, width=8, relief=GROOVE)
        self.entry_lat.pack(side='left')
        self.label_comma = Label(self.coord_frame, text=', ')
        self.label_comma.pack(side='left')
        self.entry_long = Entry(self.coord_frame, width=8, relief=GROOVE)
        self.entry_long.pack(side='left')
        self.label_endparen = Label(self.coord_frame, text=')')
        self.label_endparen.pack(side='left')
        self.coord_frame.pack(side='top')
        self.button_calc = Button(self.top_frame,
                                text='Calculate',
                                command=self.calculate)
        self.button_calc.pack(side='left')
        self.button_quit = Button(self.top_frame, text='Quit',
                                  command=lambda:sys.exit())
        self.button_quit.pack(side='left')
        self.distance_var = StringVar()
        self.distance_var.set('Distance: 0')
        self.label_dist = Label(self.top_frame,
                            textvariable=self.distance_var, relief=GROOVE)
        self.label_dist.pack(side='right')
        
        self.list_pick = Listbox(self.picker_frame, selectmode=EXTENDED,
                                 width=35, height=15, relief=GROOVE)
        self.list_pick.pack()
        
        # Tour
        self.tour_var = StringVar()
        self.label_result = Label(self.tour_frame, width=35, height=19,
                                  textvariable=self.tour_var,
                                  relief=GROOVE, anchor=NW, justify=LEFT)
        self.label_result.pack()
        
        # Map
        self.canvas = Canvas(self.map_frame, width=300, height=300)
        self.canvas.pack()
        
        # Pack
        self.top_frame.pack()
        self.bot_frame.pack()
        self.picker_frame.pack()
        
        self.input_frame.pack(side='left')
        self.tour_frame.pack(side='left')
        self.map_frame.pack(side='left')

    def getFile(self, f):
        """Load in College IDs
        
        Keyword arguments:
        f -- reference to file to load from
        """
        ids = f.read()
        f.close()
        collegeids = ids.split('\n')
        self.locations = []
        for i in collegeids:
            if len(i) > 0:
                f = urlopen('http://graph.facebook.com/'+i)
                d = json.load(f)
                lat = float(d['location']['latitude'])
                long = float(d['location']['longitude'])
                self.locations.append((d['name'],(lat, long)))
        self.locations.sort()
        for i in self.locations:
            self.list_pick.insert(END, i[0])
        
    def calculate(self):
        """Calculate the shortest tour and display a graphical map"""
        mindist = -1
        minlist = []
        distances = []
        selectedcolleges = []
        graphcoords = []
        minx = -1
        miny = -1
        maxx = -1
        maxy = -1
        prevx = -1
        prevy = -1
        for i in self.list_pick.curselection():
            selectedcolleges.append(self.locations[int(i)])
        currentindex = -1
        permutations = itertools.permutations(selectedcolleges)
        for i in permutations:
            currentindex += 1
            # add starting location to beginning and end of tour
            i = ([('Start',(self.entry_lat.get(), self.entry_long.get()))] +
                 list(i) + [('Start',(self.entry_lat.get(),
                                      self.entry_long.get()))])
            currentdist = 0
            currentdists = []
            for j in range(len(i)-1):
                dist = calcdist(i[j][1],i[j+1][1])
                currentdist += dist
                currentdists.append(dist)
            if mindist == -1 or currentdist < mindist:
                mindist = currentdist
                minlist = i
                distances = currentdists
        self.tour_var.set("")
        j = 0
        print minlist
        for i in minlist:
            line = i[0]
            if j < len(distances):
                line += "\n  |-  %.1f miles" % distances[j]
            line += "\n"
            self.tour_var.set(self.tour_var.get() + line)
            j += 1
            latitude = float(i[1][0])+90
            longitude = float(i[1][1])+90
            graphcoords.append((longitude,latitude))
            if minx == -1 or longitude < minx:
                minx = longitude
            if miny == -1 or latitude < miny:
                miny = latitude
            if maxx == -1 or longitude > maxx:
                maxx = longitude
            if maxy == -1 or latitude > maxy:
                maxy = latitude
        # clear canvas
        for i in self.canvas.find_all():
            self.canvas.delete(i)
            
        # convert geographic coordinates to cartesian coordinates and draw map
        # pseudocode: (steps 1-3 were done in the minlist foreach loop)
        # 1 swap the tuple values to convert from latitude/longitude to x/y
        # 2 add 90 to guarantee all values are >= 0
        # 3 get the smallest x's and y's
        # 4 subtract the smallest x value from all the x values, repeat for y
        #   values. this moves the coordinates so they start from the NW corner
        # 5 scale the coordinates so the elements fill the canvas by multiply-
        #   ing the coordinates by the scale factor from the axis that needs
        #   less scaling before its elements go off the canvas. allowance is
        #   given for longer names, so shorter names (like 'Start') will pro-
        #   duce a small amount of unused canvas space
        # 6 draw the elements
        xscale = (self.sidelength - self.padding*2 - self.textlength) / (maxx -
                                                                         minx)
        yscale = (self.sidelength - self.padding*3) / (maxy - miny)
        scale = -1
        if xscale > yscale:
            scale = yscale
        else:
            scale = xscale
        j = 0
        for i in graphcoords:
            x = i[0]
            y = i[1]
            x = (x - minx) * scale
            y = (y - miny) * scale
            randcol = genRandCol()
            self.canvas.create_oval(x+self.padding-self.radius,
                                    y+self.padding-self.radius,
                                    x+self.padding+self.radius,
                                    y+self.padding+self.radius,
                                    outline=randcol, fill=randcol)
            self.canvas.create_text(x+self.padding+self.radius*1.5,
                                    y+self.padding+self.radius*1.5,
                                    text=minlist[j][0], width=self.textlength,
                                    anchor=NW)
            if prevx != -1:
                self.canvas.create_line(x+self.padding, y+self.padding,
                                        prevx+self.padding, prevy+self.padding,
                                        arrow=LAST)
            prevx = x
            prevy = y
            j += 1
            
        self.distance_var.set('Total: %.1f miles' %mindist)
        
def genRandCol():
    """Fancy colors ^_^"""
    hex = range(10)
    hex.extend(['a', 'b', 'c', 'd', 'e', 'f'])
    col = "#"
    for i in range(3):
        col += str(hex[int(random.random()*len(hex))])
    return col
    
def main():
    app = Application()
    app.master.title("Traveling Student Calculator")
    app.mainloop()
    
if __name__ == "__main__":
    main()
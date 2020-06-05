import math
import serial
import serial.tools.list_ports
import time
import webbrowser
import cv2
from tkinter import *
from tkinter import messagebox
from zaber_motion import Units, Library, MotionLibException
from zaber_motion.ascii import Connection, AxisSettings
from PIL import Image, ImageTk
from pylablib.aux_libs.devices import Thorlabs

class MainGUI:
    canvas_x = 900
    canvas_y = 900
    scale_factor = canvas_x/300
    cap = cv2.VideoCapture(0)

    def __init__(self):
        self.window = Tk()
        self.window.title('Gantry Motion Control')
        self.connected_text = Label(self.window, text="Connecting...")
        self.connected_text.pack()
        self.check_connection()
        self.canvas_create()
        with Thorlabs.K10CR1(str(55142424)) as self.rotaryStage:
            self.rotaryStage.set_velocity_params(20, acceleration=None)
            with Connection.open_serial_port(self.zaberport) as connection:
                self.device_list = connection.detect_devices()
                self.connected_text.configure(text="Found {} devices".format(len(self.device_list)))

                if len(self.device_list) == 2:
                    pass
                elif len(self.device_list) == 1:
                    messagebox.showerror('Error', 'Only one stage controllers is connected.\nCheck the connection then reopen')
                    quit()
                else:
                    messagebox.showerror('Error',
                                         'More than 2 Zaber controllers are conntected. \nEnsure only two controllers are connected')
                    quit()

                self.xyController = self.device_list[0]
                self.zController = self.device_list[1]
                self.Xaxis = self.xyController.get_axis(1)
                self.Yaxis = self.xyController.get_axis(2)
                self.Zaxis = self.zController.get_axis(1)

                menu = Menu(self.window)
                self.window.config(menu=menu)
                filemenu = Menu(menu)
                menu.add_cascade(label='File', menu=filemenu)
                filemenu.add_command(label='Home', command=self.zaber_home)
                filemenu.add_command(label='Help', command=lambda: webbrowser.open('https://iastate.box.com/s/huwdeysldcoheqrfgy4wmlfk6vyvoyvu'))
                filemenu.add_command(label='Quit', command=quit)

                self.window.mainloop()

    def check_connection(self):
        '''
        Asks user to check if zaber products are connected to device
        '''
        if messagebox.askokcancel('Connect', 'Connect to Zaber products'):
            self.zaberport = self.find_com_ports()
            if self.zaberport is not None:
                self.connected_text.config(text="Found Zaber Devices...")
                self.connected_text.update_idletasks()
                return self.zaberport
            else:
                self.connected_text.config(text='No Zaber products are currently plugged in. Check the connection then reopen')
                self.connected_text.update_idletasks()
                time.sleep(10)
                quit()
        else:
            quit()

    def find_com_ports(self):
        '''
        find_com_ports(): Finds all the COM ports that are plugged into the computer
        and returns any that have the term 'serial' in them
        and returns any that have the term 'serial' in them
        '''
        self.port = serial.tools.list_ports.comports()
        for self.port, self.desc, self.hwid in sorted(self.port):
            print(self.port+','+self.desc)
            if "serial" in self.desc.lower() and "usb" in self.desc.lower():
                return self.port

    def zaber_home(self):
        '''
        home command for all stages
        '''
        self.xyController.all_axes.home()
        self.zController.all_axes.home()
        #self.rotaryStage.home(sync=True, force=True, timeout=None)

    def canvas_create(self):
        '''
        Creates canvas for users to select which points they want the stage to go to and allocates button clicks to functions
        '''
        self.color_fg = 'black'
        self.color_bg = 'white'
        self.old_x = None
        self.old_y = None
        self.penwidth = 1
        self.drawWidgets()
        self.c.bind('<ButtonPress-2>', self.squarePress)  # create square
        self.c.bind('<B2-Motion>', self.squareMotion)
        self.c.bind('<ButtonRelease-2>', self.squareRelease)
        self.c.bind('<Button-1>', self.point)  # create point or line

    def drawWidgets(self):
        self.controls = Frame(self.window, padx=5, pady=5)

        self.scan_speed = IntVar()
        self.scan_speed.set(50)
        Label(self.controls, text='XY Stage Velocity (mm/sec)').pack()
        self.scan_speed_select = OptionMenu(self.controls, self.scan_speed, 50, 100, 150, 200, 250, 300)
        self.scan_speed_select.pack()

        Label(self.controls, text='').pack()

        self.stepover_size = IntVar()
        self.stepover_size.set(100)
        Label(self.controls, text='Scan Stepover Value (um)').pack()
        self.stepover_size_select = OptionMenu(self.controls, self.stepover_size, 25, 50, 100, 150, 200, 250)
        self.stepover_size_select.pack()

        self.canvas_function = IntVar()
        self.canvas_function.set(1)

        Label(self.controls, text='\n\n').pack()
        self.buttonZUp = Button(self.controls, text='Z Up', width=15)
        self.buttonZUp.pack()
        self.buttonZUp.bind('<ButtonPress-1>', self.zStageUpStart)
        self.buttonZUp.bind('<ButtonRelease-1>', self.zStageUpEnd)

        Label(self.controls, text='').pack()
        self.buttonZDown = Button(self.controls, text='Z Down', width=15)
        self.buttonZDown.pack()
        self.buttonZDown.bind('<ButtonPress-1>', self.zStageDownStart)
        self.buttonZDown.bind('<ButtonRelease-1>', self.zStageDownEnd)

        Label(self.controls, text='').pack()
        self.zStageSpeed = IntVar()
        self.zStageSpeed.set(1000)
        Label(self.controls, text='Z Stage Velocity (um/sec)').pack()
        self.zStageSpeed_select = OptionMenu(self.controls, self.zStageSpeed, 500, 1000, 5000, 10000)
        self.zStageSpeed_select.pack()

        Label(self.controls, text='\n\n').pack()
        self.gratingAngle = IntVar()
        self.gratingAngle.set(0)
        Label(self.controls, text='Grating Angle').pack()
        self.gratingAngle_select = OptionMenu(self.controls, self.gratingAngle, 0, 20, 40, 60, 80)
        self.gratingAngle_select.pack()
        self.gratingAlign = Button(self.controls, text='Align Grating', width=15, command=self.rotateGrating)
        self.gratingAlign.pack()

        self.controls.pack(side=LEFT)

        self.c = Canvas(self.window, width=self.canvas_x, height=self.canvas_y, bg=self.color_bg, )
        self.c.pack()

        self.scanProgress = Label(self.window, text='', font=("Arial", 18), justify=RIGHT)
        self.scanProgress.pack(side=LEFT)
        self.ScanProgressPercent = Label(self.window, text='', font=("Arial", 18), justify=LEFT)
        self.ScanProgressPercent.pack()

        self.videoFeed()

    def point(self, e):
        '''
        Code that controls when a person uses the left click funciton of a mouse
        '''
        print ('Old points:',round(self.Xaxis.get_position(Units.LENGTH_MILLIMETRES),1),'',round(self.Yaxis.get_position(Units.LENGTH_MILLIMETRES),1))

        if self.old_x and self.old_y:
            self.c.create_line(self.old_x, self.old_y, e.x, e.y, width=self.penwidth, fill=self.color_fg,
                               capstyle=ROUND, smooth=True)
        print('New points:', e.x/self.scale_factor, ',', e.y/self.scale_factor)
        self.x_distance = ((e.x)/self.scale_factor) - int(round(self.Xaxis.get_position(Units.LENGTH_MILLIMETRES), 1))
        self.y_distance = ((e.y)/self.scale_factor) - int(round(self.Yaxis.get_position(Units.LENGTH_MILLIMETRES), 1))
        self.total_move_distance = math.sqrt(abs(self.x_distance)**2 + abs(self.y_distance)**2)

        self.x_velocity = (self.x_distance/self.total_move_distance) * self.scan_speed.get()
        self.y_velocity = (self.y_distance / self.total_move_distance) * self.scan_speed.get()

        print('X velocity:', int(round(self.x_velocity, 1)), '  Y velocity:', int(round(self.y_velocity, 1)))

        self.old_x = e.x
        self.old_y = e.y

        self.Xaxis.settings.set("maxspeed", abs(int(round(self.x_velocity, 4))), Units.VELOCITY_MILLIMETRES_PER_SECOND)
        self.Yaxis.settings.set("maxspeed", abs(int(round(self.y_velocity, 4))), Units.VELOCITY_MILLIMETRES_PER_SECOND)
        self.Xaxis.move_absolute(e.x / self.scale_factor, Units.LENGTH_MILLIMETRES, wait_until_idle=False)
        self.Yaxis.move_absolute(e.y / self.scale_factor, Units.LENGTH_MILLIMETRES,  wait_until_idle=False)

    def squarePress(self, e):
        '''
        Code that controls when a person clicks down on the middle mouse button
        '''
        self.initial_X = e.x
        self.initial_Y = e.y

    def squareMotion(self, e):
        '''
        Code that controls when a person clicks down on the middle mouse button
        '''
        self.c.delete(ALL)
        self.videoFeed()
        self.c.create_rectangle(self.initial_X, self.initial_Y, e.x, e.y, fill='black')

    def squareRelease(self, e):
        '''
        Code that controls when a person releases the middle mouse button
        '''
        if e.x >= self.canvas_x:      #error checking to make sure the final point is on the Canvas
            e.x = self.canvas_x
        elif e.x <= 0:
            e.x = 0
        if e.y >= self.canvas_y:
            e.y = self.canvas_y
        elif e.y <= 0:
            e.y = 0
        self.final_X = e.x
        self.final_Y = e.y
        self.c.delete(ALL)
        self.videoFeed()
        self.c.create_rectangle(self.initial_X, self.initial_Y, e.x, e.y, fill='black')
        print('Initial points', self.initial_X,',', self.initial_Y)
        print('Final points', self.final_X,',', self.final_Y)
        self.scanSquare()

    def scanSquare(self):
        '''
        takes points from the square created in squareRelease and controls Zaber stages until scan is complete
        :return:
        '''
        self.scanProgress.config(text='Scan Starting')
        self.scanProgress.update_idletasks()
        if self.final_X >= self.initial_X:
            self.start_X = self.initial_X
            self.end_X = self.final_X
        else:
            self.start_X = self.final_X
            self.end_X = self.initial_X
        if self.final_Y >= self.initial_Y:
            self.start_Y = self.initial_Y
            self.end_Y = self.final_Y
        else:
            self.start_Y = self.final_Y
            self.end_Y = self.initial_Y
        i = round(float(self.start_Y),5)
        self.Xaxis.settings.set("maxspeed", self.scan_speed.get(), Units.VELOCITY_MILLIMETRES_PER_SECOND)
        self.Yaxis.move_absolute(i / self.scale_factor, Units.LENGTH_MILLIMETRES, wait_until_idle=False) # move to starting Y
        self.Xaxis.move_absolute(self.start_X / self.scale_factor, Units.LENGTH_MILLIMETRES) # move to start X
        print('move to start')
        time.sleep(2)
        while i <= self.end_Y:
            self.Xaxis.move_absolute(self.end_X / self.scale_factor, Units.LENGTH_MILLIMETRES) # move to end X
            i += self.stepover_size.get()/1000
            print(round(i, 5))
            self.Yaxis.move_absolute(round(i, 5) / self.scale_factor, Units.LENGTH_MILLIMETRES, wait_until_idle=False) # stepover
            self.Xaxis.move_absolute(self.start_X / self.scale_factor, Units.LENGTH_MILLIMETRES)
            self.scanPrecentCompleteCalculation = round((((i-self.start_Y)/(self.end_Y-self.start_Y))*100), 1)
            self.scanProgress.config(text='Percent complete:')
            self.scanProgress.update_idletasks()
            self.ScanProgressPercent.config(text=self.scanPrecentCompleteCalculation)
        self.scanProgress.config(text='Scan Complete')
        self.ScanProgressPercent.config(text='')


    def zStageUpStart(self, e):
        self.Zaxis.move_velocity((-1*self.zStageSpeed.get()/1000), unit=Units.VELOCITY_MILLIMETRES_PER_SECOND)
        print('Z Up at speed', (-1*self.zStageSpeed.get()/1000))

    def zStageUpEnd(self, e):
        self.Zaxis.stop(wait_until_idle=True)
        print('Z Stop')

    def zStageDownStart(self, e):
        self.Zaxis.move_velocity((self.zStageSpeed.get()/1000), unit=Units.VELOCITY_MILLIMETRES_PER_SECOND)
        print('Z Down at speed', (self.zStageSpeed.get()/1000))

    def zStageDownEnd(self, e):
        self.Zaxis.stop(wait_until_idle=True)
        print('Z Stop')

    '''def videoFeed(self):
        self.original = Image.open("C:/Users/Matt Goode/Pictures/IowaStateCyclones.png")
        resized = self.original.resize((self.canvas_x, self.canvas_y))
        self.videofeed = ImageTk.PhotoImage(resized)
        self.c.create_image(0, 0, image=self.videofeed, anchor=NW)'''

    def rotateGrating(self):
        self.rotaryStage.move_to(str(self.gratingAngle.get()))
        self.rotaryStage.wait_for_move(timeout=None)

    def videoFeed(self):
        _, frame = self.cap.read()
        self.cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        self.img = Image.fromarray(self.cv2image)
        resized = self.img.resize((self.canvas_x, self.canvas_y))
        self.videofeed = ImageTk.PhotoImage(resized)
        self.c.create_image(0, 0, image=self.videofeed, anchor=NW)
        #self.c.after(1, self.videoFeed)


    def quit(self):     # quit command for GUI
        self.window.destroy()

Library.toggle_device_db_store(True)
app = MainGUI()
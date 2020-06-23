import math
import serial
import serial.tools.list_ports
import time
import webbrowser
import cv2
import collections
import threading
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
    rotaryStage = Thorlabs.K10CR1(str(55142424))
    micro_step_size = 1.97450259 # units in um
    axis_resolution = 64

    def __init__(self):
        self.window = Tk()
        self.window.title('Gantry Motion Control')
        self.connected_text = Label(self.window, text="Connecting...")
        self.connected_text.pack()
        self.check_connection()
        self.canvas_create()
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
        try:
            CommData = collections.namedtuple("CommData", ["messageID", "data", "source", "dest"])
            homeParameter = CommData(messageID=1090, data=b"\x01\x00\x02\x00\x01\x00'{^\x04UU\x08\x00", source=80, dest=1)
            self.rotaryStage.send_comm_data(0x0440, homeParameter.data)
            self.rotaryStage.home(sync=True, force=True, timeout=None)

        except:
            print('An exception occurred')
        self.status_feed.config(text='Home Complete')
        self.status_feed.update_idletasks()

    def canvas_create(self):
        '''
        Creates canvas for users to select which points they want the stage to go to and allocates button clicks to functions
        '''
        self.color_fg = 'black'
        self.color_bg = 'white'
        self.old_x = None
        self.old_y = None
        self.penwidth = 1
        self.draw_widgets()
        self.c.bind('<ButtonPress-2>', self.square_press)  # create square
        self.c.bind('<B2-Motion>', self.square_motion)
        self.c.bind('<ButtonRelease-2>', self.square_release)
        self.c.bind('<ButtonPress-1>', self.line_press)  # create square
        self.c.bind('<B1-Motion>', self.line_motion)
        self.c.bind('<ButtonRelease-1>', self.line_release)# create point or line

    def draw_widgets(self):
        self.controls = Frame(self.window, padx=5, pady=5)

        self.scan_speed = IntVar()
        self.scan_speed.set(300)
        Label(self.controls, text='XY Stage Velocity (mm/sec)').pack()
        self.scan_speed_select = OptionMenu(self.controls, self.scan_speed, 50, 100, 150, 200, 250, 300)
        self.scan_speed_select.pack()

        Label(self.controls, text='').pack()

        self.stepover_size = IntVar()
        self.stepover_size.set(250)
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

        self.status_feed = Label(self.window, text='', font=("Arial", 18), justify=RIGHT)
        self.status_feed.pack()

        self.videoFeed()

    def line_press(self, e):
        '''
        Code that controls when a person clicks down on the left mouse button
        '''
        self.initialLineX = e.x
        self.initialLineY = e.y

    def line_motion(self, e):
        self.c.delete(ALL)
        self.videoFeed()
        self.c.create_line(self.initialLineX, self.initialLineY, e.x, e.y, width=self.penwidth, fill=self.color_fg,
                           capstyle=ROUND, smooth=True)
    def line_release(self, e):
        if e.x >= self.canvas_x:      #error checking to make sure the final point is on the Canvas
            e.x = self.canvas_x
        elif e.x <= 0:
            e.x = 0
        if e.y >= self.canvas_y:
            e.y = self.canvas_y
        elif e.y <= 0:
            e.y = 0
        self.finalLineX = e.x
        self.finalLineY = e.y
        self.c.delete(ALL)
        self.videoFeed()
        self.c.create_line(self.initialLineX, self.initialLineY, self.finalLineX, self.finalLineY, width=self.penwidth,
                           fill=self.color_fg, capstyle=ROUND, smooth=True)
        self.scan_line()

    def square_press(self, e):
        '''
        Code that controls when a person clicks down on the middle mouse button
        '''
        self.initial_X = e.x
        self.initial_Y = e.y

    def square_motion(self, e):
        '''
        Code that controls when a person clicks down on the middle mouse button
        '''
        self.c.delete(ALL)
        self.videoFeed()
        self.c.create_rectangle(self.initial_X, self.initial_Y, e.x, e.y, fill='black')

    def square_release(self, e):
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
        self.scan_square()

    def scan_square(self):
        '''
        takes points from the square created in squareRelease and controls Zaber stages until scan is complete
        :return:
        '''
        # Update scan status to starting scan
        self.status_feed.config(text='Scan Starting')
        self.status_feed.update_idletasks()

        # Determines which X and Y value is the smallest and sets that value to the starting point
        if self.final_X >= self.initial_X:
            self.start_X = self.initial_X/self.scale_factor
            self.end_X = self.final_X/self.scale_factor
        else:
            self.start_X = self.final_X/self.scale_factor
            self.end_X = self.initial_X/self.scale_factor

        if self.final_Y >= self.initial_Y:
            self.start_Y = self.initial_Y/self.scale_factor
            self.end_Y = self.final_Y/self.scale_factor
        else:
            self.start_Y = self.final_Y/self.scale_factor
            self.end_Y = self.initial_Y/self.scale_factor

        i = round(float(self.start_Y),5)

        try:
            # sets velocity of stage sand moves to starting XY position
            self.Xaxis.settings.set("maxspeed", self.scan_speed.get(), Units.VELOCITY_MILLIMETRES_PER_SECOND)
            self.Yaxis.move_absolute(i, Units.LENGTH_MILLIMETRES, wait_until_idle=False)
            self.Xaxis.move_absolute(self.start_X, Units.LENGTH_MILLIMETRES)

            # calculates and sets trigger
            self.xyController.generic_command(self.trigger_command_creator(self.stepover_size.get(), "X"), check_errors=True)
            time.sleep(2)

            while i <= self.end_Y:
                # enable trigger and move from stating X to ending X
                self.xyController.generic_command("trigger 1 enable", check_errors=True)
                self.Xaxis.move_absolute(self.end_X, Units.LENGTH_MILLIMETRES) # move to end X

                i += self.stepover_size.get() / 1000
                self.xyController.generic_command("trigger 1 disable", check_errors=True)

                print(round(i, 5))
                self.Yaxis.move_absolute(round(i, 5), Units.LENGTH_MILLIMETRES, wait_until_idle=False) # stepover
                self.Xaxis.move_absolute(self.start_X, Units.LENGTH_MILLIMETRES)

                # calculate how much of the scan has been completed and update status feed
                self.scanPrecentCompleteCalculation = round(((i-self.start_Y)/(self.end_Y-self.start_Y))*100, 1)
                self.status_feed.config(text=("Precent complete: " + str(self.scanPrecentCompleteCalculation) + "%"))
                self.status_feed.update_idletasks()

        except MotionLibException as err:
            print(err)

        # Update status feed to scan complete
        self.status_feed.config(text='Scan Complete')

    def scan_line(self):
        '''
        Code that takes the start and end points of a line, calculates each axis's velocity, and commands stage
        to the start/end points
        '''
        # Update scan status to starting scan
        self.status_feed.config(text='Scan Starting')
        self.status_feed.update_idletasks()

        # Determines which X and Y value is the smallest and sets that value to the starting point
        if self.finalLineX >= self.initialLineX:
            self.start_X = self.initialLineX
            self.end_X = self.finalLineX
        else:
            self.start_X = self.finalLineX
            self.end_X = self.initialLineX

        if self.finalLineY >= self.initialLineY:
            self.start_Y = self.initialLineY
            self.end_Y = self.finalLineY
        else:
            self.start_Y = self.finalLineY
            self.end_Y = self.initialLineY

        # calculate the total X, total Y, and line distance of item
        self.x_distance = (self.end_X - self.start_X)/self.scale_factor
        self.y_distance = (self.end_Y - self.start_Y)/self.scale_factor
        self.total_move_distance = math.sqrt(abs(self.x_distance) ** 2 + abs(self.y_distance) ** 2)

        # calculate trigger size for X axis based on stepover size
        if self.x_distance >= self.y_distance:
            self.line_trigger_value = self.stepover_size.get() * (self.x_distance*1000) / (
                    self.total_move_distance*1000)
            self.which_axis = "X"
        else:
            self.line_trigger_value = self.stepover_size.get() * (self.y_distance * 1000) / (
                        self.total_move_distance * 1000)
            self.which_axis = "Y"

        print("X Values:", self.start_X, self.end_X)
        print("Y Values:", self.start_Y, self.end_Y)

        try:
            # set and turn on Zaber trigger
            self.xyController.generic_command(self.trigger_command_creator(self.line_trigger_value, self.which_axis), check_errors=True)
            self.xyController.generic_command("trigger 1 enable", check_errors=True)

            # set velocity
            self.Xaxis.settings.set("maxspeed", self.scan_speed.get(), Units.VELOCITY_MILLIMETRES_PER_SECOND)
            self.Yaxis.settings.set("maxspeed", self.scan_speed.get(), Units.VELOCITY_MILLIMETRES_PER_SECOND)

            # move to stating point and chill for a second
            self.Xaxis.move_absolute(self.start_X / self.scale_factor, Units.LENGTH_MILLIMETRES, wait_until_idle=False)
            self.Yaxis.move_absolute(self.start_Y / self.scale_factor, Units.LENGTH_MILLIMETRES, wait_until_idle=True)
            time.sleep(2)

            # move from starting position to ending position
            self.Xaxis.move_absolute(self.end_X / self.scale_factor, Units.LENGTH_MILLIMETRES, wait_until_idle=False)
            self.Yaxis.move_absolute(self.end_Y / self.scale_factor, Units.LENGTH_MILLIMETRES)

        except MotionLibException as err:
            print(err)

        # Update status feed to scan complete
        self.status_feed.config(text='Scan Complete')
        self.status_feed.update_idletasks()

    def zStageUpStart(self, e):
        try:
            self.Zaxis.move_velocity((-1*self.zStageSpeed.get()/1000), unit=Units.VELOCITY_MILLIMETRES_PER_SECOND)
        except MotionLibException as err:
            print(err)

    def zStageUpEnd(self, e):
        try:
            self.Zaxis.stop(wait_until_idle=True)
        except MotionLibException as err:
            print(err)

    def zStageDownStart(self, e):
        try:
            self.Zaxis.move_velocity((self.zStageSpeed.get()/1000), unit=Units.VELOCITY_MILLIMETRES_PER_SECOND)
        except MotionLibException as err:
            print(err)

    def zStageDownEnd(self, e):
        try:
            self.Zaxis.stop(wait_until_idle=True)
        except MotionLibException as err:
            print(err)

    def trigger_command_creator(self, e, i):
        '''
        Inputs: step over size (user input), micro step size (value from Zaber), axis resolution (value from Zaber)
        :return: ASCII protocal for updating trigger to specified step value
        '''

        self.trigger_value = int(e / self.micro_step_size)
        if i == "X":
            self.trigger_command = "trigger dist 1 1 " + str(self.trigger_value)
            print("X axis trigger")
        else:
            self.trigger_command = "trigger dist 1 2 " + str(self.trigger_value)
            print("Y axis trigger")
        return(self.trigger_command)

    '''def videoFeed(self):
        self.original = Image.open("C:/Users/Matt Goode/Pictures/IowaStateCyclones.png")
        resized = self.original.resize((self.canvas_x, self.canvas_y))
        self.videofeed = ImageTk.PhotoImage(resized)
        self.c.create_image(0, 0, image=self.videofeed, anchor=NW)'''

    def rotateGrating(self):
        '''
        Commands Thorlabs K10CR1/M to rotate to specified angle
        '''
        if int(self.gratingAngle.get()) != round(self.rotaryStage.get_position(), 0):
            self.desiredGratingAngle = int(self.gratingAngle.get())
            self.rotaryStage.move_to(self.desiredGratingAngle)
            self.rotaryStage.wait_for_move(timeout=None)

    def videoFeed(self):
        '''
        Sets up query to camera on computer to update the background image of the canvas
        '''
        _, frame = self.cap.read()
        self.cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        self.img = Image.fromarray(self.cv2image)
        resized = self.img.resize((self.canvas_x, self.canvas_y))
        self.videofeed = ImageTk.PhotoImage(resized)
        self.c.create_image(0, 0, image=self.videofeed, anchor=NW)
        #self.c.after(1, self.videoFeed)

    def quit(self):     # quit command for GUI
        self.cv2image.terminate()
        self.window.destroy()


Library.toggle_device_db_store(True)
app = MainGUI()

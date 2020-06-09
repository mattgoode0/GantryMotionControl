import pyvisa #https://pyvisa.readthedocs.io/en/latest/
import time
import numpy
from datetime import datetime
import pylab


class MSO64:
    hScale = str("20.0E-9")
    vScale = ["100.0E-3", "750.0E-3", "500.0E-3", "50.0E-3"]

    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        print(rm.list_resources())
        self.scope = rm.open_resource('USB::0x0699::0x0528::C021927::INSTR')
        print('Connected to MSO64')

    def ConfigureChannels(self):
        # Configure scope using SCPI commands

        # Reset instrument. Turn on display of all four channels
        self.channelDisplay = str("*RST;:DIS:GLO:CH1:STATE 1;:DIS:GLO:CH2:STATE 1;:DIS:GLO:CH3:STATE 1;:DIS:GLO:CH4:STATE 1")
        self.scope.write(channelDisplay)

        # Name Channels
        self.ch1Label = str("SAW Signal")
        self.ch2Label = str("IR Phototrigger")
        self.ch3Label = str("Stage V Trigger")
        self.ch4Label = str("DC Levels")

        # Build the SCPI string for setting the labels for the oscillscope channels.
        self.channelLabels = str(":CH1:LAB:NAM \"" + self.ch1Label + "\";:CH2:LAB:NAM \"" +
                    self.ch2Label + "\";:CH3:LAB:NAM \"" + self.ch3Label + "\";:CH4:LAB:NAM \"" +
                    self.ch4Label + "\"")

        self.scope.write(self.channelLabels)

        # Set the vertical scale limits
        self.vScaleCMD = str(":CH1:SCA " + self.vScale[0] + ";:CH2:SCA " + self.vScale[1] +
                           ";:CH3:SCA " + self.vScale[2] + ";:CH4:SCA " + self.vScale[3] + ";")
        self.scope.write(self.vScaleCMD)

        self.hScaleCMD = str(":HOR:POS 5;:HOR:SCA " + self.hScale)
        self.scope.write(self.hScaleCMD)

    def configTrigger(self):
        self.triggerCommand = "TRIG:A:TYP LOGI;:TRIG:A:LOGI:FUNC AND;:TRIG:A:LOGICP:CH1 X;:TRIG:A:LOGICP:CH2 HIGH;"
        self.triggerCommand += ":TRIG:A:LOGICP:CH3 HIGH;:TRIG:A:LOGICP:CH4 X;"
        self.triggerCommand += ":TRIG:A:LEV:CH2 " + _triglvl + ";:TRIG:A:LEV:CH3 1.0;"

        self.scope.write(self.triggerCommand)

    def saveFileToSSD(self):
        self.path = "C:\TestScan"
        self.rfBase = self.path + "RF-"
        self.dcBase = self.path + "DC-"
        self.fileFormate = "00000"
        self.rfSaveCMD = "SAV:WAVE CH1, \""
        self.dcSaveCMD = "SAV:WAVE CH4, \""
        self.CurrentTime = time.strftime("%Y%m%d-%H%M")
        self.rfBase += self.CurrentTime + ".wfm"
        self.dcBase += self.CurrentTime + ".wfm"
        self.rfSaveCMD += self.rfBase + "\\"
        self.dcSaveCMD += self.dcBase + "\\"

    def DisconnectMSO(self):
        self.scope.
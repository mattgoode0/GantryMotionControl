from IviScope import *
from VISA_wrapper_metaclass import *
import numbers

class Generic(object):
    __metaclass__ = InstrumentMetaclass
    def write(self,s):
        print s
    def ask(self,s):
        print s
        return '45.4'

class NR1(TestValueFromType): # defined in the DPO3000 doc
    def __init__(self):
        TestValueFromType.__init__(self, numbers.Integral)

class NR2(TestValueFromType): # defined in the DPO3000 doc
    def __init__(self):
        TestValueFromType.__init__(self, numbers.Number)
    def to_string(self, value):
        return "%f"%value

class NR3(TestValueFromType): # defined in the DPO3000 doc
    def __init__(self):
        TestValueFromType.__init__(self, numbers.Number)
    def to_string(self, value):
        return "%e"%value


class Acquisition(Group):
    __metaclass__ = InstrumentMetaclass
    StartTime =  generic_get_set_command('HORizontal:DELay:TIME', NR3())
    Status = AcquisitionStatus.Unknown
    Type = generic_get_set_command('ACQuire:MODe', TestValueFromEnum(AcquisitionType, ['SAMple','HIRes','AVErage','ENVelope','PEAKdetect']))


class ChannelGroup(IndexedGroup):
    __metaclass__ = InstrumentMetaclass
    var = '<X>' # String that should be replaced by the channel number
    Count = 4 # Number of channels
    Coupling = generic_get_set_command('CH<X>:COUPling', TestValueFromEnum(VerticalCoupling, ['AC','DC','GND']))
    Offset = generic_get_set_command('CH<X>:OFFSet',NR3())
 
    @property
    def Name(self):
        return 'CH%i'%self._item

    NumberOfPointsMinimum = generic_get_set_command('HORizontal:RECOrdlength', NR1())
    RecordLength = generic_get_set_command('HORizontal:RECOrdlength', NR1())


class MyScope(Generic, InstrumentCommand):
    def __init__(self, *args, **keywords):
        Generic.__init__(self, *args, **keywords)
        self.Acquisition = Acquisition(self)
        self.Channel = ChannelGroup(self)
    

if __name__=="__main__":
    scope = MyScope()
    scope.Channel[2].Offset = 34.
    scope.Channel[1].Coupling = VerticalCoupling.Ground
    scope.Channel[1].Coupling = 'Ground'
# Note that scope.Channel[1].Coupling = "GND", which is the string send to the scope does not work


from VISA_wrapper import TestValueFromType

class NR1(TestValueFromType):
    def __init__(self):
	TestValueFromType.__init__(self, number.Integral)

class NR2(TestValueFromType):
    def __init__(self):
	TestValueFromType.__init__(self, number.Number)
    def to_string(self, value):
	return "%f"%value

class NR3(TestValueFromType):
    def __init__(self):
	TestValueFromType.__init__(self, number.Number)
    def to_string(self, value):
	return "%e"%value


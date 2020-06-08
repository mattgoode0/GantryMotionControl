import visa
import numpy
from datetime import datetime

visaRsrcAddr = "MSO64"

rm = visa.ResourceManager()
scope = rm.open_resource(visaRsrcAddr)

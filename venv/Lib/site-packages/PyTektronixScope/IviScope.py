from enum import Enum

AcquisitionStatus = Enum('Complete', 'InProgress', 'Unknown')
AcquisitionType = Enum('Normal', 'HiResolution', 'Average', 'PeakDetect', 'Envelope')

VerticalCoupling = Enum('AC','DC','Ground')





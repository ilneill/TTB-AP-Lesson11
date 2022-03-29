# Using an Arduino with Python LESSON 10: Passing Data from Python to Arduino.
# https://www.youtube.com/watch?v=VdSFwYrYqW0
# https://toptechboy.com/

# Internet References:
# https://www.glowscript.org/docs/VPythonDocs/index.html
# https://gist.github.com/eaydin/768a200c5d68b9bc66e7

# https://crccalc.com/?method=crc8
#  CRC-8/MAXIM
#    rgbLEDs=0!243 | rgbLEDs=1!173 | rgbLEDs=4!146


import time
import serial
from vpython import *
import numpy as np

# vPython refresh rate.
vPythonRefreshRate = 100
# Helper Scale Axis toggle.
showAxis = False
# Test the virtual meters with pseudo random data.
pseudoDataMode = False
pseudoDataCounter = 0 # Used to update some virtual meters more slowly.

# A place on which to put our things...
canvas(title = "<b><i>Arduino with Python - Real World Measurements Visualised!</i></b>", background = color.cyan, width = 800, height = 600)

# Axis for helping with virtual meter design and layout.
if showAxis:
    # An origin axis.
    arrow(color = color.blue, round = True, pos = vector(-0.5, 0, 0), axis = vector(1, 0, 0), shaftwidth = 0.02) # X axis.
    arrow(color = color.blue, round = True, pos = vector(0, -0.5, 0), axis = vector(0, 1, 0), shaftwidth = 0.02) # Y axis.
    arrow(color = color.blue, round = True, pos = vector(0, 0, -0.5), axis = vector(0, 0, 1), shaftwidth = 0.02) # Z axis.
    # An Z offest axis.
    for graduation in range(6): # X axis.
        arrow(color = color.magenta, round = True, pos = vector(graduation / 2, 0, 0.25), axis = vector(0.5, 0, 0), shaftwidth = 0.02)
        arrow(color = color.magenta, round = True, pos = vector(-graduation / 2, 0, 0.25), axis = vector(-0.5, 0, 0), shaftwidth = 0.02)
    for graduation in range(4): # Y axis.
        arrow(color = color.magenta, round = True, pos = vector(0, graduation / 2, 0.25), axis = vector(0, 0.5, 0), shaftwidth = 0.02)
        arrow(color = color.magenta, round = True, pos = vector(0, -graduation / 2, 0.25), axis = vector(0, -0.5, 0), shaftwidth = 0.02)
    for graduation in range(2): # Z axis.
        arrow(color = color.magenta, round = True, pos = vector(0, 0, graduation / 2), axis = vector(0, 0, 0.5), shaftwidth = 0.02)
        arrow(color = color.magenta, round = True, pos = vector(0, 0, -graduation / 2), axis = vector(0, 0, -0.5), shaftwidth = 0.02)

# Return some pseudo random data for virtual meter testing.
def pseudoData():
    time.sleep(0.1) # Not too fast...
    pot1Value = int(1023 * np.random.rand())
    tDHT11 = (70 * np.random.rand() - 10.0)
    hDHT11 = (100 * np.random.rand())
    tDHT22 = (70 * np.random.rand() - 10.0)
    hDHT22 = (100 * np.random.rand())
    return(pot1Value, tDHT11, hDHT11, tDHT22, hDHT22)

# A bag of small screws for us to draw exactly where we like.
def drawScrew(sPos = vector(0, 0, 0)):
    cylinder(color = color.black, opacity = 1, pos = vector(0, 0, 0.05) + sPos, axis = vector(0, 0, 0.04), radius = 0.06) # Head.
    cylinder(color = color.black, opacity = 1, pos = vector(0, 0, 0) + sPos, axis = vector(0, 0, 0.05), radius = 0.03)    # Shaft.
    cone(color = color.black, opacity = 1, pos = vector(0, 0, 0) + sPos, axis = vector(0, 0, -0.25), radius = 0.03)       # Thread.
    slotAngle = np.random.rand() * np.pi / 2 # An angle between 0 and 90 degrees.
    screwCross1 = box(color = vector(0.8, 0.8, 0.8), opacity = 1, pos = vector(0, 0, 0.0801) + sPos, size = vector(0.1, 0.02, 0.02)) # Cross pt1.
    screwCross1.rotate(angle = slotAngle, axis = vector(0, 0, 1))               # Randomly rotate this part of the cross.
    screwCross2 = box(color = vector(0.8, 0.8, 0.8), opacity = 1, pos = vector(0, 0, 0.0801) + sPos, size = vector(0.1, 0.02, 0.02)) # Cross pt2.
    screwCross2.rotate(angle = slotAngle + np.pi / 2, axis = vector(0, 0, 1))   # Add 90 degrees for the other part of the cross.

# Work out the Arduino rgbLEDs command action.
def rgbLEDsAction(sensorValue = "nan", bgThreshold = 30, rgThreshold = 70, hysteresis = 0.5):
    # TODO: Adjust thresholds to stabilise the LEDs if a reading is jittering around a boundary.
    # If we have valid data.
    if sensorValue != "nan":
        if sensorValue < bgThreshold:                 # Under the blue-green threshold.
            arduinoAction = 1                         # Bit 0 set to 1.
        if bgThreshold <= sensorValue <= rgThreshold: # Within the thresholds for green.
            arduinoAction = 2                         # Bit 1 set to 1.
        if sensorValue > rgThreshold:                 # Over the green-red threshold.
            arduinoAction = 4                         # Bit 2 set to 1.
    else:
        arduinoAction = 0                             # Otherwise all LEDs are turned off.
    return arduinoAction

# Calculate a Dallas/Maxim CRC8 checksum. Literally, the Arduino code translated...
def calcCRC8(data2Check = ""):
    chksumCRC8 = 0
    for character in data2Check:
        dataByte = ord(character)                     # Get the ASCII value of the byte to be processed.
        for bitCounter in range(8):
            sum = ((dataByte ^ chksumCRC8) & 1)
            chksumCRC8 >>= 1
            if sum:
                chksumCRC8 ^= 0x8c
            dataByte >>= 1
    return chksumCRC8

# Meter Type 1 - A rectangluar style meter with a curved scale and a needle, and a 30%/70% band indication BGR LED.
class meterType1:
    def __init__(self, mt1Pos = vector(0, 0, 0), mt1Color = color.red, mt1ScaleMin = 0, mt1ScaleMax = 5, mt1Label = "", mt1Units = ""):
        self.mt1Pos = mt1Pos
        self.mt1Color = mt1Color
        self.mt1ScaleMin = int(mt1ScaleMin)
        self.mt1ScaleMax = int(mt1ScaleMax)
        self.mt1ScaleRange = mt1ScaleMax - mt1ScaleMin
        self.mt1Label = mt1Label
        self.mt1Units = mt1Units
        # Draw the virtual meter...
        box(color = color.white, opacity = 1, size = vector(2.25, 1.5, 0.1), pos = vector(0, 0, 0) + self.mt1Pos) # Draw the virtual meter box.
        # Draw the virtual meter needle and set it to the 0 position.
        self.meterNeedle = arrow(length = 1, shaftwidth = 0.02, color = self.mt1Color, round = True, pos = vector(0, -0.65, 0.1) + self.mt1Pos, axis = vector(np.cos(5 * np.pi / 6), np.sin(5 * np.pi / 6), 0))
        cylinder(color = self.mt1Color, opacity = 1, radius = 0.05, pos = vector(0, -0.65, 0.05) + self.mt1Pos, axis = vector(0, 0, 0.1))
        cylinder(color = color.gray(0.5), opacity = 1, radius = 0.2, pos = vector(0, -0.5, 0.05) + self.mt1Pos, axis = vector(0, 0, 0.01))
        # Draw the virtual meter scale major marks.
        for unitCounter, theta in zip(range(self.mt1ScaleMin, self.mt1ScaleMax + 1), np.linspace(5 * np.pi / 6, np.pi / 6, self.mt1ScaleRange + 1)):
            majorUnit = text(text = str(unitCounter), color = self.mt1Color, opacity = 1, align = "center", height = 0.1, pos = vector(1.1 * np.cos(theta), 1.1 * np.sin(theta) - 0.65, 0.095) + self.mt1Pos)
            majorUnit.rotate(angle = theta - np.pi / 2, axis = vector(0, 0, 1))
            box(color = color.black, pos = vector(np.cos(theta), np.sin(theta) - 0.65, 0.08) + self.mt1Pos, size = vector(0.1, 0.02, 0.02), axis = vector(np.cos(theta), np.sin(theta), 0))
        # Draw the virtual meter scale minor marks.
        for unitCounter, theta in zip(range(self.mt1ScaleMin * 10, (self.mt1ScaleMax * 10) + 1), np.linspace(5 * np.pi / 6, np.pi / 6, (self.mt1ScaleRange * 10) + 1)):
            if unitCounter % 5 == 0 and unitCounter % 10 != 0: # Draw the minor unit midway between the major marks.
                minorUnit = text(text = "5", color = self.mt1Color, opacity = 1, align = "center", height = 0.05, pos = vector(1.05 * np.cos(theta), 1.05 * np.sin(theta) - 0.65, 0.095) + self.mt1Pos)
                minorUnit.rotate(angle = theta - np.pi / 2, axis = vector(0, 0, 1))
            box(color = color.black, pos = vector(np.cos(theta), np.sin(theta) - 0.65, 0.08) + self.mt1Pos, size = vector(0.05, 0.01, 0.01), axis = vector(np.cos(theta), np.sin(theta), 0))
        # Meter Label and Units.
        text(text = self.mt1Label, color = self.mt1Color, opacity = 1, align = "center", height = 0.1, pos = vector(0, 0.6, 0.1) + self.mt1Pos, axis = vector(1, 0, 0))
        text(text = self.mt1Units, color = self.mt1Color, opacity = 1, align = "center", height = 0.115, pos = vector(0, 0, 0.1) + self.mt1Pos, axis = vector(1, 0, 0))
        # Add the raw reading too - this is initially not visible as the value may not be provided in future updates.
        self.rawValue = label(text = "0000", visible = False, color = self.mt1Color, height = 10, opacity = 0, box = False, pos = vector(-0.75, 0.6, 0.1) + self.mt1Pos)
        # Add the digital reading too.
        self.digitalValue = label(text = "0.00V", visible = True, color = self.mt1Color, height = 10, opacity = 0, box = False, pos = vector(0.75, 0.6, 0.1) + self.mt1Pos)
        # Add a 30%/70% band indicator RGB Color LED.
        self.voltageRGBLED  = rgbColorLED(vector(0.75, -0.425, 0.05) + self.mt1Pos, self.mt1ScaleRange * 0.3, self.mt1ScaleRange * 0.7)
        # Corner screws.
        drawScrew(vector(-1.045, 0.67, -0.03) + self.mt1Pos)  # Top Left corner.
        drawScrew(vector(1.045, 0.67, -0.03) + self.mt1Pos)   # Top Right corner.
        drawScrew(vector(-1.045, -0.67, -0.03) + self.mt1Pos) # Bottom Left corner.
        drawScrew(vector(1.045, -0.67, -0.03) + self.mt1Pos)  # Bottom Right corner.
        # Lets put a mostly transparent glass cover over the virtual meter.
        box(color = color.white, opacity = 0.25, size = vector(2.25, 1.5, 0.32), pos = vector(0, 0, 0.15) + self.mt1Pos)
        # At this point we have no data to drive the virtual meter.
        self.DataWarning = text(text = "-No Data-", color = self.mt1Color, opacity = 1, align = "center", height = 0.125, pos = vector(0, -0.25, 0.2) + self.mt1Pos, axis = vector(1, 0, 0))
    def update(self, mt1Value = "NAN", mt1RawValue = "-1"):
        if mt1Value != "nan":
            # Clip the virtual meter value if it is out of range.
            self.mt1Value = np.clip(mt1Value, self.mt1ScaleMin, self.mt1ScaleMax)
            # If we have a raw value, store it and make it visible.
            if mt1RawValue != "-1":
                self.mt1RawValue = mt1RawValue
                self.rawValue.visible = True
            else:
                self.rawValue.visible = False
            # Turn off the data warning.
            self.DataWarning.opacity = 0
            # Print the raw potentiometer value.
            self.rawValue.text = str("<i>%04d</i>" % self.mt1RawValue)
            # Print the digital value.
            self.digitalValue.text = str("%1.2f" % self.mt1Value) + "V"
            # Use the value to set the angle of virtual meter needle... explanation...
            #   0V is 5pi/6 rads, 5V is pi/6 rads, thus the needle movement range is 4pi/6 rads.
            #   The value range is ScaleMin -> ScaleMax, or ScaleRange, so needle angle is the (needle range * value/max) ratio.
            #       = 4pi/6 * (Value - ScaleMin) / ScaleRange rads.
            #   Thus, the needle position is 5pi/6 - (4pi/6 * (Value - ScaleMin) / ScaleRange) rads.
            # e.g. ScaleMin = -5, ScaleMax = +5, ScaleRange = 10 => needle position is 5pi/6 - (4pi/6 * (Value - -5) / 10) rads
            theta  = (5 * np.pi / 6) - (4 * np.pi / 6 * ((self.mt1Value - self.mt1ScaleMin) / self.mt1ScaleRange))
            self.meterNeedle.axis = vector(np.cos(theta), np.sin(theta), 0)
            # Update the rgbLED.
            self.voltageRGBLED.update(self.mt1Value)
        else:
            # Turn on the data warning.
            self.DataWarning.opacity = 1

# Meter Type 2 - A circular style virtual meter with a scale and a curved 101 segment bar.
class meterType2:
    def __init__(self, mt2Pos = vector(0, 0, 0), mt2Color = color.blue, mt2ScaleMin = 0, mt2ScaleMax = 100, mt2Label = "", mt2Units = ""):
        self.mt2Pos = mt2Pos
        self.mt2Color = mt2Color
        self.mt2ScaleMin = int(mt2ScaleMin)
        self.mt2ScaleMax = int(mt2ScaleMax)
        self.mt2ScaleRange = mt2ScaleMax - mt2ScaleMin
        self.mt2Label = mt2Label
        self.mt2Units = mt2Units
        # Draw the virtual meter...
        cylinder(color = color.white, opacity = 1, radius = 0.85, pos = vector(0, 0, -0.05) + self.mt2Pos, axis = vector(0, 0, 0.1)) # Draw the virtual meter dial.
        # Draw the virtual meter segments and set them to "off" status.
        self.meterSegments = [] # A list in which to put all the virtual meter segments for later reference and update.
        for segmentCounter, theta in zip(range(100 + 1), np.linspace(8 * np.pi / 6, np.pi / 6, 100 + 1)):
            # Box segments have an off opacity equal to their proportional postion in the range.
            self.meterSegments.append(box(color = color.white, opacity = segmentCounter / self.mt2ScaleRange, size = vector(0.15, 0.025, 0.02), pos = vector(0.55 * np.cos(theta), 0.55 * np.sin(theta), 0.095) + self.mt2Pos, axis = vector(np.cos(theta - np.pi), np.sin(theta - np.pi), 0)))
        # Draw the virtual meter scale major marks.
        for unitCounter, theta in zip(range(self.mt2ScaleMin, self.mt2ScaleMax + 1), np.linspace(8 * np.pi / 6, np.pi / 6, self.mt2ScaleRange + 1)):
            if unitCounter % 10 ==0:
                majorUnit = text(text = str(unitCounter), color = self.mt2Color, opacity = 1, align = "center", height = 0.065, pos = vector(0.75 * np.cos(theta), 0.75 * np.sin(theta), 0.095) + self.mt2Pos)
                majorUnit.rotate(angle = theta - np.pi / 2, axis = vector(0, 0, 1))
                box(color = color.black, pos = vector(0.685 * np.cos(theta), 0.685 * np.sin(theta), 0.095) + self.mt2Pos, size = vector(0.1, 0.02, 0.02), axis = vector(np.cos(theta), np.sin(theta), 0))
        # Draw the virtual meter scale minor marks.
        for unitCounter, theta in zip(range(self.mt2ScaleMin, self.mt2ScaleMax + 1), np.linspace(8 * np.pi / 6, np.pi / 6, self.mt2ScaleRange + 1)):
            if unitCounter % 5 == 0 and unitCounter % 10 != 0: # Draw the minor unit midway between the major marks.
                minorUnit = text(text = "5", color = self.mt2Color, opacity = 1, align = "center", height = 0.05, pos = vector(0.72 * np.cos(theta), 0.72 * np.sin(theta), 0.095) + self.mt2Pos)
                minorUnit.rotate(angle = theta - np.pi / 2, axis = vector(0, 0, 1))
            box(color = color.black, pos = vector(0.685 * np.cos(theta), 0.685 * np.sin(theta), 0.095) + self.mt2Pos, size = vector(0.05, 0.01, 0.01), axis = vector(np.cos(theta), np.sin(theta), 0))
        # Meter Label and Units.
        text(text = self.mt2Label, color = self.mt2Color, opacity = 1, align = "center", height = 0.1, pos = vector(0, 0.2, 0.1) + self.mt2Pos, axis = vector(1, 0, 0))
        text(text = self.mt2Units, color = self.mt2Color, opacity = 1, align = "center", height = 0.115, pos = vector(0, -0.3, 0.1) + self.mt2Pos, axis = vector(1, 0, 0))
        # Add the raw digital reading too.
        self.rawValue = label(text = "00.0", color = self.mt2Color, height = 10, opacity = 0, box = False, pos = vector(0.5, 0, 0.1) + self.mt2Pos)
        # Center screw.
        drawScrew(vector(0, 0, -0.03) + self.mt2Pos)
        # Lets put a mostly transparent glass cover over the virtual meter.
        cylinder(color = color.white, opacity = 0.25, radius = 0.85, pos = vector(0, 0, -0.05) + self.mt2Pos, axis = vector(0, 0, 0.25))
        # At this point we have no data to drive the virtual meter.
        self.DataWarning = text(text = "-No Data-", color = self.mt2Color, opacity = 1, align = "center", height = 0.125, pos = vector(0, -0.5, 0.2) + self.mt2Pos, axis = vector(1, 0, 0))
    def update(self, mt2Value = "NAN"):
        # If we have valid data.
        if mt2Value != "NAN":
            # Clip the virtual meter value if it is out of range.
            self.mt2Value = np.clip(mt2Value, self.mt2ScaleMin, self.mt2ScaleMax)
            # Turn off the data warning.
            self.DataWarning.opacity = 0
            # Print the raw digital sensor value.
            self.rawValue.text = str("<i>%2.1f</i>" % self.mt2Value)
            # Calculate the proportion of segments to light.
            meterSegmentsOn = ((self.mt2Value - self.mt2ScaleMin) / self.mt2ScaleRange * 100) + 1
            # Work through the segments setting their colour and opacity.
            for meterSegment in range(0, 100 + 1, 1):
                # Colour.
                if meterSegment <= int(meterSegmentsOn): # If on (fully or partially), the segments are set to their on colour.
                    self.meterSegments[meterSegment].color = self.mt2Color
                else: # Otherwise they are set to white.
                    self.meterSegments[meterSegment].color = color.white
                # Opacity.
                if meterSegment < int(meterSegmentsOn):
                    # Fully on segments are opacity 1.
                    self.meterSegments[meterSegment].opacity = 1
                elif meterSegment == int(meterSegmentsOn):
                    # If a segment is partially on, use modulo maths to set the opacity to the fractional part of the number.
                    self.meterSegments[meterSegment].opacity = meterSegmentsOn % 1
                else:
                    # Fully off segments have an opacity equal to their proportional postion in the range.
                    self.meterSegments[meterSegment].opacity = meterSegment / self.mt2ScaleRange
        else:
            # Turn on the data warning.
            self.DataWarning.opacity = 1

# Meter Type 3 - A thermometer style virtual meter with a scale and rising column.
class meterType3:
    def __init__(self, mt3Pos = vector(0, 0, 0), mt3Color = color.red, mt3ScaleMin = 0.0, mt3ScaleMax = 100.0, mt3Label = "", mt3Units = ""):
        self.mt3Pos = mt3Pos
        self.mt3Color = mt3Color
        self.mt3ScaleMin = mt3ScaleMin
        self.mt3ScaleMax = mt3ScaleMax
        self.mt3Range = mt3ScaleMax - mt3ScaleMin
        self.mt3Label = mt3Label
        self.mt3Units = mt3Units
        # Draw the virtual meter...
        box(color = color.white, opacity = 1, size = vector(0.75, 1.75, 0.1), pos = vector(0, 0, 0) + self.mt3Pos) # Draw the virtual meter box.
        sphere(color = self.mt3Color, radius = 0.1, pos = vector(0, -0.65, 0.15) + self.mt3Pos)
        cylinder(color = color.gray(0.5), opacity = 1, pos = vector(0, -0.65, 0.15) + self.mt3Pos, axis = vector(0, 1.15, 0), radius = 0.049)
        sphere(color = color.gray(0.5), opacity = 1, radius = 0.049, pos = vector(0, 0.5, 0.15) + self.mt3Pos)
        self.measurement = cylinder(color = self.mt3Color, pos = vector(0, -.65, 0.15) + self.mt3Pos, axis = vector(0, 0.15, 0), radius = 0.05)
        for unitCounter, tick in zip(np.linspace(self.mt3ScaleMin, self.mt3ScaleMax, 11), np.linspace(0, 1, 11)):
            text(text = str(unitCounter), color = self.mt3Color, align = "right", height = 0.05, pos = vector(-0.15, -0.6725 + 0.15 + tick, 0.15) + self.mt3Pos)
            box(color = color.black, pos = vector(-0.1, -0.65 + 0.15 + tick, 0.15) + self.mt3Pos, size = vector(0.05, 0.01, 0.01), axis = vector(1, 0, 0))
        for tick in np.linspace(0, 1, 51):
            box(color = color.black, pos = vector(-0.1, -0.65 + 0.15 + tick, 0.15) + self.mt3Pos, size = vector(0.025, 0.005, 0.005), axis = vector(1, 0, 0))
        text(text = self.mt3Label, color = self.mt3Color, opacity = 1, align = "center", height = 0.075, pos = vector(0, 0.6, 0.15) + self.mt3Pos, axis = vector(1, 0, 0))
        text(text = self.mt3Units, color = self.mt3Color, opacity = 1, align = "left", height = 0.095, pos = vector(0.125, -0.685, 0.15) + self.mt3Pos, axis = vector(1, 0, 0))
        # Add the raw reading too.
        self.rawValue = label(text = "00.0", color = self.mt3Color, height = 10, opacity = 0, box = False, pos = vector(0, -0.82, 0.1) + self.mt3Pos)
        # Corner screws.
        drawScrew(vector(-0.3, 0.8, -0.03) + self.mt3Pos)  # Top Left corner.
        drawScrew(vector(0.3, 0.8, -0.03) + self.mt3Pos)   # Top Right corner.
        drawScrew(vector(-0.3, -0.8, -0.03) + self.mt3Pos) # Bottom Left corner.
        drawScrew(vector(0.3, -0.8, -0.03) + self.mt3Pos)  # Bottom Right corner.
        # Lets put a mostly transparent glass cover over the virtual meter.
        box(color = color.white, opacity = 0.25, size = vector(0.75, 1.75, 0.32), pos = vector(0, 0, 0.1) + self.mt3Pos)
        # At this point we have no data to drive the virtual meter.
        self.DataWarning = text(text = "-No Data-", color = self.mt3Color, opacity = 1, align = "center", height = 0.125, pos = vector(0, 0, 0.2) + self.mt3Pos, axis = vector(1, 0, 0))
    def update(self, mt3Value = "NAN"):
        # If we have valid data.
        if mt3Value != "NAN":
            # Clip the virtual meter value if it is out of range.
            self.mt3Value = np.clip(mt3Value, self.mt3ScaleMin, self.mt3ScaleMax)
            # Turn off the data warning.
            self.DataWarning.opacity = 0
            # Print the raw digital sensor value.
            self.rawValue.text = str("<i>%2.1f</i>" % self.mt3Value)
            # Update the virtual meter reading - basically converting the measurement to a proportion of the unit length column.
            self.measurement.axis = vector(0, 0.15 + ((self.mt3Value - self.mt3ScaleMin)  / self.mt3Range), 0)
        else:
            # Turn on the data warning.
            self.DataWarning.opacity = 1

# Meter Type 4 - A 10 segment LED bank style virtual meter with blue, green and red LEDs that illuminate from left to right, or bottom to top.
class meterType4:
    def __init__(self, mt4Pos = vector(0, 0, 0), mt4InARow = True, mt4OffColor = color.gray(0.5), mt4ScaleMin = 0.0, mt4ScaleMax = 100.0):
        self.mt4Pos = mt4Pos
        self.mt4InARow = mt4InARow
        self.mt4OffColor = mt4OffColor
        self.mt4ScaleMin = mt4ScaleMin
        self.mt4ScaleMax = mt4ScaleMax
        self.mt4Range = mt4ScaleMax - mt4ScaleMin
        # Draw the LED bank...
        if self.mt4InARow:
            box(color = color.white, opacity = 1, size = vector(0.775, 0.2, 0.16), pos = vector(0, 0, 0.08) + self.mt4Pos) # Draw the LED box horizontally.
        else:
            box(color = color.white, opacity = 1, size = vector(.2, 0.775, 0.16), pos = vector(0, 0, 0.08) + self.mt4Pos) # Draw the LED box vertically.
        # Draw the LED bank segments and set them to off status.
        self.ledSegments = [] # A list in which to put all the LED segments for later reference and update.
        for axisOffset in np.linspace(-0.3375, 0.3375, 10): # The LED bank has 10 LEDs, in a row or a column.
            if self.mt4InARow:
                self.ledSegments.append(box(color = self.mt4OffColor, opacity = 1 , size = vector(0.05, 0.15, 0.07), pos = vector(axisOffset, 0, 0.13) + self.mt4Pos, axis = vector(0, 0, 0)))
                cylinder(color = color.white, opacity = 1, pos = vector(axisOffset, 0.05, 0.095) + self.mt4Pos, axis = vector(0, 0, -0.35), radius = 0.01)
                cylinder(color = color.white, opacity = 1, pos = vector(axisOffset, -0.05, 0.095) + self.mt4Pos, axis = vector(0, 0, -0.3), radius = 0.01)
            else:
                self.ledSegments.append(box(color = self.mt4OffColor, opacity = 1 , size = vector(0.15, 0.05, 0.07), pos = vector(0, axisOffset, 0.13) + self.mt4Pos, axis = vector(0, 0, 0)))
                cylinder(color = color.white, opacity = 1, pos = vector(0.05, axisOffset, 0.095) + self.mt4Pos, axis = vector(0, 0, -0.35), radius = 0.01)
                cylinder(color = color.white, opacity = 1, pos = vector(-0.05, axisOffset, 0.095) + self.mt4Pos, axis = vector(0, 0, -0.3), radius = 0.01)
        # At this point we have no data to drive the virtual meter.
        self.DataWarning = text(text = "-No Data-", color = self.mt4OffColor, opacity = 1, align = "center", height = 0.1, pos = vector(0, -0.055, 0.2) + self.mt4Pos, axis = vector(1, 0, 0))
    def update(self, mt4Value = "NAN"):
        # If we have valid data.
        if mt4Value != "NAN":
            # Clip the virtual meter value if it is out of range.
            self.mt4Value = np.clip(mt4Value, self.mt4ScaleMin, self.mt4ScaleMax)
            # Turn off the data warning.
            self.DataWarning.opacity = 0
            # Calculate the proportion of LED segments to light.
            ledSegmentsOn = (self.mt4Value - self.mt4ScaleMin) / self.mt4Range * 10
            # Work through the LEDs segments setting their colour and opacity.
            for ledSegment in range(0, 10, 1):
                # Colour.
                if ledSegment <= int(ledSegmentsOn):
                    if ledSegment < 3:         # If on, the first 3 LEDs are blue.
                        self.ledSegments[ledSegment].color = color.blue
                    elif 3 <= ledSegment <= 6: # If on, the middle 4 LEDs are green.
                        self.ledSegments[ledSegment].color = color.green
                    else:                      # if on, the remaining 3 LEDs are red.
                        self.ledSegments[ledSegment].color = color.red
                else:                          # Otherwise the LEDs are set to the off colour.
                    self.ledSegments[ledSegment].color = self.mt4OffColor
                # Opacity.
                if ledSegment < int(ledSegmentsOn) or ledSegment > int(ledSegmentsOn):
                    # Fully on or off LEDs are opacity 1.
                    self.ledSegments[ledSegment].opacity = 1
                else:
                    # An LED is partially on only if it is more than 25% on.
                    if ledSegmentsOn % 1 < 0.25: # Using modulo maths to get the fractional part of the number.
                        self.ledSegments[ledSegment].color = self.mt4OffColor
                        self.ledSegments[ledSegment].opacity = 1
                    else:
                        self.ledSegments[ledSegment].opacity = ledSegmentsOn % 1 # Set the opacity to the fractional part of the number.
        else:
            # Turn on the data warning.
            self.DataWarning.opacity = 1

# A simple LED.
class smallLED():
    def __init__(self, smallLEDPos = vector(0, 0, 0), offColor = color.gray(0.5)):
        self.smallLEDPos = smallLEDPos
        self.offColor = offColor
        self.ledDome = sphere(color = self.offColor, opacity = 1, radius = 0.1, pos = vector(0, 0, 0.15) + self.smallLEDPos)
        self.ledBody = cylinder(color = self.offColor, opacity = 1, pos = vector(0, 0, 0.15) + self.smallLEDPos, axis = vector(0, 0, -0.1), radius = 0.1)
        self.ledBase = cylinder(color = self.offColor, opacity = 1, pos = vector(0, 0, 0.05) + self.smallLEDPos, axis = vector(0, 0, -0.05), radius = 0.125)
        cylinder(color = color.white, opacity = 1, pos = vector(-0.05, 0, 0) + self.smallLEDPos, axis = vector(0, 0, -0.25), radius = 0.01)
        cylinder(color = color.white, opacity = 1, pos = vector(0.05, 0, 0) + self.smallLEDPos, axis = vector(0, 0, -0.30), radius = 0.01)
    def update(self, smallLEDColor = "default"):
        if smallLEDColor == "default":
            self.color = self.offColor
        else:
            self.color = smallLEDColor
        self.ledDome.color = self.color
        self.ledBody.color = self.color
        self.ledBase.color = self.color
# A horizontal or vertical bank of 3 simple LEDs.
class rgbLEDBank():
    def __init__(self, rgbLEDBankPos = vector(0, 0, 0), rgbInARow = True, bgThreshold = 5, rgThreshold = 30, hysteresis = 0.5):
        self.rgbLEDBankPos = rgbLEDBankPos
        self.rgbInARow = rgbInARow
        self.bgThreshold = bgThreshold
        self.rgThreshold = rgThreshold
        self.hysteresis = hysteresis # TODO: Adjust thresholds to stabilise the LEDs if a reading is jittering around a boundary.
        if self.rgbInARow:  # Draw the LEDs horizontally.
            self.blueLED  = smallLED(vector(-0.25, 0, 0) + self.rgbLEDBankPos)
            self.greenLED = smallLED(vector(0, 0, 0) + self.rgbLEDBankPos)
            self.redLED   = smallLED(vector(0.25, 0, 0) + self.rgbLEDBankPos)            
        else:               # Draw the LEDs vertically.
            self.blueLED  = smallLED(vector(0, -0.25, 0) + self.rgbLEDBankPos)
            self.greenLED = smallLED(vector(0, 0, 0) + self.rgbLEDBankPos)
            self.redLED   = smallLED(vector(0, 0.25, 0) + self.rgbLEDBankPos)
    def update(self, sensorValue = "NAN"):
        # If we have valid data.
        if sensorValue != "NAN":
            self.sensorValue = sensorValue
            if self.sensorValue < self.bgThreshold: # Under the blue-green threshold.
                self.blueLED.update(color.blue)
                self.greenLED.update()
                self.redLED.update()
            if self.bgThreshold <= self.sensorValue <= self.rgThreshold: # Within the thresholds for green.
                self.blueLED.update()
                self.greenLED.update(color.green)
                self.redLED.update()
            if self.sensorValue > self.rgThreshold: # Over the green-red threshold.
                self.blueLED.update()
                self.greenLED.update()
                self.redLED.update(color.red)
# A 3 discrete RGB color LED.
class rgbColorLED():
    def __init__(self, rgbColorLEDPos = vector(0, 0, 0), bgThreshold = 1.5, rgThreshold = 3.5, hysteresis = 0.5, offColor = color.gray(0.5)):
        self.rgbColorLEDPos = rgbColorLEDPos
        self.offColor = offColor
        self.bgThreshold = bgThreshold
        self.rgThreshold = rgThreshold
        self.hysteresis = hysteresis # TODO: Adjust thresholds to stabilise the LEDs if a reading is jittering around a boundary.
        self.ledDome = sphere(color = self.offColor, opacity = 1, radius = 0.1, pos = vector(0, 0, 0.15) + self.rgbColorLEDPos)
        self.ledBody = cylinder(color = self.offColor, opacity = 1, pos = vector(0, 0, 0.15) + self.rgbColorLEDPos, axis = vector(0, 0, -0.1), radius = 0.1)
        self.ledBase = cylinder(color = self.offColor, opacity = 1, pos = vector(0, 0, 0.05) + self.rgbColorLEDPos, axis = vector(0, 0, -0.05), radius = 0.125)
        cylinder(color = color.white, opacity = 1, pos = vector(-0.06, 0, 0) + self.rgbColorLEDPos, axis = vector(0, 0, -0.25), radius = 0.01)
        cylinder(color = color.white, opacity = 1, pos = vector(-0.02, 0, 0) + self.rgbColorLEDPos, axis = vector(0, 0, -0.30), radius = 0.01)
        cylinder(color = color.white, opacity = 1, pos = vector(0.02, 0, 0) + self.rgbColorLEDPos, axis = vector(0, 0, -0.35), radius = 0.01)
        cylinder(color = color.white, opacity = 1, pos = vector(0.06, 0, 0) + self.rgbColorLEDPos, axis = vector(0, 0, -0.25), radius = 0.01)
    def update(self, sensorValue = "NAN"):
        # If we have valid data.
        if sensorValue != "NAN":
            self.sensorValue = sensorValue
            if self.sensorValue < self.bgThreshold: # Under the blue-green threshold.
                self.color = color.blue
            if self.bgThreshold <= self.sensorValue <= self.rgThreshold: # Within the thresholds for green.
                self.color = color.green
            if self.sensorValue > self.rgThreshold: # Over the green-red threshold.
                self.color = color.red
            self.ledDome.color = self.color
            self.ledBody.color = self.color
            self.ledBase.color = self.color
# A full range RGB tricolor LED.
class rgbTriColorLED():
    def __init__(self, rgbTriColorLEDPos = vector(0, 0, 0), offColorR = 127, offColorG = 127, offColorB = 127):
        self.rgbTriColorLEDPos = rgbTriColorLEDPos
        self.offColorR = offColorR / 255
        self.offColorG = offColorG / 255
        self.offColorB = offColorB / 255
        self.offColor = vector(self.offColorR, self.offColorG, self.offColorB)
        self.ledDome = sphere(color = self.offColor, opacity = 1, radius = 0.1, pos = vector(0, 0, 0.15) + self.rgbTriColorLEDPos)
        self.ledBody = cylinder(color = self.offColor, opacity = 1, pos = vector(0, 0, 0.15) + self.rgbTriColorLEDPos, axis = vector(0, 0, -0.1), radius = 0.1)
        self.ledBase = cylinder(color = self.offColor, opacity = 1, pos = vector(0, 0, 0.05) + self.rgbTriColorLEDPos, axis = vector(0, 0, -0.05), radius = 0.125)
        cylinder(color = color.white, opacity = 1, pos = vector(-0.06, 0, 0) + self.rgbTriColorLEDPos, axis = vector(0, 0, -0.25), radius = 0.01)
        cylinder(color = color.white, opacity = 1, pos = vector(-0.02, 0, 0) + self.rgbTriColorLEDPos, axis = vector(0, 0, -0.30), radius = 0.01)
        cylinder(color = color.white, opacity = 1, pos = vector(0.02, 0, 0) + self.rgbTriColorLEDPos, axis = vector(0, 0, -0.35), radius = 0.01)
        cylinder(color = color.white, opacity = 1, pos = vector(0.06, 0, 0) + self.rgbTriColorLEDPos, axis = vector(0, 0, -0.25), radius = 0.01)
    def update(self, rgbTriColorLEDR = "default", rgbTriColorLEDG = "default", rgbTriColorLEDB = "default"):
        if rgbTriColorLEDR == "default":
            self.colorR = self.offColorR
        else:
            self.colorR = rgbTriColorLEDR / 255
        if rgbTriColorLEDG == "default":
            self.colorG = self.offColorG
        else:
            self.colorG = rgbTriColorLEDG / 255
        if rgbTriColorLEDB == "default":
            self.colorB = self.offColorB
        else:
            self.colorB = rgbTriColorLEDB / 255
        self.color = vector(self.colorR, self.colorG, self.colorB)
        self.ledDome.color = self.color
        self.ledBody.color = self.color
        self.ledBase.color = self.color

# Lets draw some virtual meters.
voltageMeter1  = meterType1(vector(0, 0.675, -0.1), color.red, 0, 5, "Potentiometer 1", "V")
thermoMeter1   = meterType3(vector(-2.5, 0.75, -0.1), color.red, -10, 60, "DHT11 Temp", u"\N{DEGREE SIGN}C") # Using UTF8 to get a degree symbol.
humidityMeter1 = meterType2(vector(-2.25, -1.25, -0.1), color.blue, 0, 100, "DHT11 Hum", "%")
alertLEDs      = rgbLEDBank(vector(-1.75, 0.75, -0.15), False, 5, 30) # Blue/Green threshold is 5, Green/Red threshold is 30.
thermoMeter2   = meterType3(vector(2.5, 0.75, -0.1), color.red, -10, 60, "DHT22 Temp", u"\N{DEGREE SIGN}C")  # Using UTF8 to get a degree symbol.
humidityMeter2 = meterType2(vector(2.25, -1.25, -0.1), color.blue, 0, 100, "DHT22 Hum", "%")
alertLEDBank   = meterType4(vector(1.75, 0.75, -0.15), False, color.gray(0.5), -10, 60)

# Now lets stamp my logo and name on the virtual meter display... and "EasiFace" is my logo - you need your own!
myLogoL1 = "EasiFace"
for letterCounter, theta in zip(range(len(myLogoL1)), np.linspace(5 * np.pi / 8, 3 * np.pi / 8, len(myLogoL1))):
    logo1Letter = myLogoL1[letterCounter]
    logo1Character = text(text = logo1Letter, color = color.green, opacity = 1, align = "center", height = 0.2, pos = vector(2.1 * np.cos(theta), 2.1 * np.sin(theta) - 3, -0.035), axis = vector(1, 0, 0))
    logo1Character.rotate(angle = theta - np.pi / 2, axis = vector(0, 0, 1))
myLogoL2 = "MeterPanel" # Warning - I found that when this text had a space in it, it broke vPython.
for letterCounter, theta in zip(range(len(myLogoL2)), np.linspace(5 * np.pi / 8, 3 * np.pi / 8, len(myLogoL2))):
    logo2Letter = myLogoL2[letterCounter]
    logo2Character = text(text = logo2Letter, color = color.green, opacity = 1, align = "center", height = 0.2, pos = vector(1.9 * np.cos(theta), 1.8 * np.sin(theta) - 3, -0.035), axis = vector(1, 0, 0))
    logo2Character.rotate(angle = theta - np.pi / 2, axis = vector(0, 0, 1))
# Next, lets put a pyramid below the logo, just because we can.
pyramid(pos = vector(0, -2, 0), color = color.green, size = vector(0.5, 0.25, 0.25), axis = vector(0, 1, 0))
# Finally, lets mount it all on a dark gray metal panel and screw that onto the canvas.
box(color = color.gray(0.5), opacity = 1, texture = textures.metal, size = vector(7, 4.5, 0.1), pos = vector(0, -0.25, -0.2))
drawScrew(vector(-3.4, 1.9, -0.23))
drawScrew(vector(3.4, 1.9, -0.23))
drawScrew(vector(-3.4, -2.4, -0.23))
drawScrew(vector(3.4, -2.4, -0.23))

# Connect to the Arduino on the correct serial port!
if not pseudoDataMode: # We are not virtual meter testing with pseudo random data.
    serialOK = True
    try:
        # My Arduino happens to connect as serial port 'com3'. Yours may be different!
        arduinoDataStream = serial.Serial('com3', 115200)
        # Give the serial port time to connect.
        time.sleep(1)
    except serial.SerialException as err:
        serialOK = False
        # Put an error message on top of the virtual meters.
        serialErrorVisible = 0
        serialError = text(text = "-Serial Error-", color = color.red, opacity = serialErrorVisible, align = "center", height = 0.5, pos = vector(0, -0.25, 0.25), axis = vector(1, 0, 0))
        print("Serial Error: %s." % (str(err)[0].upper() + str(err)[1:])) # A cosmetic fix to uppercase the first letter of err.

# Initialise the sensor reading variables.
pot1Value = "-1" # Invalid.
tDHT11 = hDHT11 = tDHT22 = hDHT22 = "NAN" # Invalid.
# Initialise real world meter variables.
rgbLEDsArduino = "NAN" # Invalid.

# An infinite loop...
while True:
    # Set the vPython refresh rate.
    rate(vPythonRefreshRate)
    if not pseudoDataMode: # We are not virtual meter testing with pseudo random data.
        if serialOK:
            # Wait until all the data has been received from the Arduino.
            while arduinoDataStream.in_waiting == 0:
                rate(vPythonRefreshRate)
            # Read the CSV data from the Arduino.
            arduinoDataPacket = arduinoDataStream.readline()
            # Convert the CSV data from a byte stream to a CSV string.
            arduinoDataPacket = str(arduinoDataPacket, 'utf-8')
            # Strip the CRLF from the end of the CSV string.
            arduinoDataPacket = arduinoDataPacket.strip('\r\n')
            # Check if there is a CRC8 checksum.
            if "!" in arduinoDataPacket:
                # Convert the CSV string into data and CRC8 checksum parts.
                (sensorData, chksumCRC8) = arduinoDataPacket.split("!")
            else:
                sensorData = arduinoDataPacket      # Assuming we only have the sensor data.
                chksumCRC8 = calcCRC8(sensorData)   # No CRC8 checksum provided, so create one.
            # Split the sensor data if the CRC8 checksum passes.
            if chksumCRC8.isdigit() and calcCRC8(sensorData) == int(chksumCRC8):
                # Convert the sensorData string into separate variables.
                (pot1Value, tDHT11, hDHT11, tDHT22, hDHT22) = sensorData.split(",")
                # Check the returned data and convert the variables to numbers.
                # NaN is a valid float number value and means "not a number", i.e. the Arduino has no valid data for this measurement.
                if pot1Value != "-1":
                    pot1Value = int(pot1Value)
                if tDHT11 != "NAN":
                    tDHT11   = float(tDHT11)
                if hDHT11 != "NAN":
                    hDHT11   = float(hDHT11)
                if tDHT22 != "NAN":
                    tDHT22   = float(tDHT22)
                if hDHT22 != "NAN":
                    hDHT22   = float(hDHT22)
        else:
            # Flash the serial error message on top of the virtual meters.
            serialErrorVisible = (serialErrorVisible + 1) % 2 # Using modulo 2 maths to toggle the variable between 0 and 1.
            serialError.opacity = serialErrorVisible
            # Wait for a bit...
            time.sleep(0.5)
    else: # Get some pseudo random data to test the virtual meters.
        (pot1Value, tDHT11, hDHT11, tDHT22, hDHT22) = pseudoData()

    # Update the visual display with the latest sensor measurements.
    if pot1Value != "-1":
        pot1Voltage = round(5 * pot1Value / 1024, 2) # Calculate the voltage represented by this sensor value.
    else:
        pot1Voltage = "nan"
    voltageMeter1.update(pot1Voltage, pot1Value) # Send this virtual meter the calculated float voltage and the raw integer value.
    # Update these virtual meters less frequently if we are using pseudo random data.
    pseudoDataCounter = (pseudoDataCounter + 1) % 10 # More modulo maths. This time to reset a 0-9 counter.
    if not pseudoDataMode or pseudoDataCounter == 0:
        thermoMeter1.update(tDHT11)
        humidityMeter1.update(hDHT11)
        alertLEDs.update(tDHT11)
        thermoMeter2.update(tDHT22)
        humidityMeter2.update(hDHT22)
        alertLEDBank.update(tDHT22)

    # Update the real world, if it is connected.
    if not pseudoDataMode: # We are not virtual meter testing with pseudo random data.
        if serialOK:
            # Using the potentiometer voltage to drive the Arduino BGR LEDs.
            rgbLEDsArduinoUpdate = rgbLEDsAction(pot1Voltage, 1.5, 3.5) # The potentiometer value and 30%/70% thresholds.
            # Only send an update to the Arduino if the rgbLEDs status has changed from the last time.
            if rgbLEDsArduinoUpdate != rgbLEDsArduino:
                # Construct the command to send to the Arduino.
                arduinoCmd = "rgbLEDs=%d" % rgbLEDsArduinoUpdate    # This is the command (subject and action).
                chksumCRC8 = calcCRC8(arduinoCmd)                   # This is the CRC8 checksum of the command.
                arduinoCmd = "%s!%d\n" % (arduinoCmd, chksumCRC8)   # Put them together, separated by the delimiter, and terminate with a newline.
                # Encode and send the command to the Arduino. 
                arduinoDataStream.write(arduinoCmd.encode())
                # Update the current Arduino rgbLEDs status.
                rgbLEDsArduino = rgbLEDsArduinoUpdate

# EOF

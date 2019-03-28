#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Load .gtd files created by Gecko and the St. Olaf HF radar
Convert to the .mat ImpDAR file

Author:
Benjamin Hills
benjaminhhills@gmail.com
University of Washington
Earth and Space Sciences

Mar 28 2019





########
From original StoDeep script
########

% DESCRIPTION:
% Reads any data file created by the St. Olaf radar systems
%
% INPUT:
%   filename    String containing the filename that contain the data
%
% OUTPUT:
%   raw             An n x 1 array of structure containing the data, where
%                   n is the number of channels
%   rawinfo         A structure containing information about the data
%                   in the file
%
% REMARKS:
%
% EXAMPLES:
%
% AUTHOR:
% I. Campbell 6/21/05
% Department of Physics, St. Olaf College, MN, USA
%
% REVISION HISTORY:
% Renamed fields and fixed bugs, R. Pettersson  Nov. 2005
% At some point this was de-functionalized into a script (perhaps
% 2006-2007). Re-adapted to a new version of gekko (3.6). B. Youngblood and
% K. Lapo June 2010
% Change in type for metadata.nominal frequency added by RWJ for
% Version 3.8 in September 2013.

"""

import numpy as np
from datetime import date
from .RadarData import RadarData, RadarFlags

class gecko(RadarData):
    def __init__(self, fn, channel=1):
        with open(fn, 'rb') as fid:
            # get the length of the file
            fid.seek(0,2)     # go to the file end.
            eof = fid.tell()   # get the end of file location
            fid.seek(0,0)      # go back to file beginning
            # ------------------------------------------------------------------------
            ### File Header ###
            self.Version = np.fromfile(fid, np.int16, 1)[0]/100
            # File Name ends in NULL character
            self.Filename = fid.read(64)
            # Decimal day from 1 Jan 1970 We add an offset to 1 Jan 1970
            self.Serialtime = np.fromfile(fid,np.float64,1)[0] + date(1970,1,1).toordinal()
            self.Timezone = int(np.fromfile(fid,np.int16,1)[0])//1440
            # number of recorded channels
            self.chan = channel
            self.nChannels = np.fromfile(fid,np.uint8,1)[0]
            # Acquistition method (0 = Odometer, 1 = Stacks, 2 = Time)
            self.RecordMode = np.fromfile(fid,np.uint8,1)[0]
            if self.RecordMode == 0:
                self.RecordModeString = 'Odometer'
            elif self.RecordMode == 1:
                self.RecordModeString = 'Stacks'
            elif self.RecordMode == 2:
                self.RecordModeString = 'Time'
            else:
                Warning('Unkown Record Mode')
            # Recording interval, when the recording method is stacks this is 0,
            # otherwise is is the distance/time settings triggering a new trace
            self.RecordInterval = np.fromfile(fid, np.int16, 1)[0]
            self.NumberOfStacks = np.fromfile(fid, np.int16, 1)[0]
            self.SampFreq = np.fromfile(fid, np.int16, 1)[0]*1e6
            self.dt = 1./self.SampFreq
            self.PreTriggerDepth = np.fromfile(fid, np.int16, 1)[0]
            self.PostTriggerDepth = np.fromfile(fid, np.int16, 1)[0]
            self.snum = self.PreTriggerDepth + self.PostTriggerDepth
            #Trigger source (1 = Chan A, 2 = Chan B, -1 = External)
            self.TriggerSource = np.fromfile(fid, np.int8, 1)[0]
            if self.TriggerSource == 1:
                self.triggersourceString = 'Channel A'
            elif self.TriggerSource == 2:
                self.triggersourceString = 'Channel B'
            elif self.TriggerSource == -1:
                self.triggersourceString = 'External'
            else:
                Warning('Unkown in Trigger Source')
            # Trigger slope (0 = positive, 1 = negative)
            self.TriggerSlope = np.fromfile(fid, np.uint8, 1)[0]
            if self.TriggerSlope == 0:
                self.TriggerSlopeString = 'Positive'
            elif self.TriggerSlope == 1:
                self.TriggerSlopeString = 'Negative'
            else:
                Warning('Unkown Trigger Slope')
            # External Trigger range (Full range in in mV)
            self.ExtTriggerRange = np.fromfile(fid, np.int16, 1)[0]
            # External trigger coupling (0 = DC, 1 = AC)
            self.ExtTriggerCoupling = np.fromfile(fid,np.uint8,1)[0]
            if self.ExtTriggerCoupling == 0:
                self.ExtTriggerCouplingString = 'DC'
            elif self.ExtTriggerCoupling == 1:
                self.ExtTriggerCouplingString = 'AC'
            else:
                Warning('Unknown External Trigger Coupling')
            # Odometer calibration constant(meters per trigger)
            if self.Version < 3.21:
                self.OdometerCalibration = np.fromfile(fid,np.int16,1)[0]
            # Nominal Freqiency (MHz)
            # (Change of type in Version 3.8, N.B. this adds 2 bytes to header length)
            if self.Version < 3.8:
                self.NominalFrequency = np.fromfile(fid,np.int16,1)[0]
            else:
                self.NominalFrequency = np.fromfile(fid,np.float32,1)[0]
            # Antenna separation (m)
            self.AntennaSeparation = np.fromfile(fid,np.float32,1)[0]
            # Read and toss extra blank spaceor
            # Only needed for pre 3.6 version
            if self.Version < 3.6:
                buffer = np.fromfile(fid,np.int8,27)

            # ------------------------------------------------------------------------
            ### Channel Headers ###

            for nn in range(self.nChannels):
                # Channel number
                nChan = np.fromfile(fid,np.uint8,1)[0]
                if nChan != (nn+1):
                    raise TypeError('Corrupt Channel header, %s instead of %s'%(nChan,nn+1))
                if nn == 0:
                    self.ChName = np.empty((self.nChannels)).astype(str)
                    self.VoltRange = np.empty((self.nChannels))
                    self.Impedance = np.empty((self.nChannels))
                    self.ImpedanceString = np.empty((self.nChannels)).astype(str)
                    self.Coupling = np.empty((self.nChannels))
                    self.CouplingString = np.empty((self.nChannels)).astype(str)
                # Construct channel name
                self.ChName[nn] = 'Channel' + str(nChan)
                # Voltage Range
                self.VoltRange[nn] = np.fromfile(fid,np.int16,1)[0]
                # Channel Impedance (0 = 50 Ohm, 1 = 1 MOhm)
                self.Impedance[nn] = np.fromfile(fid,np.uint8,1)[0]
                if self.Impedance[nn] == 0:
                    self.ImpedanceString[nn] = '1 MOhm'
                elif self.Impedance[nn] == 1:
                    self.ImpedanceString[nn] = '50 Ohm'
                else:
                    Warning('Unknown Impedance for',self.ChName[nn])
                # Channel coupling (0 = DC, 1 = AC)
                self.Coupling[nn] = np.fromfile(fid,np.uint8,1)[0]
                if self.Coupling[nn] == 0:
                    self.CouplingString[nn] = 'DC'
                elif self.Coupling[nn] == 1:
                    self.CouplingString[nn] = 'AC'
                else:
                    Warning('Unknown Coupling for',self.ChName[nn])
                # Read and toss extra blank space
                # Only needed for pre 3.6 version
                if self.Version < 3.6:
                    buffer = np.fromfile(fid,np.int8,27)

            # ------------------------------------------------------------------------
            ### Trace Headers and Data ###

            # Travel time
            self.travel_time = np.arange(-self.PreTriggerDepth,
                                         self.PostTriggerDepth)*1./self.SampFreq
            # Set trace counter
            nTrc = 0
            while fid.tell() < eof:
                nTrc += 1
                if nTrc%100 == 0:
                    print(fn)
                    print('Loading... Trace #',nTrc)
                    print(fid.tell(),eof,self.nChannels)
                # Preallocate the arrays
                if nTrc == 1:
                    self.trace_num = np.array([])
                    self.decday = np.array([])
                    self.trace_int = np.array([])
                    self.trig_level = np.array([])
                    self.Odometer = np.array([])
                    self.pressure = np.array([])
                    self.lat = np.array([])
                    self.long = np.array([])
                    self.elev = np.array([])
                    self.GPSResolution = np.array([])
                    self.data = np.empty((0,self.snum))
                for nn in range(self.nChannels):
                    # Read Trace header type (0 = Trace, 1 = Marker, 2 = Comment)
                    nHeaderType = np.fromfile(fid,np.uint8,1)
                    # Recording channel number
                    nChan = np.fromfile(fid,np.uint8,1)[0]
                    if nChan != nn+1:
                        raise TypeError('Corrupt Channel header, %s instead of %s'%(nChan,nn+1))
                    # Trace number in file set
                    trace_num = np.fromfile(fid,np.int32,1)[0]
                    # We add an offset to 1 Jan 1970 to get MATLAB date numbers
                    decday = np.fromfile(fid,np.float64,1)[0] + date(1970,1,1).toordinal()
                    # Stacks/trace
                    # Unless record mode is stacks, then it is time/trace
                    trace_int = np.fromfile(fid,np.float32,1)[0]
                    # Trigger level in percentage of input range in mV
                    trig_level = np.fromfile(fid,np.int16,1)[0]
                    # This is a bug that was fixed since no versions have ever used
                    # an odometer or pressure reading. 3.6 and beyond do not use
                    # these fields.
                    if self.Version < 3.21:
                        # Odometer readings (0 if no Odometer is used)
                        Odometer = np.fromfile(fid,np.float32,1)[0]
                        # Pressure gauge (0 if no pressure gauge is used)
                        pressure = np.fromfile(fid,np.float32,1)[0]
                    # GPS Lat/Long/elev
                    lat = np.fromfile(fid,np.float64,1)[0]
                    long = np.fromfile(fid,np.float64,1)[0]
                    elev = np.fromfile(fid,np.float32,1)[0]
                    # GPS accuracy
                    GPSResolution = np.fromfile(fid,np.float32,1)[0]
                    # Read and toss last blank bytes
                    # (Only needed for pre 3.6 version)
                    if self.Version < 3.6:
                        if self.Version < 3.2:
                            buffer = np.fromfile(fid,np.int8,12)
                        else:
                            buffer = np.fromfile(fid,np.int8,14)
                    # If it is actual radar data, not a comment or marker
                    if nHeaderType == 0:
                        # Read the trace data
                        newdata = np.fromfile(fid,np.int16,self.snum)
                    elif nHeaderType == 1:
                        # Read marker number
                        nNumber = np.fromfile(fid,np.int16,1)
                        # Read trace number
                        buffer = np.fromfile(fid,np.int32,1)
                        # We add an offset to 1 Jan 1970 to get MATLAB date numbers
                        buffer = np.fromfile(fid,np.float64,1) + date(1970,1,1);
                        # GPS Latitude
                        buffer = np.fromfile(fid,np.float64,1)
                        # GPS longitude
                        buffer = np.fromfile(fid,np.float64,1)
                        # GPS altitude
                        buffer = np.fromfile(fid,np.float32,1)
                        # GPS altitude
                        buffer = np.fromfile(fid,np.float32,1)
                        # Break the channel loop and restart
                        break
                    # These variables are only recorded accurately on the first channel
                    if nn+1 == 1:
                        self.trace_num = np.append(self.trace_num,trace_num)
                        self.decday = np.append(self.decday,decday)
                        self.trace_int = np.append(self.trace_int,trace_int)
                        self.trig_level = np.append(self.trig_level,trig_level)
                        if self.Version < 3.21:
                            self.Odometer = np.append(self.Odometer,Odometer)
                            self.pressure = np.append(self.pressure,pressure)
                        self.lat = np.append(self.lat,lat)
                        self.long = np.append(self.long,long)
                        self.elev = np.append(self.elev,elev)
                        self.GPSResolution = np.append(self.GPSResolution,GPSResolution)
                    # If on the desired output channel then write to the class instance
                    if nn+1 == self.chan:
                        # Store data
                        self.data = np.append(self.data,[newdata],axis=0)

            # -----------------------------------------------------------------------------
            ### Finalize output ###

            # transpose
            self.data = np.transpose(self.data)
            # other variables are from the array shape
            self.tnum = self.data.shape[1]
            self.trig_level = np.zeros((self.tnum,))
            if self.Version >= 3.6:
                self.pressure = np.zeros((self.tnum,))
            try:
                self.flags = RadarFlags()
            except:
                self.flags = None
            self.x_coord = np.zeros((self.tnum,))
            self.y_coord = np.zeros((self.tnum,))
            self.dist = np.arange(self.tnum)
            self.trig = np.zeros((self.tnum,))

            for attr in ['chan','data', 'decday', 'dist', 'dt', 'elev', 'flags', 'lat', 'long', 'pressure', 'snum', 'tnum', 'trace_int', 'trace_num', 'travel_time', 'trig', 'trig_level', 'x_coord', 'y_coord']:
                if getattr(self, attr) is None:
                    print(attr + ' is not defined')
                    setattr(self, attr, 0)

# -----------------------------------------------------------------------------

def load_gecko(fn, *args, **kwargs):
    return gecko(fn)

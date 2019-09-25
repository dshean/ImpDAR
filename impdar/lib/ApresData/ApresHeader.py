#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 David Lilien <dlilien90@gmail.com>
#
# Distributed under terms of the GNU GPL3 license.

"""
Header for ApRES data

This code is based on a series of Matlab scripts from Craig Stewart,
Keith Nicholls, and others.
The ApRES (Automated phase-sensitive Radio Echo Sounder) is a self-contained
instrument from BAS.

Author:
Benjamin Hills
bhills@uw.edu
University of Washington
Earth and Space Sciences

Sept 23 2019

"""

import numpy as np
import re

# --------------------------------------------------------------------------------------------

class ApresHeader():
    """
    Class for parameters from the header file.
    """
    def __init__(self):
        """Initialize data paramaters"""
        self.fsysclk = 1e9
        self.fs = 4e4

    # --------------------------------------------------------------------------------------------

    def read_header(self,fn_apres,max_header_len=2000):
        """
        Read the header string, to be partitioned later

        Parameters
        ---------
        fn_apres: string
            file name to update with
        max_header_len: int
            maximum length of header to read (can be too long)

        Output
        ---------
        """
        fid = open(fn_apres,'rb')
        self.header = str(fid.read(max_header_len))
        fid.close()

    # --------------------------------------------------------------------------------------------

    def file_format(self):
        """
        Determine fmcw file format from burst header using keyword presence
        There are a few different formats through the years.

        ### Original Matlab script Notes ###
        Craig Stewart
        2013-10-20
        Updated by Keith Nicholls, 2014-10-22: RMB2
        """

        if 'SW_Issue=' in self.header: # Data from RMB2 after Oct 2014
            self.fileformat = 5
        elif 'SubBursts in burst:' in self.header: # Data from after Oct 2013
            self.file_format = 4
        elif '*** Burst Header ***' in self.header: # Data from Jan 2013
            self.file_format = 3
        elif 'RADAR TIME' in self.header: # Data from Prototype FMCW radar (nov 2012)
            self.file_format = 2
        else:
            TypeError('Unknown file format - check file')

    def update_parameters(self):
        """
        Update the parameters with the apres file header


        ### Original Matlab Notes ###
        Extract from the hex codes the actual paramaters used by RMB2
        The contents of config.ini are copied into a data header.
        Note this script assumes that the format of the hex codes have quotes
        e.g. Reg02="0D1F41C8"

        Checks for a sampling frequency of 40 or 80 KHz.  Apart from Lai Bun's
        variant (WDC + Greenland) it could be hard coded to 40 KHz.

        However, there is no check made by the system that the N_ADC_SAMPLES
        matches the requested chirp length

        NOT COMPLETE - needs a means of checking for profile mode, where multiple sweeps
        per period are transmitted- see last line
        """

        loc1 = [m.start() for m in re.finditer('Reg0', self.header)]
        loc2 = [m.start() for m in re.finditer('="', self.header)]

        for k in range(len(loc1)):
            case = self.header[loc1[k]:loc2[k]]

            if case == 'Reg01':
                # Control Function Register 2 (CFR2) Address 0x01 Four bytes
                # Bit 19 (Digital ramp enable)= 1 = Enables digital ramp generator functionality.
                # Bit 18 (Digital ramp no-dwell high) 1 = enables no-dwell high functionality.
                # Bit 17 (Digital ramp no-dwell low) 1 = enables no-dwell low functionality.
                # With no-dwell high, a positive transition of the DRCTL pin initiates a positive slope ramp, which
                # continues uninterrupted (regardless of any activity on the DRCTL pin) until the upper limit is reached.
                # Setting both no-dwell bits invokes a continuous ramping mode of operation;
                loc3 = self.header[loc2[k]+2:].find('"')
                val = self.header[loc2[k]+2:loc2[k]+loc3+2]
                val = bin(int(val, 16))
                val = val[::-1]
                self.noDwellHigh = int(val[18])
                self.noDwellLow = int(val[17])

            #elif case == 'Reg08':
            #    # Phase offset word Register (POW) Address 0x08. 2 Bytes dTheta = 360*POW/2^16.
            #    val = char(reg{1,2}(k));
            #    H.phaseOffsetDeg = hex2dec(val(1:4))*360/2^16;

            elif case == 'Reg0B':
                # Digital Ramp Limit Register Address 0x0B
                # Digital ramp upper limit 32-bit digital ramp upper limit value.
                # Digital ramp lower limit 32-bit digital ramp lower limit value.
                loc3 = self.header[loc2[k]+2:].find('"')
                val = self.header[loc2[k]+2:loc2[k]+loc3+2]
                self.startFreq = int(val[8:], 16)*self.fsysclk/(2**32)
                self.stopFreq = int(val[:8], 16)*self.fsysclk/(2**32)

            elif case == 'Reg0C':
                # Digital Ramp Step Size Register Address 0x0C
                # Digital ramp decrement step size 32-bit digital ramp decrement step size value.
                # Digital ramp increment step size 32-bit digital ramp increment step size value.
                loc3 = self.header[loc2[k]+2:].find('"')
                val = self.header[loc2[k]+2:loc2[k]+loc3+2]
                self.rampUpStep = int(val[8:], 16)*self.fsysclk/(2**32)
                self.rampDownStep = int(val[:8], 16)*self.fsysclk/(2**32)

            elif case == 'Reg0D':
                # Digital Ramp Rate Register Address 0x0D
                # Digital ramp negative slope rate 16-bit digital ramp negative slope value that defines the time interval between decrement values.
                # Digital ramp positive slope rate 16-bit digital ramp positive slope value that defines the time interval between increment values.
                loc3 = self.header[loc2[k]+2:].find('"')
                val = self.header[loc2[k]+2:loc2[k]+loc3+2]
                self.tstepUp = int(val[4:], 16)*4/self.fsysclk
                self.tstepDown = int(val[:4], 16)*4/self.fsysclk

        strings = ['SamplingFreqMode=','N_ADC_SAMPLES=']
        output = np.empty((len(strings))).astype(str)
        for i,string in enumerate(strings):
            if string in self.header:
                search_start = self.header.find(string)
                search_end = self.header[search_start:].find('\\')
                output[i] = self.header[search_start+len(string):search_end+search_start]

        self.fs = output[0]
        if self.fs == 1:        # if self.fs > 70e3:
            self.fs = 8e4       #     self.fs = 80e3
        else:                   # else
            self.fs = 4e4       #     self.fs = 40e3

        self.snum = int(output[1])

        self.nstepsDDS = round(abs((self.stopFreq - self.startFreq)/self.rampUpStep)) # abs as ramp could be down
        self.chirpLength = int(self.nstepsDDS * self.tstepUp)
        self.nchirpSamples = round(self.chirpLength * self.fs)

        # If number of ADC samples collected is less than required to collect
        # entire chirp, set chirp length to length of series actually collected
        if self.nchirpSamples > self.snum:
            self.chirpLength = self.snum / self.fs

        self.K = 2.*np.pi*(self.rampUpStep/self.tstepUp) # chirp gradient (rad/s/s)
        if self.stopFreq > 400e6:
            self.rampDir = 'down'
        else:
            self.rampDir = 'up'

        if self.noDwellHigh and self.noDwellLow:
            self.rampDir = 'upDown'
            self.nchirpsPerPeriod = np.nan # self.nchirpSamples/(self.chirpLength)



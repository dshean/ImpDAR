#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 David Lilien <dlilien90@gmail.com>
#
# Distributed under terms of the GNU GPL-3.0 license.

"""
An alternative ImpDAR class for ApRES data.
This should be considered separate from impulse data.
This class has a different set of loading and filtering scripts.

Author:
Benjamin Hills
bhills@uw.edu
University of Washington
Earth and Space Sciences

Sept 24 2019

"""


import datetime
import numpy as np
from scipy.io import loadmat
from .ApresFlags import ApresFlags
from ..ImpdarError import ImpdarError

class ApresData(object):
    """A class that holds the relevant information for an ApRES acquisition.

    We keep track of processing steps with the flags attribute.
    This base version's __init__ takes a filename of a .mat file in the old StODeep format to load.
    """
    #: Attributes that every ApresData object should have and should not be None.
    attrs_guaranteed = ['data',
                        'decday',
                        'dt',
                        'lat',
                        'long',
                        'snum',
                        'tnum',
                        'trace_num',
                        'travel_time']

    #: Optional attributes that may be None without affecting processing.
    #: These may not have existed in old StoDeep files that we are compatible with,
    #: and they often cannot be set at the initial data load.
    #: If they exist, they all have units of meters.
    attrs_optional = ['x_coord',
                      'y_coord',
                      'elev',
                      'fn',
                      'file_read_code']

    # TODO: add imports
    #from ._ApresDataProcessing import
    #from ._ApresDataSaving import

    # Now make some load/save methods that will work with the matlab format
    def __init__(self, fn_mat):
        if fn_mat is None:
            # Write these out so we can document them
            # Very basics
            self.snum = None  #: int number of samples per trace
            self.tnum = None  #: int, the number of traces in the file
            self.data = None  #: np.ndarray(snum x tnum) of the actual return power
            self.dt = None  #: float, The spacing between samples in travel time, in seconds

            # Per-trace attributes
            #: np.ndarray(tnum,) of the acquisition time of each trace
            #: note that this is referenced to Jan 1, 0 CE (matlabe datenum)
            #: for convenience, use the `datetime` attribute to access a python version of the day
            self.decday = None
            #: np.ndarray(tnum,) latitude along the profile. Generally not in projected coordinates
            self.lat = None
            #: np.ndarray(tnum,) longitude along the profile. Generally not in projected coords.
            self.long = None
            self.trace_num = None  #: np.ndarray(tnum,) The 1-indexed number of the trace

            # Sample-wise attributes
            #: np.ndarray(snum,) The two way travel time to each sample, in us
            self.travel_time = None

            # Optional attributes
            #: str, the input filename. May be left as None.
            self.fn = None
            #: int, the read code. Gives different values based on the success of the read.
            self.file_read_code = None
            #: np.ndarray(tnum,) Optional. Projected x-coordinate along the profile.
            self.x_coord = None
            #: np.ndarray(tnum,) Optional. Projected y-coordinate along the profile.
            self.y_coord = None
            #: np.ndarray(tnum,) Optional. Elevation along the profile.
            self.elev = None

            # Special attributes
            #: impdar.lib.RadarFlags object containing information about the processing steps done.
            self.flags = ApresFlags()

            self.data_dtype = None
            return

        # TODO: add a matlab load
        mat = loadmat(fn_mat)
        for attr in self.attrs_guaranteed:
            if mat[attr].shape == (1, 1):
                setattr(self, attr, mat[attr][0][0])
            elif mat[attr].shape[0] == 1 or mat[attr].shape[1] == 1:
                setattr(self, attr, mat[attr].flatten())
            else:
                setattr(self, attr, mat[attr])
        # We may have some additional variables
        for attr in self.attrs_optional:
            if attr in mat:
                if mat[attr].shape == (1, 1):
                    setattr(self, attr, mat[attr][0][0])
                elif mat[attr].shape[0] == 1 or mat[attr].shape[1] == 1:
                    setattr(self, attr, mat[attr].flatten())
                else:
                    setattr(self, attr, mat[attr])
            else:
                setattr(self, attr, None)

        self.data_dtype = self.data.dtype

        self.fn = fn_mat
        self.flags = ApresFlags()
        self.flags.from_matlab(mat['flags'])
        self.check_attrs()

    def check_attrs(self):
        """Check if required attributes exist.

        This is largely for development only; loaders should generally call this method last,
        so that they can confirm that they have defined the necessary attributes.

        Raises
        ------
        ImpdarError
            If any required attribute is None or any optional attribute is fully absent"""
        for attr in self.attrs_guaranteed:
            if not hasattr(self, attr):
                raise ImpdarError('{:s} is missing. \
                    It appears that this is an ill-defined RadarData object'.format(attr))
            if getattr(self, attr) is None:
                raise ImpdarError('{:s} is None. \
                    It appears that this is an ill-defined RadarData object'.format(attr))

        for attr in self.attrs_optional:
            if not hasattr(self, attr):
                raise ImpdarError('{:s} is missing. \
                    It appears that this is an ill-defined RadarData object'.format(attr))

        if not hasattr(self, 'data_dtype') or self.data_dtype is None:
            self.data_dtype = self.data.dtype
        return

    @property
    def datetime(self):
        """A python operable version of the time of acquisition of each trace"""
        return np.array([datetime.datetime.fromordinal(int(dd)) + datetime.timedelta(days=dd % 1) - datetime.timedelta(days=366)
                         for dd in self.decday], dtype=np.datetime64)




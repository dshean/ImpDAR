#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 dlilien <dlilien@berens>
#
# Distributed under terms of the MIT license.

"""

"""
import os
import unittest
import numpy as np
from impdar.lib import load

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestLoad(unittest.TestCase):

    def test_load_mat(self):
        data = load.load_mat(os.path.join(THIS_DIR, 'input_data', 'small_data.mat'))
        self.assertEqual(data.data.shape, (20, 40))

    def test_loadmat(self):
        data = load.load('mat', os.path.join(THIS_DIR, 'input_data', 'small_data.mat'))
        self.assertEqual(data[0].data.shape, (20, 40))

    def test_loadgssi(self):
        data = load.load('gssi', os.path.join(THIS_DIR, 'input_data', 'test_gssi.DZT'))

    def test_loadpe(self):
        data = load.load('pe', os.path.join(THIS_DIR, 'input_data', 'test_pe.DT1'))

    def test_loadbad(self):
        with self.assertRaises(ValueError):
            data = load.load('bad', os.path.join(THIS_DIR, 'input_data', 'small_data.bad'))

    def test_load_and_exitmat(self):
        data = load.load_and_exit('mat', os.path.join(THIS_DIR, 'input_data', 'small_data.mat'), o=os.path.join(THIS_DIR, 'input_data', 'small_data_rawrrr.mat'))
        self.assertTrue(os.path.exists(os.path.join(THIS_DIR, 'input_data', 'small_data_rawrrr.mat')))

    def test_load_and_exitcustomfn(self):
        data = load.load_and_exit('mat', os.path.join(THIS_DIR, 'input_data', 'small_data.mat'))
        self.assertTrue(os.path.exists(os.path.join(THIS_DIR, 'input_data', 'small_data_raw.mat')))

    def test_load_and_exiterror(self):
        # We are blocking multiple outputs with o kwarg
        with self.assertRaises(ValueError):
            load.load_and_exit('mat', [os.path.join(THIS_DIR, 'input_data', 'small_data.mat'), os.path.join(THIS_DIR, 'input_data', 'small_data.mat')], o='dummy')

    def tearDown(self):
        if os.path.exists(os.path.join(THIS_DIR, 'input_data', 'small_data_raw.mat')):
            os.remove(os.path.join(THIS_DIR, 'input_data', 'small_data_raw.mat'))
        if os.path.exists(os.path.join(THIS_DIR, 'input_data', 'small_data_rawrrr.mat')):
            os.remove(os.path.join(THIS_DIR, 'input_data', 'small_data_rawrrr.mat'))


if __name__ == '__main__':
    unittest.main()

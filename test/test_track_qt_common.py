#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import track_qt

def test_change_emitter():
    class mock:
        pass
    m = mock()
    ce = track_qt.change_emitter(m)

def test_matrix_table_model():
    mtm = track_qt.matrix_table_model(None)

if __name__ == '__main__':
    test_change_emitter()
    test_matrix_table_model()
    


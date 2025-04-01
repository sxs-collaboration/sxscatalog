# SPDX-FileCopyrightText: 2025-present Mike Boyle <michael.oliver.boyle@gmail.com>
#
# SPDX-License-Identifier: MIT

def test_import():
    import sxscatalog
    assert sxscatalog.__version__

def test_load_simulations():
    import sxscatalog
    sxscatalog.load("simulations")

def test_load_simulations_tagged():
    import sxscatalog
    sxscatalog.load("simulations", tag="3.0.0a4")

def test_load_dataframe():
    import sxscatalog
    sxscatalog.load("dataframe")

def test_load_dataframe_tagged():
    import sxscatalog
    sxscatalog.load("dataframe", tag="3.0.0a4")

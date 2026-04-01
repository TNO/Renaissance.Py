change_comment = """#!/usr/bin/env python
# -----------------------------------------------------------------------------#
#                                                                             #
#                                 Python script                               #
#                                                                             #
# -----------------------------------------------------------------------------#
#
# Ident         : ABCD_utils.py
# Description   : Utility functions for unittest
#
# History
# 2016-03-31    : xx
# 2016-06-01    : yy
# 2016-08-10    : zz
# -----------------------------------------------------------------------------#
#                                                                             #
#                   Copyright (c) 2016, ABCD Netherlands B.V.                 #
#                               All rights reserved                           #
#                                                                             #
# -----------------------------------------------------------------------------#

import inspect
"""

new_change_comment = """#!/usr/bin/env python
# -----------------------------------------------------------------------------#
#                                                                             #
#                                 Python script                               #
#                                                                             #
# -----------------------------------------------------------------------------#
#
# Ident         : ABCD_utils.py
# Description   : Utility functions for unittest
#
# History
# 2016-03-31    : xx
# 2016-06-01    : yy
# 2016-08-10    : zz
# 2026-01-22    : uu
# -----------------------------------------------------------------------------#
#                                                                             #
#                   Copyright (c) 2016, ABCD Netherlands B.V.                 #
#                               All rights reserved                           #
#                                                                             #
# -----------------------------------------------------------------------------#

import inspect
"""
set_up = """
def setUp(self):
    self._patch_readout_data_filler = mock.patch("ACBD_ReadoutDataFiller.ReadoutDataFiller")
    self._patch_readout_data_publisher = mock.patch("ACBD_ReadoutDataPublisher.ReadoutDataPublisher")
    self._patch_dt_context_rep = mock.patch("ACBDxRepUtils.DPxCONTEXT")
    self._patch_dtxa_context_rep = mock.patch("ACBDxRepUtils.DTXAxCONTEXT")
    self._patch_dt_context_filler = mock.patch("ACBD_ReadoutDataFiller.DPxCONTEXT")
    self._patch_dtxa_context_filler = mock.patch("ACBD_ReadoutDataFiller.DTXAxCONTEXT")

    _ = self._patch_readout_data_filler.start()
    _ = self._patch_readout_data_publisher.start()
    _ = self._patch_dtxa_context_rep.start()
    _ = self._patch_dtxa_context_filler.start()
    mock_dt_context_rep = self._patch_dt_context_rep.start()
    mock_dt_context_filler = self._patch_dt_context_filler.start()

    mock_dt_context_rep.lookup_instance.return_value = (True, 1)
    mock_dt_context_filler.lookup_instance.return_value = (True, 2)

    ACBDxAPxData.data = ACBDxAPxData.ACBDxAPxData()
    ACBDxAPxData.data.initialize_engine(ACBDxEngine.ACBDxEngine())
    self.engine_stub = ACBDxEngine_stub()
    self.wh_stub = EMxWLxCTL_stub()
    self.vipr_stub = VIPS_stub()
    self.doubles = []
    
    context_stub = ACBDxCONTEXT.ACBDxCONTEXTStub()
    self.doubles.append(TAUT.TestDoubles(acbdxcontext=context_stub))
    self.doubles.append(
        TAUT.TestDoubles(module=ACBDxAPxData.data.rep, context=context_stub)
    )
    self.doubles.append(
        TAUT.TestDoubles(
            module=EMxWLxCTL.EMxWLxCTL, reload_wafer=self.wh_stub.reload_wafer
        )
    )
    self.doubles.append(
        TAUT.TestDoubles(
            module=ACBDxEngine.ACBDxEngine,
            measure_wafer=self.engine_stub.measure_wafer_gw,
        )
    )
    self.doubles.append(
        TAUT.TestDoubles(module=VIPS, check_stopped=self.vipr_stub.check_stopped)
    )
    
    ACBDxAPxData.data.adv_wp = ACBDxADVxWP.input()
    self.measurement_strategy = ACBD_MeasurementDefault.ACBD_MeasurementDefault()
"""
new_set_up = """
def setUp(self):
    self._patch_readout_data_filler = mock.patch("ACBD_ReadoutDataFiller.ReadoutDataFiller")
    self._patch_readout_data_publisher = mock.patch("ACBD_ReadoutDataPublisher.ReadoutDataPublisher")
    self._patch_dt_context_rep = mock.patch("ACBDxRepUtils.DPxCONTEXT")
    self._patch_dtxa_context_rep = mock.patch("ACBDxRepUtils.DTXAxCONTEXT")
    self._patch_dt_context_filler = mock.patch("ACBD_ReadoutDataFiller.DPxCONTEXT")
    self._patch_dtxa_context_filler = mock.patch("ACBD_ReadoutDataFiller.DTXAxCONTEXT")

    _ = self._patch_readout_data_filler.start()
    _ = self._patch_readout_data_publisher.start()
    _ = self._patch_dtxa_context_rep.start()
    _ = self._patch_dtxa_context_filler.start()
    mock_dt_context_rep = self._patch_dt_context_rep.start()
    mock_dt_context_filler = self._patch_dt_context_filler.start()

    mock_dt_context_rep.lookup_instance.return_value = (True, 1)
    mock_dt_context_filler.lookup_instance.return_value = (True, 2)

    ACBDxAPxData.data = ACBDxAPxData.ACBDxAPxData()
    ACBDxAPxData.data.initialize_engine(ACBDxEngine.ACBDxEngine())
    self.engine_stub = ACBDxEngine_stub()
    self.wh_stub = EMxWLxCTL_stub()
    self.vipr_stub = VIPS_stub()
    self.patches = []

    self.context_stub = ACBDxCONTEXT.ACBDxCONTEXTStub()
    self.patches.append(patch('ACBDxCONTEXT.acbdxcontext', self.context_stub))
    self.patches.append(patch.object(ACBDxAPxData.data.rep, 'context', self.context_stub))
    self.patches.append(patch.object(EMxWLxCTL.EMxWLxCTL, 'reload_wafer', self.wh_stub.reload_wafer))
    self.patches.append(patch.object(ACBDxEngine.ACBDxEngine, 'measure_wafer', self.engine_stub.measure_wafer_gw))
    self.patches.append(patch.object(VIPS, 'check_stopped', self.vipr_stub.check_stopped))
    for p in self.patches:
        p.start()

    ACBDxAPxData.data.adv_wp = ACBDxADVxWP.input()
    self.measurement_strategy = ACBD_MeasurementDefault.ACBD_MeasurementDefault()
"""

tear_down = """
def tearDown(self):
    self._patch_readout_data_filler.stop()
    self._patch_readout_data_publisher.stop()
    self._patch_dt_context_rep.stop()
    self._patch_dtxa_context_rep.stop()
    self._patch_dt_context_filler.stop()
    self._patch_dtxa_context_filler.stop()
    for double in self.doubles:
        double.exit()
"""

new_tear_down = """
def tearDown(self):
    ABCDxCONTEXT.abcdxcontext.reset_method_attributes("start_wafer")
    ABCDxCONTEXT.abcdxcontext.reset_method_attributes("finish_wafer")
    ABCDxCONTEXT.abcdxcontext.reset_method_attributes("start_lot")
    ABCDxCONTEXT.abcdxcontext.reset_method_attributes("finish_lot")
    
    self._patch_readout_data_filler.stop()
    self._patch_readout_data_publisher.stop()
    self._patch_dt_context_rep.stop()
    self._patch_dtxa_context_rep.stop()
    self._patch_dt_context_filler.stop()
    self._patch_dtxa_context_filler.stop()
    patch.stopall()
"""

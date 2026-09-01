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

tear_down_simple = """
def tearDown(self):
    for double in self.doubles:
        double.exit()
"""
tear_down_simple_new = """
def tearDown(self):
    for p in self.patches:
        p.stop()
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

set_up_common = """def setUpCommon(self):
        self.tds = [
            TestDoubles(abcdxread=ImprovedStub(ABCDxREAD.abcdxread)),
            TestDoubles(abcdxws=ImprovedStub(ABCDxWS.abcdxws)),
            TestDoubles(abxstream2=ImprovedStub(ABxSTREAM2.abxstream2)),
            TestDoubles(bcxclear=ImprovedStub(BCxCLEAR.bcxclear)),
            TestDoubles(bcxload=ImprovedStub(BCxLOAD.bcxload))
        ]
        self.sut = ABCDxVIPCxAB.ABCDxVIPCxAB()"""

set_up_common_new = """def setUpCommon(self):
        ImprovedStub.ret_vals = {}
        ImprovedStub.ret_vals_ex = {}
        ImprovedStub.call_logs = {}
        ImprovedStub.store_args = {}

        self.abcdxread = ImprovedStub(ABCDxREAD.abcdxread)
        self.abcdxws = ImprovedStub(ABCDxWS.abcdxws)
        self.abxstream2 = ImprovedStub(ABxSTREAM2.abxstream2)
        self.bcxclear = ImprovedStub(BCxCLEAR.bcxclear)
        self.bcxload = ImprovedStub(BCxLOAD.bcxload)
        self.patchers = [
            patch.object(ABCDxREAD, 'abcdxread', self.abcdxread),
            patch.object(ABCDxWS, 'abcdxws', self.abcdxws),
            patch.object(ABxSTREAM2, 'abxstream2', self.abxstream2),
            patch.object(BCxCLEAR, 'bcxclear', self.bcxclear),
            patch.object(BCxLOAD, 'bcxload', self.bcxload),
        ]

        for p in self.patchers:
            p.start()

        self.sut = ABCDxVIPCxAB.ABCDxVIPCxAB()"""

tear_down_common = """def tearDownCommon(self):
    for td in self.tds:
        td.exit()"""
tear_down_common_new = """def tearDownCommon(self):
    for p in self.patchers:
        try:
            p.stop()
        except RuntimeError:
            pass
"""

insert_add_patcher = """
def add_patcher(self, target, name, replacement):
    p = patch.object(target, name, replacement)
    p.start()
    self.patchers.append(p)"""

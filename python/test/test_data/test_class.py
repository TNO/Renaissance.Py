test_measure_wafer = """
"""

new_test_measure_wafer = """
"""
set_up = """
def setUp(self):
    self._patch_readout_data_filler = mock.patch("EMRM_ReadoutDataFiller.ReadoutDataFiller")
    self._patch_readout_data_publisher = mock.patch("EMRM_ReadoutDataPublisher.ReadoutDataPublisher")
    self._patch_dt_context_rep = mock.patch("EMRMxRepUtils.DPxCONTEXT")
    self._patch_dtxa_context_rep = mock.patch("EMRMxRepUtils.DTXAxCONTEXT")
    self._patch_dt_context_filler = mock.patch("EMRM_ReadoutDataFiller.DPxCONTEXT")
    self._patch_dtxa_context_filler = mock.patch("EMRM_ReadoutDataFiller.DTXAxCONTEXT")

    _ = self._patch_readout_data_filler.start()
    _ = self._patch_readout_data_publisher.start()
    _ = self._patch_dtxa_context_rep.start()
    _ = self._patch_dtxa_context_filler.start()
    mock_dt_context_rep = self._patch_dt_context_rep.start()
    mock_dt_context_filler = self._patch_dt_context_filler.start()

    mock_dt_context_rep.lookup_instance.return_value = (True, 1)
    mock_dt_context_filler.lookup_instance.return_value = (True, 2)

    EMRMxAPxData.data = EMRMxAPxData.EMRMxAPxData()
    EMRMxAPxData.data.initialize_engine(EMRMxEngine.EMRMxEngine())
    self.engine_stub = EMRMxEngine_stub()
    self.wh_stub = EMxWLxCTL_stub()
    self.vipr_stub = VIPR_stub()
    self.doubles = []

    context_stub = EMRMxCONTEXT.EMRMxCONTEXTStub()
    self.doubles.append(TAUT.TestDoubles(emrmxcontext=context_stub))
    self.doubles.append(
        TAUT.TestDoubles(module=EMRMxAPxData.data.rep, context=context_stub)
    )
    self.doubles.append(
        TAUT.TestDoubles(
            module=EMxWLxCTL.EMxWLxCTL, reload_wafer=self.wh_stub.reload_wafer
        )
    )
    self.doubles.append(
        TAUT.TestDoubles(
            module=EMRMxEngine.EMRMxEngine,
            measure_wafer=self.engine_stub.measure_wafer_gw,
        )
    )
    self.doubles.append(
        TAUT.TestDoubles(module=VIPR, check_stopped=self.vipr_stub.check_stopped)
    )

    EMRMxAPxData.data.adv_wp = EMRMxADVxWP.input()
    self.measurement_strategy = EMRM_MeasurementDefault.EMRM_MeasurementDefault()
"""
new_set_up = """
def setUp(self):
    self._patch_readout_data_filler = mock.patch("EMRM_ReadoutDataFiller.ReadoutDataFiller")
    self._patch_readout_data_publisher = mock.patch("EMRM_ReadoutDataPublisher.ReadoutDataPublisher")
    self._patch_dt_context_rep = mock.patch("EMRMxRepUtils.DPxCONTEXT")
    self._patch_dtxa_context_rep = mock.patch("EMRMxRepUtils.DTXAxCONTEXT")
    self._patch_dt_context_filler = mock.patch("EMRM_ReadoutDataFiller.DPxCONTEXT")
    self._patch_dtxa_context_filler = mock.patch("EMRM_ReadoutDataFiller.DTXAxCONTEXT")

    _ = self._patch_readout_data_filler.start()
    _ = self._patch_readout_data_publisher.start()
    _ = self._patch_dtxa_context_rep.start()
    _ = self._patch_dtxa_context_filler.start()
    mock_dt_context_rep = self._patch_dt_context_rep.start()
    mock_dt_context_filler = self._patch_dt_context_filler.start()

    mock_dt_context_rep.lookup_instance.return_value = (True, 1)
    mock_dt_context_filler.lookup_instance.return_value = (True, 2)

    EMRMxAPxData.data = EMRMxAPxData.EMRMxAPxData()
    EMRMxAPxData.data.initialize_engine(EMRMxEngine.EMRMxEngine())
    self.engine_stub = EMRMxEngine_stub()
    self.wh_stub = EMxWLxCTL_stub()
    self.vipr_stub = VIPR_stub()

    self.context_stub = EMRMxCONTEXT.EMRMxCONTEXTStub()
    self.patches = []
    self.patches.append(patch('EMRMxCONTEXT.emrmxcontext', self.context_stub))
    self.patches.append(patch.object(EMRMxAPxData.data.rep, 'context', self.context_stub))
    self.patches.append(patch.object(EMxWLxCTL.EMxWLxCTL, 'reload_wafer', self.wh_stub.reload_wafer))
    self.patches.append(patch.object(EMRMxEngine.EMRMxEngine, 'measure_wafer', self.engine_stub.measure_wafer_gw))
    self.patches.append(patch.object(VIPR, 'check_stopped', self.vipr_stub.check_stopped))
    for p in self.patches:
        p.start()

    EMRMxAPxData.data.adv_wp = EMRMxADVxWP.input()
    self.measurement_strategy = EMRM_MeasurementDefault.EMRM_MeasurementDefault()
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
    EMRWxCONTEXT.emrmxcontext.reset_method_attributes("start_wafer")
    EMRWxCONTEXT.emrmxcontext.reset_method_attributes("finish_wafer")
    EMRWxCONTEXT.emrmxcontext.reset_method_attributes("start_lot")
    EMRWxCONTEXT.emrmxcontext.reset_method_attributes("finish_lot")
    
    self._patch_readout_data_filler.stop()
    self._patch_readout_data_publisher.stop()
    self._patch_dt_context_rep.stop()
    self._patch_dtxa_context_rep.stop()
    self._patch_dt_context_filler.stop()
    self._patch_dtxa_context_filler.stop()
    patch.stopall()
"""
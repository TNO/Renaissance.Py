test_doubles_fun = """def test_align_wafer_bw(self):
    self.doubles.append(
        TAUT.TestDoubles(
            module=EMRMxEngine.EMRMxEngine, do_global_align=stub_do_global_align_bw
        )
    )
    chuck_id = EMRMxBASIC.chuck_operation_enum.CHUCK_2
    load_offset = DDXA.Struct("xyavect")
    self.assert_raises(
        ERXA.Error(EMRMxERR.EMRM_SYS_ERR, "Wafer alignment failed"),
        EMRMxAPxMEASxWLGLib.align_wafer,
        chuck_id,
        load_offset
    )
    self.assertEqual(EMRMxCONTEXT.emrmxcontext.method_called("start_lot"), 0)
    self.assertEqual(
        EMRMxCONTEXT.emrmxcontext.method_called("finish_lot"), 1
    )"""
test_doubles_fun_new = """def test_align_wafer_bw(self):
    with patch.object(EMRMxEngine.EMRMxEngine, 'do_global_align', stub_do_global_align_bw):
        chuck_id = EMRMxBASIC.chuck_operation_enum.CHUCK_2
        load_offset = DDXA.Struct("xyavect")
        self.assert_raises(
            ERXA.Error(EMRMxERR.EMRM_SYS_ERR, "Wafer alignment failed"),
            EMRMxAPxMEASxWLGLib.align_wafer,
            chuck_id,
            load_offset
        )
        self.assertEqual(EMRMxCONTEXT.emrmxcontext.method_called("start_lot"), 0)
        self.assertEqual(
            EMRMxCONTEXT.emrmxcontext.method_called("finish_lot"), 1
        )
"""

test_doubles_class_new = """class TestCloseTest(unittest.TestCase):
    
    def setUp(self):
        self._patch_readout_data_filler = mock.patch("EMRM_ReadoutDataFiller.ReadoutDataFiller")
        self._patch_readout_data_publisher = mock.patch("EMRM_ReadoutDataPublisher.ReadoutDataPublisher")
        _ = self._patch_readout_data_filler.start()
        _ = self._patch_readout_data_publisher.start()
        
        EMRMxAPxData.data = EMRMxAPxData.EMRMxAPxData()
        EMRMxAPxData.data.initialize_engine(EMRMxEngine.EMRMxEngine())
        self.tlg_stub = EMRMxTestlog_stub()
        self.patches = [
            patch.object(EMRMxTestlog.EMRMxTestlog, 'modify_tlg_file_id', self.tlg_stub.modify_tlg_file_id),
            patch.object(EMRMxTestlog.EMRMxTestlog, 'update_tlg_after_measurement', self.tlg_stub.update_tlg_after_measurement),
        ]
        for p in self.patches:
            p.start()

        self.results = EMRMxBASIC.result_struct()
        EMRMxAPxData.data.basic_inputs.mark_sequence_file_name = rms_file
        self.do_read_wid = False
        self.measurement_strategy = EMRM_MeasurementDefault.EMRM_MeasurementDefault()
        
    def tearDown(self):
        self._patch_readout_data_filler.stop()
        self._patch_readout_data_publisher.stop()
        for p in self.patches:
            p.stop()"""

test_doubles_class = """class TestCloseTest(TAUT.TestCase):
 
    def setUp(self):
        self._patch_readout_data_filler = mock.patch("EMRM_ReadoutDataFiller.ReadoutDataFiller")
        self._patch_readout_data_publisher = mock.patch("EMRM_ReadoutDataPublisher.ReadoutDataPublisher")
        _ = self._patch_readout_data_filler.start()
        _ = self._patch_readout_data_publisher.start()
        
        EMRMxAPxData.data = EMRMxAPxData.EMRMxAPxData()
        EMRMxAPxData.data.initialize_engine(EMRMxEngine.EMRMxEngine())
        self.doubles = []
 
        self.tlg_stub = EMRMxTestlog_stub()
        self.doubles.append(
            TAUT.TestDoubles(
                module=EMRMxTestlog.EMRMxTestlog,
                modify_tlg_file_id=self.tlg_stub.modify_tlg_file_id,
            )
        )
        self.doubles.append(
            TAUT.TestDoubles(
                module=EMRMxTestlog.EMRMxTestlog,
                update_tlg_after_measurement=self.tlg_stub.update_tlg_after_measurement,
            )
        )
        
        self.results = EMRMxBASIC.result_struct()
        EMRMxAPxData.data.basic_inputs.mark_sequence_file_name = rms_file
        self.do_read_wid = False
        self.measurement_strategy = EMRM_MeasurementDefault.EMRM_MeasurementDefault()
 
    def tearDown(self):
        self._patch_readout_data_filler.stop()
        self._patch_readout_data_publisher.stop()
        for double in self.doubles:
            double.exit()"""

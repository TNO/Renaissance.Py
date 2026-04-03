test_indent = """class test(b, c):
    def test_bw(self):
        self.doubles.append(TAUT.TestDoubles(a, b, c))
        id = b
        self.assert_raises(
            ERROR(a, "Wafer alignment failed"),
            id
        )
        self.assertEqual(c, 0)
"""
test_indent_new = """class test(b, c):
    def test_bw(self):
        with patch.object(a, 'b', c):
            id = b
            self.assert_raises(
                ERROR(a, "Wafer alignment failed"),
                id
            )
            self.assertEqual(c, 0)
"""
test_indent_fun = """def test_bw(self):
    self.doubles.append(TAUT.TestDoubles(a, b, c))
    id = b
    self.assert_raises(
        ERROR(a, "Wafer alignment failed"),
        id
    )
    self.assertEqual(c, 0)
"""
test_indent_fun_new = """def test_bw(self):
    with patch.object(a, 'b', c):
        id = b
        self.assert_raises(
            ERROR(a, "Wafer alignment failed"),
            id
        )
        self.assertEqual(c, 0)
"""
test_doubles_fun = """def test_align_wafer_bw(self):
    self.doubles.append(
        TAUT.TestDoubles(
            module=ACBDxEngine.ACBDxEngine, do_global_align=stub_do_global_align_bw
        )
    )
    chuck_id = ACBDxBASIC.chuck_operation_enum.CHUCK_2
    load_offset = BBAA.Struct("xyavect")
    self.assert_raises(
        ERXA.Error(ACBDxERR.ACBD_SYS_ERR, "Wafer alignment failed"),
        ACBDxAPxMEASxWLGLib.align_wafer,
        chuck_id,
        load_offset
    )
    self.assertEqual(ACBDxCONTEXT.acbdxcontext.method_called("start_lot"), 0)
    self.assertEqual(
        ACBDxCONTEXT.acbdxcontext.method_called("finish_lot"), 1
    )"""
test_doubles_fun_new = """def test_align_wafer_bw(self):
    with patch.object(ACBDxEngine.ACBDxEngine, 'do_global_align', stub_do_global_align_bw):
        chuck_id = ACBDxBASIC.chuck_operation_enum.CHUCK_2
        load_offset = BBAA.Struct("xyavect")
        self.assert_raises(
            ERXA.Error(ACBDxERR.ACBD_SYS_ERR, "Wafer alignment failed"),
            ACBDxAPxMEASxWLGLib.align_wafer,
            chuck_id,
            load_offset
        )
        self.assertEqual(ACBDxCONTEXT.acbdxcontext.method_called("start_lot"), 0)
        self.assertEqual(
            ACBDxCONTEXT.acbdxcontext.method_called("finish_lot"), 1
        )"""

test_doubles_class_new = """class TestCloseTest(unittest.TestCase):
    
    def setUp(self):
        self._patch_readout_data_filler = mock.patch("ACBD_ReadoutDataFiller.ReadoutDataFiller")
        self._patch_readout_data_publisher = mock.patch("ACBD_ReadoutDataPublisher.ReadoutDataPublisher")
        _ = self._patch_readout_data_filler.start()
        _ = self._patch_readout_data_publisher.start()
        ACBDxAPxData.data = ACBDxAPxData.ACBDxAPxData()
        ACBDxAPxData.data.initialize_engine(ACBDxEngine.ACBDxEngine())
        self.tlg_stub = ACBDxTestlog_stub()
        self.patches = [
            patch.object(ACBDxTestlog.ACBDxTestlog, 'modify_tlg_file_id', self.tlg_stub.modify_tlg_file_id),
            patch.object(ACBDxTestlog.ACBDxTestlog, 'update_tlg_after_measurement', self.tlg_stub.update_tlg_after_measurement),
        ]
        for p in self.patches:
            p.start()

        self.results = ACBDxBASIC.result_struct()
        ACBDxAPxData.data.basic_inputs.mark_sequence_file_name = rms_file
        self.do_read_wid = False
        self.measurement_strategy = ACBD_MeasurementDefault.ACBD_MeasurementDefault()

    def tearDown(self):
        self._patch_readout_data_filler.stop()
        self._patch_readout_data_publisher.stop()
        for p in self.patches:
            p.stop()"""

test_doubles_class = """class TestCloseTest(TAUT.TestCase):
 
    def setUp(self):
        self._patch_readout_data_filler = mock.patch("ACBD_ReadoutDataFiller.ReadoutDataFiller")
        self._patch_readout_data_publisher = mock.patch("ACBD_ReadoutDataPublisher.ReadoutDataPublisher")
        _ = self._patch_readout_data_filler.start()
        _ = self._patch_readout_data_publisher.start()
        
        ACBDxAPxData.data = ACBDxAPxData.ACBDxAPxData()
        ACBDxAPxData.data.initialize_engine(ACBDxEngine.ACBDxEngine())
        self.doubles = []
 
        self.tlg_stub = ACBDxTestlog_stub()
        self.doubles.append(
            TAUT.TestDoubles(
                module=ACBDxTestlog.ACBDxTestlog,
                modify_tlg_file_id=self.tlg_stub.modify_tlg_file_id,
            )
        )
        self.doubles.append(
            TAUT.TestDoubles(
                module=ACBDxTestlog.ACBDxTestlog,
                update_tlg_after_measurement=self.tlg_stub.update_tlg_after_measurement,
            )
        )
        
        self.results = ACBDxBASIC.result_struct()
        ACBDxAPxData.data.basic_inputs.mark_sequence_file_name = rms_file
        self.do_read_wid = False
        self.measurement_strategy = ACBD_MeasurementDefault.ACBD_MeasurementDefault()
 
    def tearDown(self):
        self._patch_readout_data_filler.stop()
        self._patch_readout_data_publisher.stop()
        for double in self.doubles:
            double.exit()"""

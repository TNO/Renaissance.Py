# ------------------------------------------------------#
# History                                              #
# 22-Jun-2010 : description                            #
# ------------------------------------------------------#
import unittest
from unittest import mock

import ABCDxABxCommonFunctions
import ABCDxABxREADLib
import ABCDxTL
import NNXA
import TAUT
import VIPCxUNIT


class TestImport(TAUT.TestCase):
    def test_import(self):
        self.import_and_verify_module("ABCDxTL")


class FakeABCDxTL(ABCDxTL):
    @TAUT.log_stub
    def create_test_log(self, test_log_id):
        test_log = NNXA.Object("ABCDxTL:test_log_struct")
        return test_log


class test_interface(TAUT.TestCase):
    def run(self):
        expected = self.read()
        self.assert_false(expected)
        self.assert_true(expected)
        self.assert_equal(expected, result)


class ABCD_Stub(TAUT.StubServer):
    def sharedSetUp(self):
        with TAUT.TestDoubles(module=ABCD, startup=startup_stub):
            ABCDxCONFIG.start_instance()

    @mock.patch("ABCD.result")
    def test_interaction_with_ABCD(self):
        pass


class Test_ABCDxTL(TAUT.TestCase):
    def setUpCommon(self):
        self.tds = [
            TestDoubles(abcdxread=ImprovedStub(ABCDxREAD.abcdxread)),
            TestDoubles(abcdxws=ImprovedStub(ABCDxWS.abcdxws)),
            TestDoubles(abxstream2=ImprovedStub(ABxSTREAM2.abxstream2)),
            TestDoubles(bcxclear=ImprovedStub(BCxCLEAR.bcxclear)),
            TestDoubles(bcxload=ImprovedStub(BCxLOAD.bcxload)),
        ]
        self.sut = ABCDxVIPCxAB.ABCDxVIPCxAB()

    def tearDownCommon(self):
        for td in self.tds:
            td.exit()

    def setUp(self):
        self.bc_stub = BCxCTL_stub()
        self.vipc_stub = VIPC_stub()
        self.doubles = []
        self.doubles.append(TAUT.TestDoubles(module=BCxCTL.BCxCTL, reload_wafer=self.bc_stub.reload_wafer))
        self.doubles.append(
            TAUT.TestDoubles(
                module=ABCDxEngine.ABCDxEngine,
                measure_wafer=self.engine_stub.measure_wafer_gw,
            )
        )
        self.doubles.append(TAUT.TestDoubles(module=VIPC, check_stopped=self.vipc_stub.check_stopped))

    def tearDown(self):
        for double in self.doubles:
            double.exit()


class test_log(VIPCxUNIT.TestCase):

    def test_ABCDxTL(self):
        with TAUT.TestDoubles(abcdxtl=FakeABCDxTL(None)):
            log = TAUT.Logger()

            test_log_id = NNXA.Object("EMTLXT:DD_test_log_id")
            test_log = NNXA.Object("ABCDxTL:test_log_struct")
            test_log = abcdxtl.create_test_log(test_log_id)

            file_id = NNXA.Object("EMTLXT:DD_test_log_file_id")
            file_name = NNXA.Object("ABCDxTL:.retrieve_test_log.file_name")
            fn = "ABCDxTL:test_log_struct"
            file_name[0 : len(fn)] = "ABCDxTL:test_log_struct"
            test_log, version_mismatch = abcdxtl.retrieve_test_log(file_id, test_log_id, file_name)

            abcdxtl.store_test_log(file_id, test_log)


class test_abcdxwid(TAUT.TestCase):
    def test_readout_is_ok(self):
        self.doubles.append(TAUT.TestDoubles(module=ABCDxWID.abcdwid, get_wid_readouts=stub_get_wid_readouts))
        id = ABCDxBASIC.id
        read = True
        ABCDxABxCommonFunctions.CLEAR_CALLED = False
        self.assert_raises(
            ABCD.Error(ABCDxERR.ABCD_SYS_ERR, "error message"),
            ABCDxABxREADLib.read,
            id,
            read,
        )
        self.assertEqual(ABCDxCONTEXT.abcdxcontext.method_called("start"), 0)

    def test_read_two_doubles(self):
        self.doubles.append(
            TAUT.TestDoubles(
                module=ABCDxABxLib,
                _create_marks=marks,
            )
        )
        self.doubles.append(
            TAUT.TestDoubles(
                module=ABCDxEngine.ABCDxEngine,
                measure=self.engine.measure,
            )
        )
        id = ABCDxBASIC.id
        ABCDxABxCommonFunctions.CLEAR_CALLED = False
        self.assert_raises(
            ABCD.Error(ABCDxERR.ABCD_SYS_ERR, "error message"),
            ABCDxABxREADLib.read,
            id,
        )

        self.assertEqual(ABCDxCONTEXT.abcdxcontext.method_called("start"), 1)
        self.assertEqual(ABCDxCONTEXT.abcdxcontext.method_called("finish"), 1)


if __name__ == "__main__":
    unittest.main()

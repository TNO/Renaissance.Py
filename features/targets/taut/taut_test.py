#------------------------------------------------------#
# History                                              #
# 22-Jun-2010 : description                            #
#------------------------------------------------------#
import unittest
import NNXA
import LLXA
import TAUT
import VIPCxUNIT
import ABCDxTL

class TestImport(TAUT.TestCase):
    def test_import(self):
        self.import_and_verify_module('ABCDxTL')

class FakeABCDxTL(ABCDxTL):
    @TAUT.log_stub
    def create_test_log(self, test_log_id):
        test_log = NNXA.Object('ABCDxTL:test_log_struct')
        return test_log

class Test_ABCDxTL(VIPCxUNIT.TestCase):
    def test_ABCDxTL(self):
        with TAUT.TestDoubles(abcdxtl=FakeABCDxTL(None)):
            log = TAUT.Logger()

            test_log_id = NNXA.Object('EMTLXT:DD_test_log_id')
            test_log = NNXA.Object('ABCDxTL:test_log_struct')
            test_log = abcdxtl.create_test_log(test_log_id)

            file_id = NNXA.Object('EMTLXT:DD_test_log_file_id')
            file_name = NNXA.Object('ABCDxTL:.retrieve_test_log.file_name')
            fn = 'ABCDxTL:test_log_struct'
            file_name[0:len(fn)] = 'ABCDxTL:test_log_struct'
            test_log, version_mismatch = abcdxtl.retrieve_test_log(file_id, test_log_id, file_name)

            abcdxtl.store_test_log(file_id, test_log)


if __name__ == '__main__':
    unittest.main()
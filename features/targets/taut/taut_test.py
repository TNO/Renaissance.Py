#------------------------------------------------------#
# History                                              #
# 22-Jun-2010 : description                            #
#------------------------------------------------------#
import unittest
import DDXA
import OOXA
import TAUT
import VIPRxUNIT
import EMRWxTL

class TestImport(TAUT.TestCase):
    def test_import(self):
        self.import_and_verify_module('EMRWxTL')

class FakeEMRWxTL(EMRWxTL):
    @TAUT.log_stub
    def create_test_log(self, test_log_id):
        test_log = DDXA.Object('EMRWxTL:test_log_struct')
        return test_log

class Test_EMRWxTL(VIPRxUNIT.TestCase):
    def test_EMRWxTL(self):
        with TAUT.TestDoubles(emrwxtl=FakeEMRWxTL(None)):
            log = TAUT.Logger()

            test_log_id = DDXA.Object('EMTLXT:DD_test_log_id')
            test_log = DDXA.Object('EMRWxTL:test_log_struct')
            test_log = emrwxtl.create_test_log(test_log_id)

            file_id = DDXA.Object('EMTLXT:DD_test_log_file_id')
            file_name = DDXA.Object('EMRWxTL:.retrieve_test_log.file_name')
            fn = 'EMRWxTL:test_log_struct'
            file_name[0:len(fn)] = 'EMRWxTL:test_log_struct'
            test_log, version_mismatch = emrwxtl.retrieve_test_log(file_id, test_log_id, file_name)

            emrwxtl.store_test_log(file_id, test_log)


if __name__ == '__main__':
    unittest.main()
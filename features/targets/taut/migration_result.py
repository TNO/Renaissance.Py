#------------------------------------------------------#
# History                                              #
# 22-Jun-2010 : description                            #
# 17-Feb-2026 : TAUT migration                         #
#------------------------------------------------------#
import unittest
import DDXA
import OOXA
import VIPRxUNIT
import EMRWxTL

class TestImport(unittest.TestCase):
    def test_import(self):
        import EMRWxTL
        self.assertIsNotNone(EMRWxTL)

class FakeEMRWxTL(EMRWxTL):

    def create_test_log(self, test_log_id):
        test_log = DDXA.Object('EMRWxTL:test_log_struct')
        return test_log

class Test_EMRWxTL(VIPRxUNIT.TestCase):
    def test_EMRWxTL(self):
        fake_emrwxtl = FakeEMRWxTL(None)

        test_log_id = DDXA.Object('EMTLXT:DD_test_log_id')
        test_log = DDXA.Object('EMRWxTL:test_log_struct')
        test_log = fake_emrwxtl.create_test_log(test_log_id)

        file_id = DDXA.Object('EMTLXT:DD_test_log_file_id')
        file_name = DDXA.Object('EMRWxTL:.retrieve_test_log.file_name')
        fn = 'EMRWxTL:test_log_struct'
        file_name[0:len(fn)] = 'EMRWxTL:test_log_struct'
        test_log, version_mismatch = fake_emrwxtl.retrieve_test_log(file_id, test_log_id, file_name)

        fake_emrwxtl.store_test_log(file_id, test_log)


if __name__ == '__main__':
    unittest.main()
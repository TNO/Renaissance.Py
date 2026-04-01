input_code = """
import OOXA
def a():
    x = 10

def b():
    y = 12"""
insert_code = """

class Asserter(unittest.TestCase):
    def assert_double_equal(self, a, b):
        self.assertAlmostEqual(a, b)
    
    def assert_raises(self, exception, callable_obj, *args, **kwargs):
        if isinstance(exception, BaseException):
            exc_type = type(exception)
            try:
                callable_obj(*args, **kwargs)
                self.fail("Expected {} to be raised".format(exc_type.__name__))))
            except exc_type as e:
                self.assertEqual(str(e), str(exception), "Expected error_id but got {}".format(exception.id))")
        else:
            self.assertRaises(exception, callable_obj, *args, **kwargs)
"""

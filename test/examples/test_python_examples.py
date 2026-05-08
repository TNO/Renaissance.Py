import pytest
from hamcrest import assert_that, is_

from rejuvenation.python_ast_example import python_ast_smoke_test
from rejuvenation.python_cst_example import python_cst_smoke_test
from rejuvenation.python_lst_example import python_lst_smoke_test
from rejuvenation.python_rst_example import python_rst_smoke_test

result = "\nfrom module import foo, bar, baz, quux\nba(51)\n# changed function f1 to f2\nf2(52\n,123456)\n\n# changed function f1 to f2\nf2(53\n,123456)\n\npa(54)\n\n# changed if expr to const\nisAOne=True\nif(isAOne):\n    ba()\n\n\npa(54)  \n"


class TestPythonExamples:
    def test_python_ast_still_works(self):
        result = python_ast_smoke_test()
        assert_that(result, is_(result))

    def test_python_cst_still_works(self):
        result = python_cst_smoke_test()
        assert_that(result, is_(result))

    def test_python_lst_still_works(self):
        result = python_lst_smoke_test()
        assert_that(result, is_(result))

    def test_python_rst_still_works(self):
        result = python_rst_smoke_test()
        assert_that(result, is_(result))

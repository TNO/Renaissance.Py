# from typing import Iterable
# from renaissance.common import Stream
# import pytest
# from hamcrest import *
#
#
# # test helpers:
# class A:
#     pass
#
#
# class BA(A):
#     pass
#
#
# class C:
#     pass
#
#
# class TestStream:
#
#     def test_to_iterable(self):
#         assert_that(isinstance(Stream([1, 2, 3, 4, 5]).to_iterable(), Iterable), is_(True))
#
#     def test_find_any_exception(self):
#         try:
#             Stream([]).find_any().get()
#             self.fail("Should have thrown a Value Error")
#         except ValueError:
#             pass
#
#     def test_find_first_exception(self):
#         try:
#             Stream([]).find_first().get()
#             self.fail("Should have thrown a Value Error")
#         except ValueError:
#             pass
#
#     def test_find_last_exception(self):
#         try:
#             Stream([]).find_last().get()
#             self.fail("Should have thrown a Value Error")
#         except ValueError:
#             pass
#
#     @pytest.mark.parametrize("input, expected", [(([1, 2, 3, 4, 5]), [2, 4]), (([]), [])])
#     def test_filter(self, input, expected):
#         result = Stream(input).filter(lambda x: x % 2 == 0).to_list()
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize("input, expected", [(([1, 2, 3, 4, 5]), [2, 4, 6, 8, 10]), (([]), [])])
#     def test_map(self, input, expected):
#         result = Stream(input).map(lambda x: x * 2).to_list()
#         assert_that(result, is_(expected))
#
#     a = A()
#     b = BA()  # b is a subclass of A
#     c = C()
#
#     @pytest.mark.parametrize("input, typ, expected", [(([a, b, c]), A, [a, b]), (([a, b, c]), C, [c])])
#     def test_map_cast(self, input, typ, expected):
#         result = Stream(input).map(typ).to_list()
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize(
#         "input, expected",
#         [
#             (([[1, 2], [3, 4], [5]]), [1, 2, 3, 4, 5]),
#             (([[], [1], [2, 3]]), [1, 2, 3]),
#             (([[], []]), []),
#         ],
#     )
#     def test_flat_map(self, input, expected):
#         result = Stream(input).flat_map(lambda x: x).to_list()
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize(
#         "input, expected",
#         [
#             (([Stream([1, 2]), Stream([3, 4]), Stream([5])]), [1, 2, 3, 4, 5]),
#             (([Stream([]), Stream([1]), Stream([2, 3])]), [1, 2, 3]),
#             (([Stream([]), Stream([])]), []),
#         ],
#     )
#     def test_flat_map_stream_input(self, input, expected):
#         result = Stream(input).flat_map(lambda x: x).to_list()
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize(
#         "input, expected",
#         [(([1, 2, 2, 3, 4, 4, 5]), [1, 2, 3, 4, 5]), (([1, 1, 1, 1]), [1]), (([]), [])],
#     )
#     def test_distinct(self, input, expected):
#         result = Stream(input).distinct().to_list()
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize(
#         "input, expected",
#         [(([5, 3, 1, 4, 2]), [1, 2, 3, 4, 5]), (([3, 1, 2]), [1, 2, 3]), (([]), [])],
#     )
#     def test_sorted(self, input, expected):
#         result = Stream(input).sorted().to_list()
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize(
#         "input, expected",
#         [
#             (([1, 2, 3, 4, 5]), [1, 2, 3, 4, 5]),
#             (([5, 4, 3, 2, 1]), [5, 4, 3, 2, 1]),
#             (([]), []),
#         ],
#     )
#     def test_peek(self, input, expected):
#         result = []
#         Stream(input).peek(lambda x: result.append(x)).to_list()
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize(
#         "input, limit, expected",
#         [(([1, 2, 3, 4, 5]), 3, [1, 2, 3]), (([1, 2, 3]), 5, [1, 2, 3]), (([], 3, []))],
#     )
#     def test_limit(self, input, limit, expected):
#         result = Stream(input).limit(limit).to_list()
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize(
#         "input, skip, expected",
#         [(([1, 2, 3, 4, 5]), 2, [3, 4, 5]), (([1, 2, 3]), 1, [2, 3]), (([], 1, []))],
#     )
#     def test_skip(self, input, skip, expected):
#         result = Stream(input).skip(skip).to_list()
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize("input, expected", [(([1, 2, 3, 4, 5]), [1, 2, 3, 4, 5]), (([]), [])])
#     def test_for_each(self, input, expected):
#         result = []
#         Stream(input).for_each(lambda x: result.append(x))
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize(
#         "input, expected",
#         [(([0, 1, 2, 3, 4, 5]), 15), (([0, 1, 2, 3]), 6), (([]), None)],
#     )
#     def test_reduce(self, input, expected):
#         result = Stream(input).reduce(lambda x, y: x + y).or_else(None)
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize("input, expected", [(([1, 2, 3, 4, 5]), [1, 2, 3, 4, 5]), (([]), [])])
#     def test_collect(self, input, expected):
#         result = Stream(input).collect(list)
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize("input, expected", [(([1, 2, 3, 4, 5]), 5), (([1, 2, 3]), 3), (([]), 0)])
#     def test_count(self, input, expected):
#         result = Stream(input).count()
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize(
#         "input, predicate, expected",
#         [
#             (([1, 2, 3, 4, 5]), lambda x: x > 3, True),
#             (([1, 2, 3]), lambda x: x > 3, False),
#             (([]), lambda x: x > 3, False),
#         ],
#     )
#     def test_any_match(self, input, predicate, expected):
#         result = Stream(input).any_match(predicate)
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize(
#         "input, predicate, expected",
#         [
#             (([1, 2, 3, 4, 5]), lambda x: x > 0, True),
#             (([1, 2, 3, 4, 5]), lambda x: x > 3, False),
#             (([]), lambda x: x > 0, True),
#         ],
#     )
#     def test_all_match(self, input, predicate, expected):
#         result = Stream(input).all_match(predicate)
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize(
#         "input, predicate, expected",
#         [
#             (([1, 2, 3, 4, 5]), lambda x: x > 5, True),
#             (([1, 2, 3, 4, 5]), lambda x: x > 3, False),
#             (([]), lambda x: x > 0, True),
#         ],
#     )
#     def test_none_match(self, input, predicate, expected):
#         result = Stream(input).none_match(predicate)
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize(
#         "input, expected",
#         [(([1, 2, 3, 4, 5]), 1), (([5, 4, 3, 2, 1]), 5), (([]), None)],
#     )
#     def test_find_first(self, input, expected):
#         result = Stream(input).find_first().or_else(None)
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize(
#         "input, expected",
#         [(([1, 2, 3, 4, 5]), 5), (([5, 4, 3, 2, 1]), 1), (([]), None)],
#     )
#     def test_find_last(self, input, expected):
#         result = Stream(input).find_last().or_else(None)
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize(
#         "input, expected",
#         [(([1, 2, 3, 4, 5]), 1), (([5, 4, 3, 2, 1]), 5), (([]), None)],
#     )
#     def test_find_any_get(self, input, expected):
#         result = Stream(input).find_any().get() if Stream(input).to_list() else None
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize(
#         "input, expected",
#         [(([1, 2, 3, 4, 5]), 1), (([5, 4, 3, 2, 1]), 5), (([]), None)],
#     )
#     def test_find_any_or_else(self, input, expected):
#         result = Stream(input).find_any().or_else(None)
#         assert_that(result, is_(expected))
#
#     @pytest.mark.parametrize(
#         "input, expected",
#         [(([1, 2, 3, 4, 5]), True), (([5, 4, 3, 2, 1]), True), (([]), False)],
#     )
#     def test_find_any_is_present(self, input, expected):
#         result = Stream(input).find_any().is_present()
#         assert_that(result, is_(expected))
#
#
# if __name__ == "__main__":
#     pytest.main()

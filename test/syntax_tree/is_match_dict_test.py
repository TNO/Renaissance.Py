from hamcrest import assert_that, is_, is_not

from renaissance.syntax_tree.match_finder import is_match_dict


class TestIsMatchDict:
    def test_is_same_dict(self):
        src={ 'a': 'asd', 'b': 'zxc'}
        cmp={ 'a': 'asd', 'b': 'zxc'}
        assert_that(is_match_dict(src,cmp,{}))


    def test_is_same_dict_different_key(self):
        src={ 'a': 'asd', 'b': 'zxc'}
        cmp={ 'a': 'asd', 'c': 'zxc'}
        assert_that(is_match_dict(src,cmp), is_(False))


    def test_is_same_dict_extra_key(self):
        src={ 'a': 'asd', 'b': 'zxc','extra': 'zxc'}
        cmp={ 'a': 'asd', 'b': 'zxc'}
        assert_that(is_match_dict(src,cmp), is_(False))


    def test_is_same_dict_missing_key(self):
        src={ 'a': 'asd', 'b': 'zxc'}
        cmp={ 'a': 'asd', 'b': 'zxc','extra': 'zxc'}
        assert_that(is_match_dict(src,cmp,), is_(False))


    def test_is_same_dict_extra_irelevent_key(self):
        src={ 'a': 'asd', 'b': 'zxc','macro_expansion': 'zxc'}
        cmp={ 'a': 'asd', 'b': 'zxc',}
        assert_that(is_match_dict(src,cmp,{}), is_(True))


    def test_is_same_dict_key_in_expansion(self):
        src = {'a': 'asd', 'b': 'zxc', }
        cmp = {'a': 'asd', 'b': '$var', }
        assert_that(is_match_dict(src, cmp, {'$var': ['zxc']}),  is_(True))


    def test_is_same_dict_key_no_expansion(self):
        src = {'a': 'asd', 'b': 'zxc', }
        cmp = {'a': 'asd', 'b': '$var', }
        assert_that(is_match_dict(src, cmp),  is_(True))


    def test_is_same_dict_key_in_expansion_with_different_value(self):
        src = {'a': 'asd', 'b': 'zxc', }
        cmp = {'a': 'asd', 'b': '$var', }
        assert_that(is_match_dict(src, cmp, {'$var': '_xc'}), is_(False))


    def test_is_same_dict_key_in_expansion_in_src_should_not_happen(self):
        src={ 'a': 'asd', 'b': '$var',}
        cmp={ 'a': 'asd', 'b': 'zxc',}
        assert_that(is_match_dict(src,cmp), is_(False))




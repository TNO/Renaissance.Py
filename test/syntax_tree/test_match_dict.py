"""Tests for the is_match_dict dictionary matching helper."""

from hamcrest import assert_that, is_

from renaissance.syntax_tree.match_finder import is_match_dict


class TestIsMatchDict:
    """AI: Tests for the is_match_dict dictionary matching helper."""

    def test_is_same_dict(self) -> None:
        """AI: Verify two identical dicts match."""
        src = {"a": "asd", "b": "zxc"}
        cmp = {"a": "asd", "b": "zxc"}
        assert_that(is_match_dict(src, cmp, {}))

    def test_is_same_dict_different_key(self) -> None:
        """AI: Verify dicts with a differing key do not match."""
        src = {"a": "asd", "b": "zxc"}
        cmp = {"a": "asd", "c": "zxc"}
        assert_that(is_match_dict(src, cmp), is_(False))

    def test_is_same_dict_extra_key(self) -> None:
        """AI: Verify src having an extra key not present in cmp causes a mismatch."""
        src = {"a": "asd", "b": "zxc", "extra": "zxc"}
        cmp = {"a": "asd", "b": "zxc"}
        assert_that(is_match_dict(src, cmp), is_(False))

    def test_is_same_dict_missing_key(self) -> None:
        """AI: Verify src missing a key present in cmp causes a mismatch."""
        src = {"a": "asd", "b": "zxc"}
        cmp = {"a": "asd", "b": "zxc", "extra": "zxc"}
        assert_that(
            is_match_dict(
                src,
                cmp,
            ),
            is_(False),
        )

    def test_is_same_dict_extra_irelevent_key(self) -> None:
        """AI: Verify an irrelevant 'macro_expansion' key in src is ignored when matching against cmp."""
        src = {"a": "asd", "b": "zxc", "macro_expansion": "zxc"}
        cmp = {
            "a": "asd",
            "b": "zxc",
        }
        assert_that(is_match_dict(src, cmp, {}), is_(True))

    def test_is_same_dict_key_in_expansion(self) -> None:
        """AI: Verify a placeholder value in cmp matches when it's bound to the corresponding value in the expansion map."""
        src = {
            "a": "asd",
            "b": "zxc",
        }
        cmp = {
            "a": "asd",
            "b": "$var",
        }
        assert_that(is_match_dict(src, cmp, {"$var": ["zxc"]}), is_(True))

    def test_is_same_dict_key_no_expansion(self) -> None:
        """AI: Verify a placeholder value in cmp matches src when no expansion map is provided."""
        src = {
            "a": "asd",
            "b": "zxc",
        }
        cmp = {
            "a": "asd",
            "b": "$var",
        }
        assert_that(is_match_dict(src, cmp), is_(True))

    def test_is_same_dict_key_in_expansion_with_different_value(self) -> None:
        """AI: Verify a placeholder value in cmp mismatches when the expansion map binds a different value."""
        src = {
            "a": "asd",
            "b": "zxc",
        }
        cmp = {
            "a": "asd",
            "b": "$var",
        }
        assert_that(is_match_dict(src, cmp, {"$var": "_xc"}), is_(False))

    def test_is_same_dict_key_in_expansion_in_src_should_not_happen(self) -> None:
        """AI: Verify a placeholder value appearing in src (not cmp) does not match a literal value in cmp."""
        src = {
            "a": "asd",
            "b": "$var",
        }
        cmp = {
            "a": "asd",
            "b": "zxc",
        }
        assert_that(is_match_dict(src, cmp), is_(False))

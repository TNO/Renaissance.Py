from pytest_bdd import scenarios, given, when, then, parsers


scenarios("arguments.feature")


@given(parsers.parse("there are {start:d} cucumbers"), target_fixture="cucumbers")
def given_cucumbers(start : int):
    return {"start": start, "eat": 0}


@when(parsers.parse("I eat {eat:d} cucumbers"))
def eat_cucumbers(cucumbers : dict[str, int], eat :int):
    cucumbers["eat"] += eat


@then(parsers.parse("I should have {left:d} cucumbers"))
def should_have_left_cucumbers(cucumbers: dict[str, int], left : int):
    assert cucumbers["start"] - cucumbers["eat"] == left
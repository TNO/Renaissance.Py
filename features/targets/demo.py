def some_old_fun():
    a = 1
    b = a
    return b


component_one, component_two = 1, 2
component_three: int = 3
component_four = 4
component_five = 5
component_six = sum(2, 4)

long_expression = component_one + component_two + component_three + component_four + component_five + component_six


def xyzzy(a1, a2, long_parameter_1, a3, a4, long_parameter_2):
    pass


xyzzy(1, 2, "long_string_constant1", 3, 4, "long_string_constant2")

xyzzy("with", "hanging", "indent")
items = []
attrs = [e.attr for e in items]

num_dict = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}

colors = ["red", "green", "blue", "black", "white", "gray"]

star_names = {"Sirius", "Betelgeuse", "Polaris", "Vega", "Arcturus", "Aldebaran"}

planets = (
    "Mercury",
    "Venus",
    "Earth",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
)

ingredients = [
    "green",
    "eggs",
]

if True:
    pass

try:
    pass
finally:
    pass

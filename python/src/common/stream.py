import itertools
from typing import TypeVar, Generic, Iterable, Callable, Any, Optional
from functools import reduce

T = TypeVar('T')
U = TypeVar('U')

class StreamOptional(Generic[T]):
    """ Creates a Optional result similar to java.util.Optional"""
    def __init__(self, value: Optional[T]):
        self.__value = value

    def is_present(self) -> bool:
        return self.__value is not None
    
    def get(self) -> T:
        """return the value if present, otherwise raise an exception"""
        if self.__value is None:
            raise ValueError("No value present")
        return self.__value
    
    def or_else(self, other: T) -> T:
        return self.__value if not self.__value is None else other
    
  
class Stream(Generic[T]):
    """A Stream similar to java.util.Stream"""
    def __init__(self, iterable: Iterable[T]):
        self.__iterable = iterable

    def to_iterable(self) -> Iterable[T]:
        return self.__iterable # type: ignore

    def filter(self, func: Callable[[T], bool]) -> 'Stream[T]':
        self.__iterable = filter(func, self.__iterable) # type: ignore
        return self

    def map(self, func_or_type: type[U]|Callable[[T], U|None]) -> 'Stream[U]':
        if not isinstance(func_or_type, Callable):
            return Stream(map(Stream.__cast, filter(lambda x: isinstance(x, func_or_type), self.__iterable)))
        mapped = map(func_or_type, self.__iterable) # type: ignore
        filtered = filter(lambda t: t!=None, mapped)
        return Stream(filtered)

    def flat_map(self, func: Callable[[T], 'Iterable[U]|Stream[U]']) -> 'Stream[U]':
        def get_iterable(x): 
            result = func(x)
            if isinstance(result, Stream):
                return result.__iterable
            
        flat_map = (item for sublist in map(get_iterable, self.__iterable) for item in sublist) # type: ignore
        return Stream(flat_map)

    def distinct(self) -> 'Stream[T]':
        seen = set()
        self.__iterable = (x for x in self.__iterable if x not in seen and not seen.add(x))
        return self

    def sorted(self, key: Optional[Callable[[T], Any]] = None, reverse: bool = False) -> 'Stream[T]':
        self.__iterable = iter(sorted(self.__iterable, key=key, reverse=reverse)) # type: ignore
        return self

    def peek(self, func: Callable[[T], Any]) -> 'Stream[T]':
        self.__iterable = (x for x in self.__iterable if not func(x))
        return self

    def limit(self, max_size: int) -> 'Stream[T]':
        self.__iterable = (x for i, x in enumerate(self.__iterable) if i < max_size)
        return self

    def skip(self, n: int) -> 'Stream[T]':
        self.__iterable = (x for i, x in enumerate(self.__iterable) if i >= n)
        return self

    def action(self, func: Callable[[T], Any]) -> 'Stream[T]':
        self.__iterable, iter2 = itertools.tee(self.__iterable)
        for item in iter2:
            func(item)
            return self # first item only
        return self

    def for_each(self, func: Callable[[T], Any]) -> None:
        for item in self.__iterable:
            func(item) # type: ignore

    def to_list(self) -> list[T]:
        return list(self.__iterable) # type: ignore

    def reduce(self, func: Callable[[T, T], T]) -> StreamOptional[T]:
        initial = next(self.__iterable, None) # type: ignore
        if initial is None:
            return StreamOptional(None)
        return StreamOptional(reduce(func, self.__iterable, func(initial, initial))) 

    def collect(self, collector: Callable[[Iterable[T]], Any]) -> Any:
        return collector(self.__iterable) # type: ignore

    def count(self) -> int:
        return sum(1 for _ in self.__iterable)

    def any_match(self, predicate: Callable[[T], bool]) -> bool:
        return any(predicate(x) for x in self.__iterable) # type: ignore

    def all_match(self, predicate: Callable[[T], bool]) -> bool:
        return all(predicate(x) for x in self.__iterable) # type: ignore

    def none_match(self, predicate: Callable[[T], bool]) -> bool:
        return not any(predicate(x) for x in self.__iterable) # type: ignore
    
    def find_first(self) -> StreamOptional[T]:
        try:
            return StreamOptional(next(self.__iterable, None)) # type: ignore
        except StopIteration:
            return StreamOptional(None)

    def find_last(self) -> StreamOptional[T]:
        try:
            # get the latest element from the iterable
            return StreamOptional(list(self.__iterable)[-1]) # type: ignore
        except StopIteration:
            return StreamOptional(None)

    def find_any(self) -> StreamOptional[T]:
        return self.find_first()

    @staticmethod
    def __cast(node): 
        assert isinstance(node, node) 
        return node

if __name__ == '__main__':
    # Example usage
    l = [1, 2, 3, 4, 5, 6, 7, 8]

    # Use the Stream class to chain transformations
    def multiply_by_10(x):  return x * 10
    result = Stream(l).filter(lambda x: x % 2 == 0).map(multiply_by_10).find_first().get()
    print(result)  # Output: [20, 40, 60, 80]

    # Additional operations
    sum_result = Stream(l).filter(lambda x: x % 2 == 0).map(lambda x: x * 10).reduce(lambda x, y: x + y)
    print(sum_result)  # Output: 200
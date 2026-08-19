#TODO: Why our own implementation?
#TODO: Why not use itertools? 
#TODO: Why not use RxPy?

from __future__ import annotations
from typing import Iterable, Callable, Any, Optional
from functools import reduce


class StreamOptional[T]:
    """ Creates an Optional result similar to java.util.Optional"""
    def __init__(self, value: Optional[T]):
        self.__value = value

    def is_present(self) -> bool:
        return self.__value is not None
    
    def get(self) -> T:
        """return the value if present, otherwise raise an exception"""
        if self.__value is None:
            raise ValueError("No value present")
        return self.__value
    
    def or_else[U](self, other: U) -> T|U:
        return self.__value if not self.__value is None else other
    
  
class Stream[T]:
    """A Stream similar to java.util.Stream"""
    def __init__(self, iterable: Iterable[T]):
        self.__iterable: Iterable[T] = iterable
                            #TODO: correctly solved Iterator[T@Stream] iso Iterable[T@Stream]?

    def to_iterable(self) -> Iterable[T]:
        return self.__iterable 

    def filter(self, func: Callable[[T], bool]) -> Stream[T]:
        self.__iterable = filter(func, self.__iterable) 
        return self

    def map[U](self, func_or_type: type[U]|Callable[[T], Optional[U]]) -> Stream[Optional[U]]:
        if type(func_or_type) is type[U]:
            cast : Callable[[T], Optional[U]] = lambda x: Stream.__cast(x, func_or_type)
            mapped = map(cast, self.__iterable)
        else: 
            mapped = map(func_or_type, self.__iterable) 
        filtered = filter(lambda t: t is not None, mapped)
        return Stream(filtered)

    def flat_map[U](self, func: Callable[[T], Iterable[U]|Stream[U]]) -> Stream[U]:
        def get_iterable(x: T): 
            result = func(x)
            if isinstance(result, Stream):
                return result.__iterable
            return result
            
        flat_map = (item for sublist in map(get_iterable, self.__iterable) for item in sublist) 
        return Stream(flat_map)

    def distinct(self) -> Stream[T]:
        seen: set[T] = set()
        self.__iterable = (x for x in self.__iterable if x not in seen and not seen.add(x))
        return self

    def sorted(self, key: Optional[Callable[[T], Any]] = None, reverse: bool = False) -> Stream[T]:
        self.__iterable = iter(sorted(self.__iterable, key=key, reverse=reverse))  # type: ignore
        return self

    def peek(self, func: Callable[[T], Any]) -> Stream[T]:
        self.__iterable = (x for x in self.__iterable if not func(x) or True)
        return self

    def action(self, func: Callable[[T], Any]) -> Stream[T]:
        return self.peek(func)

    def limit(self, max_size: int) -> Stream[T]:
        self.__iterable = (x for i, x in enumerate(self.__iterable) if i < max_size)
        return self

    def skip(self, n: int) -> Stream[T]:
        self.__iterable = (x for i, x in enumerate(self.__iterable) if i >= n)
        return self

    def for_each(self, func: Callable[[T], Any]) -> None:
        for item in self.__iterable:
            func(item) 

    def to_list(self) -> list[T]:
        return list(self.__iterable) 

    def reduce(self, func: Callable[[T, T], T]) -> StreamOptional[T]:
        for item in self.__iterable:
            initial = item
            #TODO: first item is used twice - as initial value and first value
            return StreamOptional(reduce(func, self.__iterable, initial)) 
        return StreamOptional(None)

    def collect(self, collector: Callable[[Iterable[T]], Any]) -> Any:
        return collector(self.__iterable) 

    def count(self) -> int:
        return sum(1 for _ in self.__iterable)

    def any_match(self, predicate: Callable[[T], bool]) -> bool:
        return any(predicate(x) for x in self.__iterable) 

    def all_match(self, predicate: Callable[[T], bool]) -> bool:
        return all(predicate(x) for x in self.__iterable) 

    def none_match(self, predicate: Callable[[T], bool]) -> bool:
        return not any(predicate(x) for x in self.__iterable) 
    
    def find_first(self) -> StreamOptional[T]:
        for item in self.__iterable:
            return StreamOptional(item)
        return StreamOptional(None)

    def find_last(self) -> StreamOptional[T]:
        try:
            # get the latest element from the iterable
            return StreamOptional(list(self.__iterable)[-1]) 
        except:
            return StreamOptional(None)

    def find_any(self) -> StreamOptional[T]:
        return self.find_first()

    @staticmethod
    def __cast[U](obj : object, typ : type[U]) -> Optional[U]: 
        if isinstance(obj, typ):
            return obj
        return None
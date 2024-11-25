
from abc import ABC, abstractmethod
from functools import partial
import multiprocessing
import dill as pickle
import re
from typing import Any, Callable, Iterable, Optional, Sequence, TypeVar

from syntax_tree.ast_processor import ASTProcessor
from .ast_factory import ASTFactory
from .ast_node import ASTNodeType
from .ast_shower import ASTShower


T = TypeVar('T')

ATU = tuple[ASTFactory[ASTNodeType],ASTNodeType]
Action = Callable[[ASTProcessor],None]
IterableProvider = Callable[[], Iterable[ATU]]


class BatchASTProcessor():

    class HasFinalAction(ABC):
        @abstractmethod
        def final_action(self)->None:
            pass

    def __init__(self, user_objects: Optional[dict[str, Any]] = None, in_memory: bool = False, max_processes=4):
        """
        Initialize the BatchASTProcessor.

        Args:
            user_objects (Optional[dict[str, Any]]): A dictionary of user-defined objects. Defaults to None.
            in_memory (bool): Flag to indicate if processing should be done in memory. Defaults to False.
            max_processes (int): The maximum number of processes to use. Defaults to 4.
        """
        self.user_objects: dict[str,Any] = user_objects if isinstance(user_objects, dict) else {}
        self.in_memory: bool = in_memory
        self.in_memory_files : dict[str,str] ={}
        self.max_processes = max_processes

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for user_object in self.user_objects.values():
            if isinstance(user_object, BatchASTProcessor.HasFinalAction):
                user_object.final_action()

    def once(self, iterable: Iterable[ATU]|IterableProvider, actions: Action|Sequence[Action], file_filter: Optional[str|re.Pattern] = None):
        """
        Processes a given iterable of ATU objects or an IterableProvider with specified actions.

        Args:
            iterable (Iterable[ATU] | IterableProvider): The iterable or provider of ATU objects to process.
            actions (Action | Sequence[Action]): The action or sequence of actions to apply to each item in the iterable.
            file_filter (Optional[str | re.Pattern], optional): A filter to apply to file names. Defaults to None.

        Returns:
            bool: True if processing was successful, False otherwise.
        """
        iterable = iterable() if callable(iterable) else iterable
        self.__process(iterable, actions, self.in_memory, file_filter)
    
    def repeat(self, iterableProvider: IterableProvider, actions: Action|Sequence[Action], file_filter: Optional[str|re.Pattern] = None, max_repeat=5):
        """
        Repeats the processing of items provided by the iterableProvider until no changes left. 
        Up to a maximum number of times.

        Args:
            iterableProvider (IterableProvider): A provider that yields items to be processed.
            actions (Action | Sequence[Action]): A single action or a sequence of actions to be performed on each item.
            file_filter (Optional[str | re.Pattern], optional): A filter to apply to the files being processed. Defaults to None.
            max_repeat (int, optional): The maximum number of times to repeat the processing. Defaults to 5.

        Returns:
            bool: True if the processing still yields changes, False otherwise.
        """
        self.__process(iterableProvider(), actions, self.in_memory, file_filter, max_repeat)

    def __process(self, iterable: Iterable[tuple[ASTFactory[ASTNodeType], ASTNodeType]], actions: Action|Sequence[Action], in_memory=False, file_filter: Optional[str|re.Pattern] = None, max_repeat=1) -> None:
        filter_pattern = file_filter if isinstance(file_filter, re.Pattern) else re.compile(file_filter) if file_filter!=None else None      

        def is_eligible(item: tuple[ASTFactory[ASTNodeType], ASTNodeType]) -> bool:
            return BatchASTProcessor.__eligible_file(filter_pattern, item)
        
        actions = actions if isinstance(actions, Sequence) else [actions] 
        # use parallel processing possible here
        partial_process_item = partial(process_atu, self=self, actions=actions, in_memory=in_memory, max_repeat=max_repeat)

        for atu in filter( is_eligible, iterable):
            partial_process_item(atu) # TODO us 
        # with multiprocessing.Pool(processes=self.max_processes, ) as pool:
        #     pool._pickle = pickle # type: ignore
        #     pool.map(partial_process_item, filter( is_eligible, iterable))

    def _replace_if_in_memory( self, item: ATU )-> ATU:
        if self.in_memory and self.in_memory_files.get(item[1].get_containing_filename()):
            return  item[0], item[0].create_from_text(self.in_memory_files[item[1].get_containing_filename()], item[1].get_containing_filename())
        return item

    @staticmethod
    def __eligible_file( file_filter: Optional[re.Pattern],  item: ATU )-> bool:
        return file_filter is None or file_filter.match(item[1].get_containing_filename()) != None

def process_atu(atu: ATU, self: BatchASTProcessor, actions: Sequence[Action], in_memory: bool, max_repeat: int):
    atu = self._replace_if_in_memory(atu)   
    ast_processor = ASTProcessor(atu[1], atu[0], self.user_objects, in_memory)

    for _ in range(max_repeat):
        for action in actions:
            action(ast_processor)
        has_changed = ast_processor.has_changed()
        if not has_changed:
            return
        ast_processor = ast_processor.commit()
        if self.in_memory:
            self.in_memory_files[ast_processor.get_filename()] = ast_processor.apply_to_string()


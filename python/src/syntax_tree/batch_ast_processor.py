
from functools import partial
import concurrent.futures
import re
from typing import Any, Callable, Iterable, Optional, Sequence, TypeVar

from syntax_tree.ast_processor import ASTProcessor
from .ast_factory import ASTFactory
from .ast_node import ASTNodeType


T = TypeVar('T')

AST_FACTORY_AND_ATU = tuple[ASTFactory[ASTNodeType],ASTNodeType]
Action = Callable[[ASTProcessor],None|Callable[[],Any]]
IterableProvider = Callable[[], Iterable[AST_FACTORY_AND_ATU]]

class BatchASTProcessor():

    def __init__(self, in_memory: bool = False, max_processes=4):
        """
        Initialize the BatchASTProcessor.

        Args:
            user_objects (Optional[dict[str, Any]]): A dictionary of user-defined objects. Defaults to None.
            in_memory (bool): Flag to indicate if processing should be done in memory. Defaults to False.
            max_processes (int): The maximum number of processes to use. Defaults to 4.
        """
        self.in_memory: bool = in_memory
        self.in_memory_files : dict[str,str] ={}
        self.max_processes = max_processes

    def once(self, iterable: Iterable[AST_FACTORY_AND_ATU]|IterableProvider, actions: Action|Sequence[Action], file_filter: Optional[str|re.Pattern] = None):
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_processes) as executor:
            for results in executor.map(partial_process_item, filter( is_eligible, iterable)):
                for callable in results:
                    # the post processing is done in the main thread
                    callable()

    def _replace_if_in_memory( self, item: AST_FACTORY_AND_ATU )-> AST_FACTORY_AND_ATU:
        if self.in_memory and self.in_memory_files.get(item[1].get_containing_filename()):
            return  item[0], item[0].create_from_text(self.in_memory_files[item[1].get_containing_filename()], item[1].get_containing_filename())
        return item

    @staticmethod
    def __eligible_file( file_filter: Optional[re.Pattern],  item: AST_FACTORY_AND_ATU )-> bool:
        return file_filter is None or file_filter.match(item[1].get_containing_filename()) != None

def process_atu(atu: AST_FACTORY_AND_ATU, self: BatchASTProcessor, actions: Sequence[Action], in_memory: bool, max_repeat: int) -> Sequence[Callable[[],None]]:
    atu = self._replace_if_in_memory(atu)   
    ast_processor = ASTProcessor(atu[1], atu[0], in_memory)
    results: Sequence[Callable[[], None]] = []

    for repeat in range(max_repeat):
        for action in actions:
            ast_processor.repeat_step = repeat
            result = action(ast_processor)
            if result:
                results.append(result)
        has_changed = ast_processor.has_changed()
        if not has_changed:
            return results
        ast_processor = ast_processor.commit()
        if self.in_memory:
            self.in_memory_files[ast_processor.get_filename()] = ast_processor.apply_to_string()
    return results


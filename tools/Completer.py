"""
Nestedcompleter for completion of hierarchical data structures.
"""
from typing import Any, Dict, Iterable, Mapping, Optional, Set, Union, Tuple, Callable, List
import os
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.completion.word_completer import WordCompleter
from prompt_toolkit.document import Document

__all__ = ["NestedCompleter", "PathCompleter"]

# NestedDict = Mapping[str, Union['NestedDict', Set[str], None, Completer]]
NestedDict = Mapping[str, Union[Any, Set[str], None, Completer]]


class NestedCompleter(Completer):
    """
    Completer which wraps around several other completers, and calls any the
    one that corresponds with the first word of the input.

    By combining multiple `NestedCompleter` instances, we can achieve multiple
    hierarchical levels of autocompletion. This is useful when `WordCompleter`
    is not sufficient.

    If you need multiple levels, check out the `from_nested_dict` classmethod.
    """

    def __init__(
            self, options: Dict[str, Optional[Completer]], ignore_case: bool = True, meta_dict=None
    ) -> None:

        self.options = options
        self.ignore_case = ignore_case
        self.meta_dict = meta_dict or dict()

    def __repr__(self) -> str:
        return "NestedCompleter(%r, ignore_case=%r, meta_dict=%r)" % (self.options, self.ignore_case, self.meta_dict)

    @classmethod
    def from_nested_dict(cls, data: NestedDict, meta_dict=None):  # -> "NestedCompleter"
        """
        Create a `NestedCompleter`, starting from a nested dictionary data
        structure, like this:

        .. code::
            {
                'name': ('description', Completer/ None/ Dict )
            }
            data = {
                'show':
                    'version': None,
                    'interfaces': None,
                    'clock': None,
                    'ip': {'interface': {'brief'}}
                }),
                'exit': None
                'enable': None
            }

        The value should be `None` if there is no further completion at some
        point.

        Values in this data structure can be a completers as well.
        """

        options: Dict[str, Optional[Completer]] = {}
        meta_dict = meta_dict or dict()
        for key, descr_n_compl in data.items():
            description = descr_n_compl[0]
            meta_dict.update({key: description})
            value = descr_n_compl[1]
            if isinstance(value, Completer):
                options[key] = value
            elif isinstance(value, dict):
                options[key] = cls.from_nested_dict(value)
            else:
                assert value is None
                options[key] = None
        return cls(options, meta_dict=meta_dict)

    def get_completions(
            self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        # Split document.
        text = document.text_before_cursor.lstrip()
        stripped_len = len(document.text_before_cursor) - len(text)
        # If there is a space, check for the first term, and use a
        # subcompleter.
        if " " in text:
            first_term = text.split()[0]
            # description = self.options.get(first_term)
            completer = self.options.get(first_term)

            remaining_text = text[len(first_term):].lstrip()
            move_cursor = len(text) - len(remaining_text) + stripped_len

            new_document = Document(
                remaining_text,
                cursor_position=document.cursor_position - move_cursor,
            )
            if isinstance(completer, NestedCompleter):
                for c in completer.get_completions(new_document, complete_event):
                    yield c
            else:
                for c in completer.get_completions(new_document, complete_event):
                    yield c

        # No space in the input: behave exactly like `WordCompleter`.
        else:
            completer = WordCompleter(
                list(self.options.keys()), ignore_case=self.ignore_case, meta_dict=self.meta_dict
            )
            for c in completer.get_completions(document, complete_event):
                yield c


class PathCompleter(Completer):
    """
    Complete for Path variables.

    :param get_paths: Callable which returns a list of directories to look into
                      when the user enters a relative path.
    :param file_filter: Callable which takes a filename and returns whether
                        this file should show up in the completion. ``None``
                        when no filtering has to be done.
    :param min_input_len: Don't do autocompletion when the input string is shorter.
    """

    def __init__(
            self,
            only_directories: bool = False,
            get_paths: Optional[Callable[[], List[str]]] = None,
            file_filter: Optional[Callable[[str], bool]] = None,
            min_input_len: int = 0,
            expanduser: bool = False,
    ) -> None:

        self.only_directories = only_directories
        self.get_paths = get_paths or (lambda: ["."])
        self.file_filter = file_filter or (lambda _: True)
        self.min_input_len = min_input_len
        self.expanduser = expanduser

    def get_completions(
            self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        text = document.text_before_cursor

        # Complete only when we have at least the minimal input length,
        # otherwise, we can too many results and autocompletion will become too
        # heavy.
        if len(text) < self.min_input_len:
            return

        try:
            # Do tilde expansion.
            if self.expanduser:
                text = os.path.expanduser(text)

            # Directories where to look.
            dirname = os.path.dirname(text)
            if dirname:
                directories = [
                    os.path.dirname(os.path.join(p, text)) for p in self.get_paths()
                ]
            else:
                directories = self.get_paths()

            # Start of current file.
            prefix = os.path.basename(text)

            # Get all filenames.
            filenames = []
            for directory in directories:
                # Look for matches in this directory.
                if os.path.isdir(directory):
                    for filename in os.listdir(directory):
                        if filename.startswith(prefix):
                            filenames.append((directory, filename))

            # Sort
            filenames = sorted(filenames, key=lambda k: k[1])

            # Yield them.
            for directory, filename in filenames:
                completion = filename[len(prefix):]
                full_name = os.path.join(directory, filename)

                if os.path.isdir(full_name):
                    # For directories, add a slash to the filename.
                    # (We don't add them to the `completion`. Users can type it
                    # to trigger the autocompletion themselves.)
                    filename += "/"
                elif self.only_directories:
                    continue

                if not self.file_filter(full_name):
                    continue

                yield Completion(completion, 0, display=filename)
        except OSError:
            pass

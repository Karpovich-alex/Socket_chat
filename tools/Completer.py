"""
Nestedcompleter for completion of hierarchical data structures.
"""
from typing import Any, Dict, Iterable, Mapping, Optional, Set, Union, Tuple

from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.completion.word_completer import WordCompleter
from prompt_toolkit.document import Document

__all__ = ["NestedCompleter"]

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
        self, options: Dict[str, Optional[Completer]], *meta_dict, ignore_case: bool = True
    ) -> None:

        self.options = options
        self.ignore_case = ignore_case
        self.meta_dict = meta_dict

    def __repr__(self) -> str:
        return "NestedCompleter(%r, ignore_case=%r)" % (self.options, self.ignore_case)

    @classmethod
    def from_nested_dict(cls, data: NestedDict) :#-> "NestedCompleter"
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
        point. If all values in the dictionary are None, it is also possible to
        use a set instead.

        Values in this data structure can be a completers as well.
        """

        options: Dict[str, Optional[Completer]] = {}
        meta_dict = dict()
        for key, descr_n_compl in data.items():
            description = descr_n_compl[0]
            meta_dict.update({key: description})
            value = descr_n_compl[1]
            if isinstance(value, Completer):
                options[key] = value
            elif isinstance(value, dict):
                options[key], sup_dict = cls.from_nested_dict(value)
                meta_dict.update(sup_dict)
            elif isinstance(value, set):
                options[key], sup_dict = cls.from_nested_dict({item: None for item in value})
                meta_dict.update(sup_dict)
            else:
                assert value is None
                options[key] = None
        print(options)
        return cls(options), meta_dict

    def __call__(self, m_dict):
        self.meta_dict = m_dict

    def get_completions(
        self, document: Document, complete_event: CompleteEvent, m_dict: Dict=dict()
    ) -> Iterable[Completion]:
        # Split document.
        text = document.text_before_cursor.lstrip()
        stripped_len = len(document.text_before_cursor) - len(text)
        if m_dict:
            self.meta_dict=m_dict
        # If there is a space, check for the first term, and use a
        # subcompleter.
        if " " in text:
            first_term = text.split()[0]
            description = self.options.get(first_term)
            completer = self.options.get(first_term)
            # If we have a sub completer, use this for the completions.
            if completer is not None:
                remaining_text = text[len(first_term) :].lstrip()
                move_cursor = len(text) - len(remaining_text) + stripped_len

                new_document = Document(
                    remaining_text,
                    cursor_position=document.cursor_position - move_cursor,
                )
                if isinstance(completer,NestedCompleter):
                    for c in completer.get_completions(new_document, complete_event, m_dict=self.meta_dict):
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

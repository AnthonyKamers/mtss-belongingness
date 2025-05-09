from typing import Dict, Union, List


class Block:
    def __init__(self, content: any = None, name: Union[None, str] = None,
                 attributes: Union[None, Dict[str, any]] = None, level: Union[None, int] = None):
        self.name = name
        self.level = level
        self.content = None
        self.attributes = None

        # check empty values passed as argument
        if content is not None:
            if isinstance(content, str) and content.strip() == '':
                self.content = None
            else:
                self.content = str(content)

        if attributes is not None:
            if isinstance(attributes, dict) and attributes == {}:
                self.attributes = None
            else:
                self.attributes = attributes

    def __str__(self):
        string_list: List[str] = []

        if self.level is not None:
            string_list.append(str(self.level))
        if self.name is not None:
            string_list.append(self.name)
        if self.attributes is not None:
            string_list.append(str(self.attributes))
        if self.content is not None:
            string_list.append(str(self.content))

        return '|'.join(string_list)

    def __len__(self):
        return len(str(self))

from typing import List

import sqlalchemy.types as types


class RolesChoice(types.TypeDecorator):
    impl = types.String

    def __init__(self, choices: List[str], **kwargs):
        super().__init__(**kwargs)

        self.choices = choices

    def process_bind_param(self, value, dialect):
        return [role for role in self.choices if role == value][0]

    def process_result_value(self, value, dialect):
        value_index = self.choices.index(value)

        return self.choices[value_index]

from datetime import date, datetime
from decimal import Decimal


class Base(object):
    """
    The base object that all models inherit from.
    Right now its sole purpose is to handle JSON serialization.
    """

    def json_serialize(self, keys=None):
        """
        Params:
            keys (array, optional): The object's properties to serialize.
            Defaults to json_keys() if parameter is not specified.

        Returns:
            (dictionary): All properties specified in json_short_keys()

        Raises:
            None
        """
        keys_filter = keys or self.json_keys()
        current_dict = self.__dict__
        new_dict = {}
        for item in current_dict:
            if item in keys_filter:
                if isinstance(current_dict.get(item), (datetime, date)):
                    current_dict[item] = current_dict.get(item).isoformat()
                elif isinstance(current_dict.get(item), (Decimal)):
                    current_dict[item] = str(current_dict.get(item))
                new_dict[item] = current_dict[item]

        return new_dict

    def json_keys(self):
        """
        Params:
            None

        Returns:
            (array): Strings representing properties for json_serialize()

        Raises:
            None
        """
        return []


def schema():
    schema = {
        "type": "object",
        "properties": {
            "attribute_id": {"type": "integer", "maximum": 4294967295},
            "name": {"type": "string", "minLength": 1, "maxLength": 50},
            "quantity": {"type": "integer", "maximum": 255}
        }
    }

    return schema

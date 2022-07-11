from typing import Any, Dict

from gema.dest import Dest
from gema.enums import DestType
from gema.schema import Model
from gema.utils import camel_to_snake


class Pydantic(Dest):
    template_file = "pydantic.jinja2"
    type = DestType.pydantic

    def __init__(self, model: Model, optional: bool = False, snake_case: bool = False):
        super().__init__(model)
        self.snake_case = snake_case
        self.optional = optional

    def _parse_model(self, imports: set[str], models: Dict[str, Any], model: Model):
        fields = []
        for field in model.fields:
            name = field.name
            snake_case_name = name
            if self.snake_case:
                snake_case_name = camel_to_snake(name)
            if isinstance(field.type, Model):
                type_ = f"'{name.title()}'"
                models[name.title()] = self._parse_model(imports, models, field.type)
            elif isinstance(field.type, list):
                imports.add("from typing import List")
                if isinstance(field.type[0], Model):
                    type_ = f"List['{name.title()}']"
                    models[name.title()] = self._parse_model(imports, models, field.type[0])
                else:
                    type_ = f"List[{field.type[0].__name__}]"
            elif field.type is Any:
                imports.add("from typing import Any")
                type_ = "Any"
            else:
                type_ = field.type.__name__
            if self.optional:
                type_ = f"Optional[{type_}]"
                imports.add("from typing import Optional")
            if name != snake_case_name:
                imports.add("from pydantic import Field")
                field_str = f"{snake_case_name}: {type_} = Field(..., alias='{name}')"
            else:
                field_str = f"{snake_case_name}: {type_}"
            fields.append(field_str)
        return fields

    def render(self):
        model = self.model
        imports = set()
        models = {}
        models["Model"] = self._parse_model(imports, models, model)
        return self.template.render(models=models, imports=sorted(imports))
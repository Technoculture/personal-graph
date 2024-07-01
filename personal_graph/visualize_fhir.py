import os
import pkgutil
import fhir.resources
import inspect
from importlib import import_module


def extract_classes_properties():
    """
    This method will fetch all the classes along with their properties and saves it in a dictionary
    @return: class_info: Dict
    """
    pkgpath = os.path.dirname(fhir.resources.__file__)

    class_info = {}
    for _, module_name, is_dir in pkgutil.iter_modules([pkgpath]):
        if not is_dir:
            try:
                module = import_module(f"fhir.resources.{module_name}")
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and not obj.__module__.startswith(
                        "pydantic"
                    ):
                        class_properties = (
                            {k: v for k, v in obj.__annotations__.items()}
                            if hasattr(obj, "__annotations__")
                            else {}
                        )
                        class_info[name] = class_properties

            except ModuleNotFoundError:
                pass

    return class_info


print(extract_classes_properties())

from .stackWidget2 import stackWidget2

# we need this code to auto populate stack/map plugins
# see: 

# from inspect import isclass
# from pkgutil import iter_modules
# from pathlib import Path
# from importlib import import_module

# from pymapmanager._logger import logger

# # iterate through the modules in the current package
# package_dir = Path(__file__).resolve().parent
# for (_, module_name, _) in iter_modules([package_dir]):

#     # import the module and iterate through its attributes
    
#     logger.info(f'module_name:{module_name}')
#     print(f'module_name:{module_name}')

#     module = import_module(f"{__name__}.{module_name}")
#     for attribute_name in dir(module):
#         attribute = getattr(module, attribute_name)

#         if isclass(attribute):        

#             try:
#                 _widgetName = attribute._widgetName  # myHumanName is a static str
#             except (AttributeError) as e:
#                 # not a pmmWidget !
#                 # logger.info(e)
#                 continue
            
#             # don't add widgets with no specific name
#             if _widgetName == 'not assigned':
#                 continue

#             # don't add widgets with no specific name
#             if _widgetName == 'Stack Widget':
#                 continue


#             # Add the class to this package's variables
#             logger.info(f'   adding globals()["{attribute_name}"] = {attribute}')
#             print(f'   adding globals()["{attribute_name}"] = {attribute}')
#             globals()[attribute_name] = attribute
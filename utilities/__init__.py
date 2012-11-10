def test_number(num, tuple=()):
  if not isinstance(num, int) and not isinstance(num, float):
    return False
  elif len(tuple) is 2 and tuple[0] is not None and num < tuple[0]:
    return False
  elif len(tuple) is 2 and tuple[1] is not None and num > tuple[1]:
    return False
  else:
    return True

def test_integer(num, tuple=()):
  if not test_number(num, tuple):
    return False
  else:
    return True

def test_float(num, tuple=()):
  if not test_number(num, tuple):
    return False
  else:
    return True

def test_string(string, tuple=()):
  if not isinstance(string, str) and not isinstance(string, unicode):
    return False
  elif len(tuple) is 2 and tuple[0] is not None and len(string) < tuple[0]:
    return False
  elif len(tuple) is 2 and tuple[1] is not None and len(string) > tuple[1]:
    return False
  else:
    return True

lambdas = {
  'number': test_number,
  'integer': test_integer,
  'float': test_float,
  'string': test_string,
  'boolean': lambda x: isinstance(x, bool),
  'list': lambda x: isinstance(x, list),
  'dict': lambda x: isinstance(x, dict),
  'file': lambda x: True,
}

def shim_schema(cls, schema):
  output_schema = {}
  dummy_schema = cls.get_dummy_schema()
  for key, value in cls.validation.iteritems():
    if key not in schema:
      output_schema[key] = dummy_schema[key]

    else:
      if isinstance(value, str) or isinstance(value, unicode):
        if lambdas[value](schema[key]):
          output_schema[key] = schema[key]
        else:
          output_schema[key] = dummy_schema[key]
      elif isinstance(value, tuple):
        if lambdas[value[0]](schema[key], tuple=value[1]):
          output_schema[key] = schema[key]
        else:
          output_schema[key] = dummy_schema[key]
      elif hasattr(value, '__call__'):
        if value(schema[key]):
          output_schema[key] = schema[key]
        else:
          output_schema[key] = dummy_schema[key]
      else:
        output_schema[key] = dummy_schema[key]
  return output_schema

def filter_valid(cls, schema):
  output_schema = {}
  for key, value in cls.validation.iteritems():
    if key in schema:
      if isinstance(value, str) or isinstance(value, unicode):
        if lambdas[value](schema[key]):
          output_schema[key] = schema[key]
      elif isinstance(value, tuple):
        if lambdas[value[0]](schema[key], tuple=value[1]):
          output_schema[key] = schema[key]
      elif hasattr(value, '__call__'):
        if value(schema[key]):
          output_schema[key] = schema[key]
  return output_schema

def is_different(obj, schema):
  different = False
  for key in obj.__class__.validation:
    if key in schema and getattr(obj, key) != schema[key]:
      different = True
  return different


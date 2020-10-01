import re
import sys

SLUG_REGEX = r'^[a-zA-Z][-a-zA-Z0-9]+$'
MODULE_REGEX = r'^[a-zA-Z][_a-zA-Z0-9]+$'

project_slug = '{{ cookiecutter.project_slug }}'

if not re.match(SLUG_REGEX, project_slug):
    print('ERROR: %s is not a valid project slug. Slug can only contain letters, digits, '
          'and dashes.' % project_slug)
    sys.exit(1)

if len(project_slug) > 28:
    print('ERROR: %s is a too long project slug. Maximum length is 28 characters '
          '(e.g., "%s").' % (project_slug, project_slug[:28]))
    sys.exit(1)

module_name = '{{ cookiecutter.code_directory }}'

if not re.match(MODULE_REGEX, module_name):
    print('ERROR: %s is not a valid Python module name. Module name can only contain '
          'letters, digits, and underscores.' % module_name)
    sys.exit(1)

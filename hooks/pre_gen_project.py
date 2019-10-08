import re
import sys


MODULE_REGEX = r'^[_a-zA-Z][_a-zA-Z0-9]+$'

project_slug = '{{ cookiecutter.project_slug }}'

if not re.match(MODULE_REGEX, project_slug):
    print('ERROR: %s is not a valid project slug. Slug can only contain letters, digits'
          ' and underscores.' % project_slug)

    # exits with status 1 to indicate failure
    sys.exit(1)

if len(project_slug) > 28:
    print('ERROR: %s is a too long project slug. Maximum length is 28 characters '
          '(e.g., "%s").' % (project_slug, project_slug[:28]))

    # exits with status 1 to indicate failure
    sys.exit(1)

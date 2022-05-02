# {{ cookiecutter.project_name }}

{% if cookiecutter.project_description %}## Project description{%- endif %}
{{ cookiecutter.project_description }}

## Quick Start

Sign up at [neu.ro](https://neu.ro) and setup your local machine according to [instructions](https://docs.neu.ro/).

Then run:

```shell
pip install -U neuro-cli neuro-flow
neuro login
neuro-flow build train
neuro-flow run jupyter
```

See [Help.md](HELP.md) for the detailed Neuro Project Template Reference.

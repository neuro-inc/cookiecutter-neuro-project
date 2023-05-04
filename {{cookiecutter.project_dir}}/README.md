# {{ cookiecutter.flow_name }}

{% if cookiecutter.flow_description %}## Flow description{%- endif %}
{{ cookiecutter.flow_description }}

## Quick Start

Sign up at [neu.ro](https://neu.ro) and setup your local machine according to [instructions](https://docs.neu.ro/).

Then run:

```shell
pip install -U pipx
pipx install neuro-all
neuro login
neuro-flow build train
neuro-flow run jupyter
```

See [Help.md](HELP.md) for the detailed Neuro Project Template Reference.

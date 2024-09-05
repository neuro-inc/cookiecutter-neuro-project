# {{ cookiecutter.flow_name }}

{% if cookiecutter.flow_description %}## Flow description{%- endif %}
{{ cookiecutter.flow_description }}

## Quick Start

Sign up at [apolo](https://console.apolo.us) and setup your local machine according to [instructions](https://docs.apolo.us/).

Then run:

```shell
pip install -U pipx
pipx install apolo-all
apolo login
apolo-flow build train
apolo-flow run jupyter
```

See [Help.md](HELP.md) for the detailed flow template reference.

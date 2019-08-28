from setuptools import find_packages, setup

setup(
    name='{{cookiecutter.project_slug}}',
    packages=find_packages(),
    version='1.0.0',
    description='{{cookiecutter.project_short_description}}',
    author='{{cookiecutter.email}}',
    license='MIT',
)

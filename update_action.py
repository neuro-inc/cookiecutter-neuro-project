"""
  Scans directories for files that satisfy a specific mask and updates
  the actions' tags.
  python3 update_action.py --input “one/*.y*ml two/*.y*ml three/*.y*ml” --name mlflow
"""

import glob
import argparse
import re
from pathlib import Path
from github import Github


parser = argparse.ArgumentParser()

parser.add_argument(
    '-i', '--inputs',
    type=str, help='Input directories to scan'
)

parser.add_argument(
    '-n', '--name',
    type=str, help='Name of the action'
)


# def glob_re(pattern, strings):
#     return filter(re.compile(pattern).match, strings)

args = parser.parse_args()
inputs = args.inputs.split(' ')
name = args.name
g = Github()
repo = g.get_repo(f"neuro-actions/{name}")
tag = list(repo.get_releases())[-1].title
# tag = '2.3.4'
pattern = re.compile(f'gh:neuro-actions/{name}' + '@[a-zA-Z]{1}\d{1,2}\.\d{1,2}\.\d{1,3}')

for input in inputs:
    path = Path(input)
    for file_path in glob.iglob(input):
        with open(file_path) as file:
            s = file.read()
        ss = re.sub(pattern, f'gh:neuro-actions/{name}@{tag}', s)
        with open(file_path, "w") as file:
            file.write(s)

"""
  Scans directories for files that satisfy a specific mask and updates
  the actions' tags.
  python3 update_actions.py --input “one/*.y*ml two/*.y*ml three/*.y*ml”
"""

import argparse
import glob
import re
from github import Github
from pathlib import Path


parser = argparse.ArgumentParser()

parser.add_argument("-i", "--inputs", type=str, help="Input directories to scan")

args = parser.parse_args()
inputs = args.inputs.split(" ")
g = Github()
pattern = r"(?:gh|github):neuro-actions/\w+@[a-zA-Z]{1}\d{1,2}\.\d{1,2}\.\d{1,3}"

for input in inputs:
    path = Path(input)
    for file_path in glob.iglob(input):
        with open(file_path) as file:
            s = file.read()
        matches = re.findall(pattern, s)
        for match in matches:
            nb, nt = match.find("/"), match.find("@")
            name = match[nb + 1 : nt]
            tag = match[nt + 1 :]
            p = re.compile(match)
            try:
                repo = g.get_repo(f"neuro-actions/{name}")
                new_tag = list(repo.get_releases())[-1].title
                if tag != new_tag:
                    ss = re.sub(p, f"gh:neuro-actions/{name}@{new_tag}", s)
                    with open(file_path, "w") as file:
                        file.write(ss)
            except:
                continue

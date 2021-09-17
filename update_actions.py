"""Scans directories for files that satisfy a specific mask and updates
version tags of all actions.

Example:
    python3 update_actions.py --source “one/*.y*ml two/*.y*ml tre/*.y*ml”
"""

import glob
import argparse
import re
from pathlib import Path
from github import Github
from typing import Dict
from github.GithubException import UnknownObjectException

parser = argparse.ArgumentParser()
cache: Dict[str, str] = {}

parser.add_argument(
    '-s', '--sources',
    type=str, help='Source directories to scan'
)

args = parser.parse_args()
sources = args.sources.split(' ')
g = Github('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')
p = r"\s+action:\s*(?P<svc>[\w-]+):(?P<org>[\w-]+)/(?P<rep>[\w-]+)@(?P<ver>v[\d.]+)"
r = re.compile(p)

for source in sources:
    path = Path(source)
    for file_path in glob.iglob(source):
        n_found = 0
        n_updated = 0
        with open(file_path) as file:
            lines = file.readlines()
        lines_new = []
        for line in lines:
            match = r.match(line)
            if match:
                n_found += 1
                slug = line.split('action:')[1].strip()
                svc, org, rep, ver = match['svc'], match['org'], match['rep'], match['ver']
                rep_path = f"{match['org']}/{match['rep']}"
                if rep in cache:
                    ver_new= cache[rep]
                else:
                    try:
                        ver_new= list(g.get_repo(rep_path).get_releases())[-1].title
                        if ver != ver_new:
                            cache[rep] = ver_new
                    except UnknownObjectException as e:
                        print(f'::set-output [warning] the repo {rep_path} in file {file_path} was not found')
                        ver_new= ver
                if ver != ver_new:
                    n_updated += 1
                slug_new= f'{svc}:{org}/{rep}@{ver_new}'
                line_new= re.sub(re.compile(slug), slug_new, line)
            else:
                line_new= line
            lines_new+= [line_new]
        with open(file_path, "w") as file:
            file.write(''.join(lines_new))
        print(f'::set-output [success] {n_updated} from {n_found} actions in file {file_path} were updated')

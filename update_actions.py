"""
  Scans directories for files that satisfy a specific mask and updates
  the actions' tags.
  python3 update_actions.py --source “one/*.y*ml two/*.y*ml three/*.y*ml”
"""

import glob
import argparse
import re
from pathlib import Path
from github import Github

parser = argparse.ArgumentParser()
cache = {}

parser.add_argument(
    '-s', '--sources',
    type=str, help='Source directories to scan'
)

args = parser.parse_args()
sources = args.sources.split(' ')
g = Github()
pattern = r"\s+action:.*"

for source in sources:
    path = Path(source)
    for file_path in glob.iglob(source):
        n_actions = 0
        n_changed = 0
        with open(file_path) as file:
            s = file.read()
        lines = re.findall(pattern, s)
        for line in lines:
            slug = line.split('action:')[1].strip()
            svc_bgn, svc_end = 0, slug.find(':')
            rep_bgn, rep_end = slug.find(':') + 1, slug.find('/')
            acn_bgn, acn_end = slug.find('/') + 1, slug.find('@')
            tag_bgn, tag_end = slug.find('@') + 1, len(slug)
            svc = slug[svc_bgn:svc_end]
            rep = slug[rep_bgn:rep_end]
            acn = slug[acn_bgn:acn_end]
            tag = slug[tag_bgn:tag_end]
            p = re.compile(slug)
            try:
                rep_path = f"{rep}/{acn}"
                rep_obj = g.get_repo(rep_path)
                if tag not in cache:
                    cache[tag] = list(rep_obj.get_releases())[-1].title
                tag_ = cache[tag]
                if tag != tag_:
                    n_changed += 1
                    ss = re.sub(p, f'{svc}:{rep}/{acn}@{tag_}', s)
                    with open(file_path, "w") as file:
                        file.write(ss)
            except:
                continue
            n_actions += 1
        print(f'::set-output {n_changed}/{n_actions} in {file_path} actions were updated')

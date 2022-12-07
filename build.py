import sys
import os
from shutil import rmtree
from pathlib import Path
import argparse
from time import sleep
from subprocess import run, Popen

SAHD_BASE = Path(".")

MKDOCS_OUT = SAHD_BASE / "mkdocs.yml"
MKDOCS_IN = SAHD_BASE / "source/mkdocsIn.yml"

SRC = SAHD_BASE / "source"
DOCS = SAHD_BASE / "docs"
WORDS = DOCS / "words"
SEMANTIC_FIELDS = DOCS / "semantic_fields"
CONTRIBUTORS = DOCS / "contributors"

semantic_fields = {}
contributors = {}

def readArgs():
    parser = argparse.ArgumentParser(description='SAHD - build.py',
        usage='use "%(prog)s --help" for more information',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("action", help="make - compiles Markdown files from the source files "
                                       "\nbuild - does `make` and then generates html files from the Markdown files"
                                       "\ndocs - does `make` and then serves the docs locally and them shows them in your browser"
                                       "\ng - does `make`, and pushes the whole site to GitHub"
                                       "\n          where it will be published under <https://...>"
                                       "\n          the repo itself will also be committed and pushed to GitHub")
    parser.add_argument("commit_msg", help="Commit message", nargs='?')
    args = parser.parse_args()

    action = args.action
    commit_msg = args.commit_msg

    return action, commit_msg


# def console(msg, error=False, newline=True):
#     msg = msg[1:] if msg.startswith("\n") else msg
#     msg = msg[0:-1] if msg.endswith("\n") else msg
#     target = sys.stderr if error else sys.stdout
#     nl = "\n" if newline else ""
#     target.write(f"{msg}{nl}")
#     target.flush()


def commit(task, msg):
    run(["git", "add", "--all", "."])
    run(["git", "commit", "-m", msg])
    run(["git", "push", "origin", "master"])


def ship_docs():
    run(["mkdocs", "gh-deploy"])


def build_docs():
    run(["mkdocs", "build"])


def serve_docs():
    proc = Popen(["mkdocs", "serve"])
    sleep(4)
    run("open http://127.0.0.1:8000", shell=True)
    try:
        proc.wait()
    except KeyboardInterrupt:
        pass
    proc.terminate()

# def error(msg):
#     errors.append(msg)
#
# def showErrors():
#     for msg in errors:
#         print(f"ERROR: {msg}")
#     return len(errors)


def get_relations():

    for word in WORDS.glob("*"):
        with open(WORDS / word.name, "r") as f:
            lines = f.readlines()
            for line in lines:
                w = word.name[:word.name.index(".")].strip()
                if line.startswith("semantic_fields:") or line.startswith("contributors:"):
                    items = line[line.index(":") + 1:].split(",")
                    for item in items:
                        item = item.strip()
                        if line.startswith("semantic_fields:"):
                            if item in semantic_fields.keys():
                                semantic_fields[item] = semantic_fields[item] + [w]
                            else:
                                semantic_fields[item] = [w]
                        else:
                            if item in contributors.keys():
                                contributors[item] = contributors[item] + [w]
                            else:
                                contributors[item] = [w]

    print(semantic_fields)
    print(contributors)


def write_docs():
    config = []
    errors = []
    texts = {}


def make_docs():
    if get_relations():
        write_docs()


def main():
    action, commit_msg = readArgs()
    if not action:
        return
    elif action == "make":
        make_docs()
    elif action == "build":
        if make_docs():
            build_docs()
    elif action == "docs":
        if make_docs():
            serve_docs()
    elif action == "g":
        if make_docs():
            ship_docs()
            commit(action, commit_msg)


main()

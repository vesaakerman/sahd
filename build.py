import sys
import os
from os.path import exists, isdir
from shutil import rmtree, copytree
from pathlib import Path
import argparse
from time import sleep
from subprocess import run, Popen
from collections import OrderedDict

SAHD_BASE = Path(".")

MKDOCS_OUT = SAHD_BASE / "mkdocs.yml"
MKDOCS_IN = SAHD_BASE / "source/mkdocsIn.yml"

SRC = SAHD_BASE / "source"
DOCS = SAHD_BASE / "docs"
WORDS = SRC / "words"
SEMANTIC_FIELDS = SRC / "semantic_fields"
CONTRIBUTORS = SRC / "contributors"
WORDS_DOCS = DOCS / "words"
SEMANTIC_FIELDS_DOCS = DOCS / "semantic_fields"
CONTRIBUTORS_DOCS = DOCS / "contributors"

errors = []

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


def error(msg):
    errors.append(msg)


def show_errors():
    for msg in errors:
        print(f"ERROR: {msg}")
    return len(errors)


def get_values(line):
    return line[line.index(":") + 1:].split(",")

def get_relations():
    semantic_fields = {}
    contributors = {}

    for word in WORDS.glob("*"):
        with open(WORDS / word.name, "r") as f:
            word_english = ""
            lines = f.readlines()
            for line in lines:
                if line.startswith("word_english:"):
                    word_english = get_values(line)[0].strip()
                elif line.startswith("semantic_fields:") or line.startswith("contributors:"):
                    if not word_english:
                        error(f"{word.name}: english word not given")
                        continue
                    keys = get_values(line)
                    for key in keys:
                        key = key.strip()
                        if line.startswith("semantic_fields:"):
                            if key in semantic_fields.keys():
                                semantic_fields[key] = semantic_fields[key] + [word_english]
                            else:
                                semantic_fields[key] = [word_english]
                        else:
                            if key in contributors.keys():
                                contributors[key] = contributors[key] + [word_english]
                            else:
                                contributors[key] = [word_english]

    # sort semantic fields and contributors dictionaries
    semantic_fields_dict, contributors_dict = {}, {}
    for i in sorted(semantic_fields):
        semantic_fields_dict[i] =  sorted(semantic_fields[i])
    for i in sorted(contributors):
        contributors_dict[i] =  sorted(contributors[i])
    return semantic_fields_dict, contributors_dict


def write_words():
    if isdir(WORDS_DOCS):
        rmtree(WORDS_DOCS)
    os.mkdir(WORDS_DOCS)
    for word in WORDS.glob("*"):
        text = []
        with open(WORDS / word.name, "r") as f:
            word_english, word_hebrew = "", ""
            semantic_fields = []
            lines = f.readlines()
            for line in lines:
                if line.startswith("word_english:"):
                    word_english = get_values(line)[0].strip()
                elif line.startswith("word_hebrew:"):
                    word_hebrew = get_values(line)[0].strip()
                elif line.startswith("semantic_fields:"):
                    semantic_fields = get_values(line)
                elif "1. Statistics" in line:
                    text.append(f"# **{word_hebrew} – {word_english}**\n\n")
                    text.append("Semantic Fields:\n")
                    for sf in semantic_fields:
                        sf = sf.strip()
                        text.append(f"[{sf}](../semantic_fields/{sf}.md)    ")
                    text.append("\n\n")
                text.append(line)
        with open(WORDS_DOCS / word.name, "w") as f:
            f.write("".join(text))


def write_semantic_fields(semantic_fields_dict):
    # copytree(SEMANTIC_FIELDS, SEMANTIC_FIELDS_DOCS, dirs_exist_ok = True)

    for s_field in semantic_fields_dict:
        if not exists(f"{SEMANTIC_FIELDS_DOCS / s_field}.md"):
            with open(f"{SEMANTIC_FIELDS_DOCS / s_field}.md", 'w') as f:
                name = s_field.capitalize().replace("_", " ")
                f.write(f'<img src="../../img/banner.png" alt="banner" width="800" height="100">\n\n # **{name}**\n\n### Related words')

        # print(semantic_fields_dict[s_field])
        #     word_english, word_hebrew = "", ""
        #     semantic_fields = []
        #     lines = f.readlines()
        #     for line in lines:
        #         if line.startswith("word_english:"):
        #             word_english = get_values(line)[0].strip()
        #         elif line.startswith("word_hebrew:"):
        #             word_hebrew = get_values(line)[0].strip()
        #         elif line.startswith("semantic_fields:"):
        #             semantic_fields = get_values(line)
        #         elif "1. Statistics" in line:
        #             text.append(f"# **{word_hebrew} – {word_english}**\n\n")
        #             text.append("Semantic Fields:\n")
        #             for sf in semantic_fields:
        #                 sf = sf.strip()
        #                 text.append(f"[{sf}](../semantic_fields/{sf}.md)    ")
        #             text.append("\n\n")
        #         text.append(line)
        # with open(WORDS_DOCS / word.name, "w") as f:
        #     f.write("".join(text))


def write_docs(semantic_fields_dict, contributors_dict):
    write_words()
    write_semantic_fields(semantic_fields_dict)


def make_docs():
    semantic_fields_dict, contributors_dict = get_relations()
    write_docs(semantic_fields_dict, contributors_dict)
    show_errors()


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

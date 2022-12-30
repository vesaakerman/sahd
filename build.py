import os
from os.path import exists, isdir
from shutil import rmtree, copytree
from pathlib import Path
import argparse
from time import sleep
from subprocess import run, Popen
import csv


SAHD_BASE = Path(".")

MKDOCS_OUT = SAHD_BASE / "mkdocs.yml"
MKDOCS_IN = SAHD_BASE / "source/mkdocsIn.yml"

SRC = SAHD_BASE / "source"
DOCS = SAHD_BASE / "docs"
WORDS = SRC / "words"
SEMANTIC_FIELDS = SRC / "semantic_fields"
CONTRIBUTORS = SRC / "contributors"
MISCELLANEOUS = SRC / "miscellaneous"
WORDS_DOCS = DOCS / "words"
SEMANTIC_FIELDS_DOCS = DOCS / "semantic_fields"
CONTRIBUTORS_DOCS = DOCS / "contributors"
MISCELLANEOUS_DOCS = DOCS / "miscellaneous"

HEADER = '<html><body><img id="banner" src="/images/banner.png" alt="banner" /></body></html>\n\n'
DOWNLOAD = '<div><input id="download" title="Download/print the document" type="image" onclick="print_document()" src="/images/icons/download3.png" alt="download" /></div>'
SHEBANQ = '<div><a id="shebanq" title="Word in SHEBANQ" href="https://shebanq.ancient-data.org/hebrew/word?id=replace" target="_blank"><img src="/images/icons/shebanq.png" alt="shebanq"></a></div>'

errors = []


def read_args():
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


def commit(task, msg):
    run(["git", "add", "--all", "."])
    run(["git", "commit", "-m", msg])
    run(["git", "push", "origin", "main"])


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
    value_list = []
    values = line[line.index(":") + 1:].split(",")
    for value in values:
        if value.strip():
            value_list.append(value.strip())
    return value_list


def reverse(word):
    return "".join(reversed(word))


def convert_to_id(lex):
    return "1" + lex.replace(">", "A").replace("<", "O").replace("[", "v").replace("/", "n").replace("=", "i")


def create_shebanq_references():
    shebanq = {}

    with open('shebanq_words.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        for row in csv_reader:
            word_hebrew = row[1]
            # if word_hebrew == reverse("תִיַּב"):
            #     for i in range(len(word_hebrew)):
            #         print(ord(word_hebrew[i]))

            word_id = convert_to_id(row[0])

            key = word_hebrew[0]
            word_hebrew = reverse(word_hebrew)
            if key in shebanq.keys():
                s = set(shebanq[key].keys())
                if word_hebrew not in s:
                    shebanq[key][word_hebrew] = word_id
            else:
                shebanq[key] = {word_hebrew: word_id}
            # if word_id == "1BJTn" or word_id == "1BJTv":
            #     print(row[0])
            #     print(word_id)
            #     print(word_hebrew)
            #     for i in range(len(word_hebrew)):
            #         print(ord(word_hebrew[i]))
            #     print(shebanq[key][word_hebrew])


    # r = "תיב"
    # print(shebanq["ב"][r])
    # r = reverse("בית֜")
    # print(shebanq["ב"][r])

    return shebanq


def get_shebanq_id(word_hebrew, shebanq_dict):
    # print(word_hebrew)
    # for i in range(len(word_hebrew)):
    #     print(ord(word_hebrew[i]))
    points = (0x5B4, 0x5B5, 0x5B6, 0x5B7, 0x5B8, 0x59C, 0x5BC)
    pointless = ""
    for i in range(len(word_hebrew)):
        if not ord(word_hebrew[i]) in points:
            pointless += word_hebrew[i]
        # print(ord(word_hebrew[i]))
    first_char = pointless[len(pointless) - 1]
    if pointless in shebanq_dict[first_char]:
        # print(word_hebrew)
        # print(reverse(pointless))
        # print(shebanq_dict[first_char][pointless])
        # for i in range(len(pointless)):
        #     print(ord(pointless[i]))

        return shebanq_dict[first_char][pointless]
    else:
        return None


def get_relations():
    words, semantic_fields, contributors = {}, {}, {}

    for word in WORDS.glob("*"):
        with open(WORDS / word.name, "r") as f:
            word_english, word_hebrew = "", ""
            lines = f.readlines()
            for line in lines:
                if line.startswith("word_english:"):
                    word_english = get_values(line)[0]
                elif line.startswith("word_hebrew:"):
                    word_hebrew = get_values(line)[0]
                    key = word_hebrew[0]
                    # word_hebrew = reverse(word_hebrew)
                    if key in words.keys():
                        words[key] = words[key] + [(word_hebrew, word_english)]
                    else:
                        words[key] = [(word_hebrew, word_english)]
                elif line.startswith("semantic_fields:") or line.startswith("contributors:"):
                    if not word_english or not word_hebrew:
                        error(f"english and/or hebrew word in {word.name} metadata not given")
                        continue
                    keys = get_values(line)
                    for key in keys:
                        if line.startswith("semantic_fields:"):
                            if key in semantic_fields.keys():
                                semantic_fields[key] = semantic_fields[key] + [(word_english, word_hebrew)]
                            else:
                                semantic_fields[key] = [(word_english, word_hebrew)]
                        else:
                            if key in contributors.keys():
                                contributors[key] = contributors[key] + [(word_english, word_hebrew)]
                            else:
                                contributors[key] = [(word_english, word_hebrew)]

    # sort dictionaries
    words_dict, semantic_fields_dict, contributors_dict = {}, {}, {}
    for i in sorted(words):
        words_dict[i] = sorted(words[i], reverse=True)
    for i in sorted(semantic_fields):
        semantic_fields_dict[i] =  sorted(semantic_fields[i])
    for i in sorted(contributors):
        contributors_dict[i] =  sorted(contributors[i])

    return words_dict, semantic_fields_dict, contributors_dict


def write_words(shebanq_dict):
    if isdir(WORDS_DOCS):
        rmtree(WORDS_DOCS)
    os.mkdir(WORDS_DOCS)

    for word in WORDS.glob("*"):
        filename = word.name
        text, semantic_fields, word_english, word_hebrew, first_dashes, second_dashes = [], [], "", "", False, False
        with open(WORDS / filename, "r") as f:
            lines = f.readlines()
            for line in lines:
                if second_dashes:
                    text.append(line)
                if line.strip() == "---" and not first_dashes:
                    first_dashes = True
                elif line.startswith("word_english:"):
                    word_english = get_values(line)[0]
                elif line.startswith("word_hebrew:"):
                    word_hebrew = get_values(line)[0]
                elif line.startswith("semantic_fields:"):
                    semantic_fields = get_values(line)
                elif line.strip() == "---" and not second_dashes:
                    second_dashes = True
                    text.append(HEADER)
                    text.append(DOWNLOAD)
                    # if reverse(word_hebrew) in shebanq_dict[word_hebrew[0]]:
                    #     text.append(SHEBANQ)
                    # print(word_hebrew)
                    # if word_hebrew.startswith("בַּ"):
                    # print("word hebrew " + word_hebrew)
                    shebanq_id = get_shebanq_id(reverse(word_hebrew), shebanq_dict)
                    if shebanq_id:
                        # print("shebangid " + shebanq_id)
                        text.append(SHEBANQ.replace("replace", shebanq_id))

                    # print(word_hebrew[0])
                    # print(reverse(word_hebrew))
                    # print (shebanq_dict[word_hebrew[len(word_hebrew) - 1]] )
                    # print ("\n\n\n\n\n\n\n")
                    if not word_english or not word_hebrew:
                        error(f"Metadata for {filename} incomplete")
                    text.append(f"# **{word_hebrew} – {word_english.replace('_', ' ')}**\n\n")
                    if len(semantic_fields) > 0:
                        text.append("Semantic Fields:\n")
                        for sf in semantic_fields:
                            text.append(f"[{sf.replace('_', ' ')}](../semantic_fields/{sf}.md)&nbsp;&nbsp;&nbsp;")
                        text.append("\n\n")

        if not second_dashes:
            error(f"Metadata for {filename} incomplete")

        with open(WORDS_DOCS / filename, "w") as f:
            f.write("".join(text))


def write_semantic_fields(semantic_fields_dict):
    if isdir(SEMANTIC_FIELDS_DOCS):
        rmtree(SEMANTIC_FIELDS_DOCS)
    copytree(SEMANTIC_FIELDS, SEMANTIC_FIELDS_DOCS)

    for s_field in semantic_fields_dict:
        name = s_field.capitalize().replace("_", " ")
        words = semantic_fields_dict[s_field]

        if not exists(SEMANTIC_FIELDS_DOCS / f"{s_field}.md"):
            with open(SEMANTIC_FIELDS_DOCS / f"{s_field}.md", 'w') as f:
                f.write(f'# **{name}**\n\n')
                f.close()

        text = [HEADER]
        with open(SEMANTIC_FIELDS_DOCS / f"{s_field}.md", 'r') as f:
            lines = f.readlines()
            for line in lines:
                text.append(line)
            text.append("\n### Related words\n")
            for word in words:
                text.append(f"[{word[1]} – {word[0].replace('_', ' ')}](../words/{word[0]}.md)<br>")

        with open(SEMANTIC_FIELDS_DOCS / f"{s_field}.md", 'w') as f:
            f.write("".join(text))


def write_contributors(contributors_dict):
    if isdir(CONTRIBUTORS_DOCS):
        rmtree(CONTRIBUTORS_DOCS)
    copytree(CONTRIBUTORS, CONTRIBUTORS_DOCS)

    for contributor in contributors_dict:
        name = contributor.title().replace("_", " ")
        words = contributors_dict[contributor]

        if not exists(CONTRIBUTORS_DOCS / f"{contributor}.md"):
            with open(CONTRIBUTORS_DOCS / f"{contributor}.md", 'w') as f:
                f.write(f'# **{name}**\n\n')
                f.close()

        text = [HEADER]
        with open(CONTRIBUTORS_DOCS / f"{contributor}.md", 'r') as f:
            lines = f.readlines()
            for line in lines:
                text.append(line)
            text.append("\n### Contributions\n")
            for word in words:
                text.append(f"[{word[1]} – {word[0]}](../words/{word[0]}.md)<br>")

        with open(CONTRIBUTORS_DOCS / f"{contributor}.md", 'w') as f:
            f.write("".join(text))


def write_index_file(filename):
    text = [HEADER]
    with open(SRC / f"{filename}.md", 'r') as f:
        lines = f.readlines()
        for line in lines:
            text.append(line)

    with open(DOCS / f"{filename}.md", 'w') as f:
        f.write("".join(text))


def write_miscellaneous_file(filename):
    text = [HEADER]
    with open(MISCELLANEOUS / f"{filename}.md", 'r') as f:
        lines = f.readlines()
        for line in lines:
            text.append(line)

    with open(f"{MISCELLANEOUS_DOCS / filename}.md", 'w') as f:
        f.write("".join(text))


def write_miscellaneous():
    if isdir(MISCELLANEOUS_DOCS):
        rmtree(MISCELLANEOUS_DOCS)
    copytree(MISCELLANEOUS, MISCELLANEOUS_DOCS)

    write_miscellaneous_file("contact")
    write_miscellaneous_file("contribution")
    write_miscellaneous_file("partners")
    write_miscellaneous_file("project_description")
    write_index_file("index")


def write_navigation(words_dict, semantic_fields_dict, contributors_dict):

    text = []
    with open(SRC / "mkdocs_in.yml", 'r') as f:
        lines = f.readlines()
        for line in lines:
            text.append(line)
            if line.replace(" ", "").startswith("-Words:"):
                for letter in words_dict:
                    text.append(f"            - {letter}:\n")
                    for word in words_dict[letter]:
                        text.append(f"                - {word[0]} - {word[1].replace('_', ' ')}: words/{word[1]}.md\n")
            elif line.replace(" ", "").startswith("-Semanticfields:"):
                for s_field in semantic_fields_dict:
                    text.append(f"            - {s_field.replace('_', ' ')}: semantic_fields/{s_field}.md\n")
            elif line.replace(" ", "").startswith("-Contributors:"):
                for contributor in contributors_dict:
                    text.append(f"            - {contributor.replace('_', ' ').title()}: contributors/{contributor}.md\n")
    with open("mkdocs.yml", 'w') as f:
        f.write("".join(text))


def make_docs():
    shebanq_dict = create_shebanq_references()
    words_dict, semantic_fields_dict, contributors_dict = get_relations()
    write_words(shebanq_dict)
    write_semantic_fields(semantic_fields_dict)
    write_contributors(contributors_dict)
    write_miscellaneous()
    write_navigation(words_dict, semantic_fields_dict, contributors_dict)
    show_errors()


def main():
    action, commit_msg = read_args()
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

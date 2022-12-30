import fitz
import re
import argparse


def read_args():
    parser = argparse.ArgumentParser(description='converts .pdf file into text-file and reformats some lines to better suit Markdown in SAHD',
                                     usage='use "%(prog)s --help" for more information',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("input", help="input pdf-file")
    parser.add_argument("output", help="ouput text-file")
    args = parser.parse_args()
    input = args.input
    output = args.output

    return input, output


def convert(input, output):
    doc = fitz.open(input)
    text = ""
    i = 0
    end = False
    while not end:
        try:
            text += doc[i].get_text("text")
            i += 1
        except:
            end = True
    with open('temp.txt', "w") as fi:
        fi.write(text)

    with open(output, "w") as f:
        with open('temp.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                m = re.search(r"^ *([0-9]+\.)[ \t].*", line)
                if m:
                    line = "## " + line
                m = re.search(r"^ *([0-9]+)[ \t]*↑.*", line)
                if m:
                    line = re.sub(r"^ *([0-9]+)([ \t]*↑)(.*)", r"[^\1]: \3", line)
                f.write(line)

    print(f"{input} converted to {output}")


input, output = read_args()
convert(input, output)
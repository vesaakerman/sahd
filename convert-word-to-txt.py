import pypandoc
import argparse
import re


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

    pypandoc.convert_file(input, 'plain', outputfile="temp.txt")

    with open(output, "w") as f:
        with open('temp.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                line = re.sub(r"^ *([0-9]+).?([ \t]*↑)(.*)", r"[^\1]: \3", line)
                line = re.sub(r"^ *([0-9]+\.[ \t].*)", r"## \1", line)
                line = re.sub(r"^[ \t]*([a-zA-Z]?[0-9.]+)([ \t].*$)", r"**\1** \2", line)
                f.write(line)

    print(f"{input} converted to {output}")


input, output = read_args()
convert(input, output)
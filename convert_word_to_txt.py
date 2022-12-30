import pypandoc
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

    output = pypandoc.convert_file(input, 'plain', outputfile=output)
    print(f"{input} converted to {output}")


input, output = read_args()
convert(input, output)
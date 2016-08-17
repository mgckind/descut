#!/usr/bin/env python3
import os,sys
import fileinput
import argparse
from jsmin import jsmin


def replacein(inputfile):
    with fileinput.FileInput(inputfile, inplace=True) as file:
        for line in file:
            print(line.replace('elements.html', 'elements-built.html'), end='')
    with fileinput.FileInput(inputfile, inplace=True) as file:
        for line in file:
            print(line.replace('app.js', 'app.min.js'), end='')

def replaceout(inputfile):
    with fileinput.FileInput(inputfile, inplace=True) as file:
        for line in file:
            print(line.replace('elements-built.html', 'elements.html'), end='')
    with fileinput.FileInput(inputfile, inplace=True) as file:
        for line in file:
            print(line.replace('app.min.js', 'app.js'), end='')


def vulcanize():
    os.system('rm -f static/elements/elements-built.html')
    command = 'vulcanize static/elements/elements.html --out-html static/elements/elements-built.html'
    os.system(command)

def minimize():
    with open('static/scripts/app.js') as js_file:
        minified = jsmin(js_file.read())
    with open('static/scripts/app.min.js','w') as js_file:
        js_file.write(minified)



    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build","-b", help="vulcanize",action="store_true")
    parser.add_argument("--dev","-d", help="(de)vulcanize",action="store_true")
    args = parser.parse_args()

    if args.build:
        vulcanize()
        minimize()
        replacein('templates/index.html')
        replacein('templates/login.html')
        

    if args.dev:
        replaceout('templates/index.html')
        replaceout('templates/login.html')




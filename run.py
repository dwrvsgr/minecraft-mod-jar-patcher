from mods import *
import sys


if __name__ == '__main__':
    jar_path = '~/Downloads/ProjectE-1.20.1-PE1.0.1.jar'
    output_path = '~/Desktop'
    patcher = ProjectEPatcher(jar_path, output_path)
    patcher.apply()

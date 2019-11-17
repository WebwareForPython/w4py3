#!/usr/bin/env python3

import os
import sys


def compilePSP(*args):
    from .Context import PSPCLContext
    from .PSPCompiler import Compiler
    pspFilename = args[0]
    fil, ext = os.path.splitext(os.path.basename(pspFilename))
    classname = fil + '_' + ext
    pyFilename = classname + '.py'
    context = PSPCLContext(pspFilename)
    context.setClassName(classname)
    context.setPythonFileName(pyFilename)
    context.setPythonFileEncoding('utf-8')
    clc = Compiler(context)
    clc.compile()


if __name__ == '__main__':
    path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, path)
    from PSP.CompilePSP import compilePSP as main
    main(sys.argv[1])

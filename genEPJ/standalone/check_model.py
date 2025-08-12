#!/usr/bin/env python
# -*- coding: utf-8 -*-
"Check the provided E+ IDF's suitability for use in genEPJ: `./check_model MYBLDG.idf`"


from sys import platform, path, argv # win/linux?

path.append('genEPJ')
path.append('../genEPJ')
from generate_EPJ import check_model, get_IDF_objs_raw

# Allow for commandline use
if __name__ == '__main__':

    if len(argv)==1 :
        print("check_model requires a file to check!")
    else:
        objs=get_IDF_objs_raw(argv[1])
        check_model(objs, args={"interactive": True, "epw": 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw', "idf": argv[1]})

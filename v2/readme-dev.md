
## This is a rewrite of the original pymapmanager backend

We need to talk about all this and it should be fun !!!

To run this code you need to use my new file format and hard-drive structure of stack and annotations (maps coming later)

Here is a link to download just one stack:

https://ucdavis.box.com/s/9eajzyanuc3pvdhturt5sxse4vxz7ulw


## 1) New file formats and directory structure

Here is an example of the file directory structure for one stack (a stack is just a .tif file)

```
/media/cudmore/data/richard/rr30a/firstMap/stacks
├── rr30a_s0
│   ├── rr30a_s0_db2.txt
│   ├── rr30a_s0_Int1.txt
│   ├── rr30a_s0_Int2.txt
│   ├── rr30a_s0.json
│   ├── rr30a_s0_l.txt
│   └── rr30a_s0_user.txt
├── rr30a_s0_ch1.tif
└── rr30a_s0_ch2.tif
```

Each raw data .tif stack like rr30a_s0_ch1.tif (regardless of its hard-drive location) will have an enclosing folder (rr30a_s0) that contains all our saved files (mostly csv text files)

This is working in principal for a single stack. I call this a 'naked stack'

## 2) Directory structure of new code

I made a branch ('pymapmanager2') that has a 'v2' folder containing all the new code.

```
../v2
├── pymapmanager
│   ├── analysis
│   │   ├── __init__.py
│   │   ├── lineAnalysis.py
│   │   ├── pointAnalysis.py
│   ├── annotations
│   │   ├── baseAnnotations.py
│   │   ├── __init__.py
│   │   ├── lineAnnotations.py
│   │   ├── pointAnnotations.py
│   ├── __init__.py
│   ├── logger.py
│   ├── map.py
│   ├── plotting
│   │   ├── __init__.py
│   │   ├── plottingUtils.py
│   ├── pymapmanager.log
│   ├── stack.py
│   └── version.pytest
├── requirements.txt
├── setup.cfg
└── setup.py
```

If you grab the branch, you can do a local install and try it out

```
# not sure how to grab the branch 'pymapmanager2'
# once you grab it and make it your current branch
cd v2
python -m venv pymm2_env
source activate pymm2_env/bin/activate
pip install -e .
```

You can then run individual pieces as a simplistic 'test' ... like:

```
python pymapmanager/stack.py 
```

## 3) This is my rational for the code design

This is the core of pymapmanager, a stack and a map ...

```
../v2
├── pymapmanager
│   ├── map.py
│   ├── stack.py
```

Contains code to handle different types of annotations. Two main type are (point, line). We will extend this in the future ...

```
│   ├── annotations
│   │   ├── baseAnnotations.py
│   │   ├── __init__.py
│   │   ├── lineAnnotations.py
│   │   ├── pointAnnotations.py
```

Contains purely computational code, lots of numpy and math. So we do not contaminate our other code with lengthy functions.

```
├── pymapmanager
│   ├── analysis
│   │   ├── __init__.py
│   │   ├── lineAnalysis.py
│   │   ├── pointAnalysis.py
```

Some basic plotting functions I am using as 'visual' tests ???

```
│   ├── plotting
│   │   ├── __init__.py
│   │   ├── plottingUtils.py
```






from setuptools import setup, find_packages

'''
## Pushing to PyPi

https://pypi.python.org/pypi/pymapmanager

1. Make sure there is a `~/.pypirc` file

	[distutils]
	index-servers=pypi

	[pypi]
	username=your_username
	password=your_password

2. [old] Update version in `PyMapManager/setup.py`

      version='0.1.1',

3. Makes .tar.gz in `dist/`

	python setup.py sdist
	
4. Push to PyPi website

	python setup.py sdist upload

## Notes:
    `requests` is required by pymapmanager.mmio
'''

exec (open('pymapmanager/version.py').read())

setup(
    name='pymapmanager',
    version=__version__,
    description='Load, analyze, and visualize Map Manager files',
    url='http://github.com/pymapmanager/PyMapManager',
    author='Robert H Cudmore',
    author_email='robert.cudmore@gmail.com',
    license='GNU GPLv3',
    #packages = find_packages(),
    packages=find_packages(include=['pymapmanager',
                            'pymapmanager.*',
                            'pymapmanager.annotations',
                            'pymapmanager.interface',
                            'pymapmanager.interface2',
                            'pymapmanager.interface2.stackWidgets',
                            'pymapmanager.interface2.mapWidgets',
                            ]),
    #packages = find_packages(exclude=['version']),
    #packages=[
    #    'pymapmanager',
    #    'pymapmanager.mmio'
    #],
    install_requires=[
        "numpy==1.23.4",
        "pandas",
        "scipy",
        "scikit-image",
        "tifffile",
        "geopandas",
        "shapely",
        "platformdirs",
        "brightest-path-lib",
    ],

	extras_require={
        'gui': [
			'matplotlib',
			'seaborn',
            'qtpy',
            'PyQt5',  # This will not work on macOS arm
            'pyqtgraph',
            'pyqtdarktheme',
		],

        'napari': [
            'napari',
            'napari-layer-table'
        ],

        'docs': [
			'mkdocs',
			'mkdocs-material',
			'mkdocs-jupyter',
            'mkdocstrings',
            'mkdocstrings-python', # resolve error as of April 30, 2023
        ],

        'dev': [
			'mkdocs',
			'mkdocs-material',
			'mkdocs-jupyter',
            'mkdocstrings',
            'tornado', # needed for pyinstaller
            'pyinstaller',
            'ipython',
            'jupyter',
            'pytest',
            'pytest-qt',
            'flake8'
		],
        
        'test': [
            'pytest',
            'pytest-cov',
            'pytest-qt',
            'flake8',
        ]
    },

)


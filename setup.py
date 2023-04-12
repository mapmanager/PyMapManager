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
                            'pymapmanager.*', 'pymapmanager.annotations',
                            'pymapmanager.interface']),
    #packages = find_packages(exclude=['version']),
    #packages=[
    #    'pymapmanager',
    #    'pymapmanager.mmio'
    #],
    install_requires=[
        "numpy",
        "pandas",
        "scipy",
        "scikit-image",
        "tifffile",
    ],
	extras_require={
        'gui': [
			'matplotlib',
            'pyqtgraph',
			#'PyQt5==5.12 # 5.12 is only version where QComboBox works # 5.15.2',
			'PyQt5',
			#'qdarkstyle',
            'pyqtdarktheme',
		],
        'napari': [
            'napari',
            'napari-layer-table'
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
            'flake8'
		],
    },

)


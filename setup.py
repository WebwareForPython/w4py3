import setuptools

with open('webware/Properties.py') as f:
    properties = {}
    exec(f.read(), properties)
    version = properties['version']
    version = '.'.join(map(str, version[:3])) + '.'.join(version[3:])
    description = properties['synopsis']

with open('README.md') as fh:
    long_description = fh.read()

requireDev = [
    'Pygments>=2.7,<3', 'WebTest>=2.0,<3',
    'waitress>=1.4.4,<2', 'hupper>=1.10,<2',
]
requireDocs = [
    'Sphinx>=3,<4', 'sphinx_rtd_theme>=0.5'
]
requireExamples = [
    'DBUtils>=2,<4', 'dominate>=2.6,<3', 'yattag>=1.14,<2',
    'Pygments>=2.7,<3', 'Pillow>=8,<9'
]
requireTests = [
    'psutil>=5.8,<6', 'flake8>=3.8,<4', 'pylint>=2.6,<3', 'tox>=3.21,<4',
    'pywin32>=300,<400;'
    'sys_platform=="win32" and implementation_name=="cpython"'
] + requireDev + requireDocs + requireExamples


setuptools.setup(
    name='Webware-for-Python',
    version=version,
    author='Christoph Zwerschke et al.',
    author_email='cito@online.de',
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='web framework servlets',
    url='https://webwareforpython.github.io/w4py3/',
    project_urls={
        'Source': 'https://github.com/WebwareForPython/w4py3',
        'Issues': 'https://github.com/WebwareForPython/w4py3/issues',
        'Documentation': 'https://webwareforpython.github.io/w4py3/',
    },
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: OS Independent',
    ],
    extras_require={
        'dev': requireDev,
        'docs': requireDocs,
        'examples': requireExamples,
        'tests': requireTests,
    },
    entry_points={
        'console_scripts': [
            'webware = webware.Scripts.WebwareCLI:main'
        ],
        'webware.plugins': [
            'MiscUtils = webware.MiscUtils',
            'PSP = webware.PSP',
            'TaskKit = webware.TaskKit',
            'UserKit = webware.UserKit',
            'WebUtils = webware.WebUtils'
        ]
    }
)

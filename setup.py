from setuptools import setup

setup(
    name="nhs_winter_sitrep",
    version='0.0.1',
    py_modules=['nhs_winter_sitrep'],
    install_requires=[
        'Click',
        'requests',
        'xlrd',
        'pandas',
        'beautifulsoup4',
        'html5lib'
    ],
    entry_points='''
        [console_scripts]
        nhs_winter_sitrep=nhs_winter_sitrep:cli
    ''',
)
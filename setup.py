from setuptools import setup, find_namespace_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

includes = [
    "myproject",
]

setup(
    name="myproject",
    version='1.0.0',
    packages=find_namespace_packages(include=includes),
    description="Myproject",
    install_requires=[],
    entry_points='''
        [console_scripts]
        myproject-cli=myproject.cli:cli
    ''',
)

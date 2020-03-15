import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

with open("requirements.txt") as f:
    requirements = [package for package in f.readlines()]

setuptools.setup(
    name="Flask Utils",
    version="0.0.1",
    author="Vitaliy Levitski",
    author_email="vitaliylevitskiand@gmail.com",
    description="Tool library for simple Flask applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vitaliylevitskiand/flask-utils",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=(
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
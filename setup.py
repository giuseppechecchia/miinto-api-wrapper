from setuptools import setup
import pathlib

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()


# This call to setup() does all the work
setup(
    name="miinto-api-wrapper",
    version="1.1.0",
    description="A simple and stupid Miinto API wrapper",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/giuseppechecchia/miinto-api-wrapper",
    author="Giuseppe Checchia",
    author_email="giuseppechecchia@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
    ],
    packages=['miintoapi'],
    python_requires='>=3.6',
    include_package_data=True,
    install_requires=["urlparse2"],
)

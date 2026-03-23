from setuptools import setup

setup(
    name="py-resounding-libraries",
    version="0.1.0",
    description="Python package from Resounding Libraries research cluster",
    url="https://github.com/NicholasCorniaOrpheus/py-resouding-libraries",
    author="Nicholas Cornia",
    author_email="nicholas.cornia@orpheusinstituut.be",
    requires_python=">=3.1",
    keywords=[
        "koha",
        "MARC",
        "API",
        "Omeka S",
        "Transkribus",
        "Wikidata",
        "Linked Open Data",
        "library software",
    ],
    license="MIT License",
    dependencies=["requests"],
    packages=["py-resounding-libraries"],
    install_requires=["numpy"],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.1",
    ],
)

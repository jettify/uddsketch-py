import os

from setuptools import find_packages, setup


def _read(f):
    with open(os.path.join(os.path.dirname(__file__), f)) as f_:
        return f_.read().strip()


classifiers = [
    "License :: OSI Approved :: Apache Software License",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Operating System :: OS Independent",
    "Development Status :: 3 - Alpha",
    "Topic :: Scientific/Engineering",
    "Topic :: Software Development :: Libraries",
]

keywords = ["uddsketch", "ddsketch"]

project_urls = {
    "Website": "https://github.com/jettify/uddsketch",
    "Documentation": "https://uddsketch.readthedocs.io",
    "Issues": "https://github.com/jettify/uddsketch/issues",
}

setup(
    name="uddsketch",
    description=("uddsketch"),
    long_description="\n\n".join((_read("README.rst"), _read("CHANGES.rst"))),
    long_description_content_type="text/x-rst",
    classifiers=classifiers,
    platforms=["POSIX"],
    author="Nikolay Novik",
    author_email="nickolainovik@gmail.com",
    url="https://github.com/jettify/uddsketch-py",
    download_url="https://pypi.org/project/uddsketch/",
    license="Apache 2",
    packages=find_packages(exclude=("tests",)),
    install_requires=[],
    setup_requires=[
        "setuptools>=45",
        "setuptools_scm",
        "setuptools_scm_git_archive",
        "wheel",
    ],
    keywords=keywords,
    zip_safe=True,
    include_package_data=True,
    project_urls=project_urls,
    python_requires=">=3.7.0",
    use_scm_version=True,
)

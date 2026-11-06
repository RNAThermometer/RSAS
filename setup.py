from setuptools import setup, find_packages

try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "RSAS: RNA Structure Analysis Suite"

try:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [
            line.split("#", 1)[0].strip() for line in fh
            if line.split("#", 1)[0].strip()
        ]
except FileNotFoundError:
    requirements = []

setup(
    name="RSAS",
    version="4.0.0",
    author="Roy Vaknin",
    author_email="roycyber13@gmail.com",
    description="RSAS: RNA Structure Analysis Suite for identifying and analyzing RNA thermometers and regulatory structures",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RoyCyber1/RSAS",
    packages=find_packages(),
    py_modules=["main", "settings_manager"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "rsas-cli=RnaThermofinder.__main__:main",
        ],
        "gui_scripts": [
            "rsas=main:main",
        ],
    },
    include_package_data=True,
)

import setuptools
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ellipsisAI",
    version="0.1.1",
    author="Daniel van der Maas",
    author_email="daniel@ellipsis-drive.com",
    description="Package to use Ellipsis Drive for AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ellipsis-drive-internal/python-package-AI",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    install_requires=[
    'ellipsis',
    'numpy',
    'tifffile',
    'Pillow',
    'requests',
    'rasterio',
    'geopandas',
    'shapely',
    'pandas'
    ],
    python_requires='>=3.6',
)

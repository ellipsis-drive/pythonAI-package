import setuptools
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ellipsis-AI",
    version="0.0.0",
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
    'pandas',
    'ellipsis',
    'Pillow',
    'geopandas==0.9.0',
    'pyproj==3.0.1',
    'numpy',
    'requests',
    'requests-toolbelt',
    'rasterio',
    'Shapely',
    'geopy',
    'xmltodict',
    'opencv-python',
    'Fiona',
    'tifffile',
    'keras==2.2.2',
    'imagecodecs'
    ],
    python_requires='>=3.6',
)

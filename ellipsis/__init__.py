#python3 setup.py sdist bdist_wheel
#twine upload --repository pypi dist/*

import pandas as pd
from PIL import Image
import geopandas as gpd
from pyproj import Proj, transform
import base64
import numpy as np
from io import BytesIO
import time
import requests
import rasterio
from datetime import datetime
import math
import tifffile
from shapely.geometry import Polygon
from rasterio.features import rasterize
from geopy.distance import geodesic
import json
#import cv2
import sys
import os
from rasterio.io import MemoryFile
from requests_toolbelt import MultipartEncoder
import warnings
import threading

__version__ = '0.0.0'
url = 'https://api.ellipsis-drive.com/v1'

s = requests.Session()
warnings.filterwarnings("ignore")


def logIn(username, password):
        r =s.post(url + '/account/login/',
                         json = {'username':username, 'password':password} )
        if int(str(r).split('[')[1].split(']')[0]) != 200:
            raise ValueError(r.text)
            
        token = r.json()
        token = token['token']
        token = 'Bearer ' + token
        return(token)



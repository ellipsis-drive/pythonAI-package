#python3 setup.py sdist bdist_wheel
#twine upload --repository pypi dist/*

import numpy as np
import ellipsis as el
import math
from datetime import datetime
import tifffile
from io import BytesIO
import requests
import os
import rasterio
import geopandas as gpd
from shapely import geometry
import pandas as pd
from PIL import Image

__version__ = '0.0.1'
url = 'https://api.ellipsis-drive.com/v1'

s = requests.Session()


def applyModel(model, blockId, captureId, targetBlockId, inputWidth, token, temp_folder, visualizationId = None):

    inputWidth = int(inputWidth)    
    if inputWidth % 256 != 0 or inputWidth <=0:
        raise ValueError("inputWidth needs to be a multiple of 256 and must be larger than zero.")

    if type(token) != type('x'):
        raise ValueError('token must be of type string')

    token_inurl = '?token=' + token.replace('Bearer ', '')


    w = int(inputWidth / 256)

    metadata = el.metadata(blockId, False, token)
    
    if metadata['isShape']:
        raise ValueError('blockId is of type vector but must be of type raster')
    
    captures = [c for c in metadata['timestamps'] if c['id'] == captureId]
    
    if len(captures) == 0:
        raise ValueError('given captureId does not exist')
    capture = captures[0]
    timestampNumber = capture['timestamp']
    startDate = capture['dateFrom']
    endDate = capture['dateTo']
    zoom = capture['zoom']
    startDate = datetime.strptime(startDate, '%Y-%m-%dT%H:%M:%S.%fZ')
    endDate = datetime.strptime(endDate, '%Y-%m-%dT%H:%M:%S.%fZ')
    if type(visualizationId) == type(None):
        num_bands = len(metadata['bands'])
        visualizationId = 'data'
    else:
        num_bands = 4
    print('creating a capture to write in')
    targetCaptureId = el.addTimestamp(mapId = targetBlockId, startDate=startDate, endDate = endDate, token=token)['id']

    bounds = el.getBounds(blockId, timestampNumber, token)
    
    if str(type(bounds)) == "<class 'shapely.geometry.polygon.Polygon'>":
        bounds = [bounds]
    else:
        bounds = [b for b in bounds]

    output = model(np.zeros((inputWidth, inputWidth, num_bands)))
    if str(type(output)) != "<class 'numpy.ndarray'>":
        raise ValueError('Output of model funciton must be a 3 dimensional numpy array')
    
    if output.shape[0] != output.shape[1]:
        raise ValueError('First and second dimension of the resutling numpy array of model should have equal length.')
    if len(output.shape) != 3:
        raise ValueError('Output of model funciton mus ba a 3 dimensional numpy array')
        
    bands_out = output.shape[2]    
    
    bound = bounds[0]        
    for bound in bounds:
        print('applying model to first connected component')
        x1, y1, x2, y2  = bound.bounds
        x1_osm =  math.floor((x1 +180 ) * 2**zoom / 360 )
        x2_osm =  math.floor( (x2 +180 ) * 2**zoom / 360)
        y2_osm = math.floor( 2**zoom / (2* math.pi) * ( math.pi - math.log( math.tan(math.pi / 4 + y1/360 * math.pi  ) ) ))
        y1_osm = math.floor( 2**zoom / (2* math.pi) * ( math.pi - math.log( math.tan(math.pi / 4 + y2/360 * math.pi  ) ) ))        
        y1_osm = max(0,y1_osm)
        y2_osm = min(2**zoom-1,y2_osm)
        x1_osm = max(0,x1_osm)
        x2_osm = min(2**zoom-1,x2_osm)
        
        x2_extra = 10*w - (x2_osm - x1_osm+1) % (10*w)
        x2_osm = x2_osm + x2_extra
        y2_extra = 10*w- (y2_osm - y1_osm+1) % (10*w)
        y2_osm = y2_osm + y2_extra
        
        
        total = (x2_osm - x1_osm+1) * (y2_osm-y1_osm +1)
        frac = 0
        
        x = x1_osm
        while x < x2_osm:
            y=y1_osm
            while y < y2_osm:
                r_out = np.zeros(( 10*w*256, 10*w*256, bands_out))
                for N in np.arange(10):
                    for M in np.arange(10):
                        r_in = np.zeros((w*256, w*256, num_bands))
                        for i in np.arange(w):
                            for j in np.arange(w):
                                frac = frac+1
                                el.loadingBar( frac, total)
                                
                                url_req = url + '/tileService/' + blockId + '/' + str(timestampNumber) + '/' + visualizationId + '/' + str(zoom) + '/' + str(x+N*w+ i) + '/' + str(y+M*w+j) + token_inurl
                                r = s.get(url_req , timeout = 10 )
                                if int(str(r).split('[')[1].split(']')[0]) == 403:
                                        raise ValueError('insufficient access')
                                elif int(str(r).split('[')[1].split(']')[0]) != 200:
                                    print(r)
                                    r = np.zeros((256,256,num_bands))
                                elif visualizationId == 'data':
                                    r = np.transpose(tifffile.imread(BytesIO(r.content)), [1,2,0] )      
                                else:
                                   r = np.array(Image.open(BytesIO(r.content)), dtype = 'uint8')
                                r_in[256*j: 256*(j+1),256*i: 256*(i+1), :] = r
                        r_out[M*inputWidth:(M+1)*inputWidth, N*inputWidth:(N+1)*inputWidth, :] = model(r_in)
                r_out = np.transpose(r_out, [2,0,1])
                r_out = r_out.astype('float32')
                xMin = x/2**zoom *2* 2.003751e+07 - 2.003751e+07
                xMax = (x + 10*w)/2**zoom *2* 2.003751e+07 - 2.003751e+07
                yMax = (2**zoom - y)/2**zoom * 2 * 2.003751e+07 - 2.003751e+07
                yMin = (2**zoom - y - 10*w)/2**zoom * 2*2.003751e+07 - 2.003751e+07
                trans = rasterio.transform.from_bounds(xMin, yMin, xMax, yMax, r_out.shape[2], r_out.shape[1])
                crs = "EPSG:3857"
                file = temp_folder + '/' + str(frac) + ".tif"
                with rasterio.open( file, 'w', compress="lzw",
                                   tiled=True, blockxsize=256, blockysize=256, count = bands_out, width=10*inputWidth, height=10*inputWidth, dtype = 'float32', transform=trans, crs=crs) as dataset:
                    dataset.write(r_out)
                el.uploadRasterFile(mapId = targetBlockId, timestampId = targetCaptureId, file = file, token = token)
                #os.remove(file)
                y = y+10*w
                
            x = x+10*w
        print('activating timestamp')
        el.activateTimestamp(mapId = targetBlockId, timestampId=targetCaptureId, active = True, token = token)
        print('capture activated result will be available soon')


def getTiles(blockId, captureId, inputWidth, token):
    
    inputWidth = int(inputWidth)    
    if inputWidth % 256 != 0 or inputWidth <=0:
        raise ValueError("inputWidth needs to be a multiple of 256 and must be larger than zero.")

    if type(token) != type('x'):
        raise ValueError('token must be of type string')

    w = int(inputWidth / 256)

    metadata = el.metadata(blockId, False, token)
    if metadata['isShape']:
        raise ValueError('blockId is of type vector but must be of type raster')

    captures = [c for c in metadata['timestamps'] if c['id'] == captureId]
    
    if len(captures) == 0:
        raise ValueError('given captureId does not exist')
    capture = captures[0]
    timestampNumber = capture['timestamp']

    zoom = capture['zoom']
    
    zoom = zoom + w -1
    
    bounds = el.getBounds(blockId, timestampNumber, token)
    
    if str(type(bounds)) == "<class 'shapely.geometry.polygon.Polygon'>":
        bounds = [bounds]
    else:
        bounds = [b for b in bounds]

    shape = gpd.GeoDataFrame({'geometry':bounds})
    
    i=0
    tiles_total = []
    for i in np.arange(shape.shape[0]):
        area = shape['geometry'].values[i]
        x1, y1, x2, y2  = area.bounds
        
        #find the x osm tiles involved   
        x1_osm =  math.floor((x1 +180 ) * 2**zoom / 360 )
        x2_osm =  math.floor( (x2 +180 ) * 2**zoom / 360)
        y2_osm = math.floor( 2**zoom / (2* math.pi) * ( math.pi - math.log( math.tan(math.pi / 4 + y1/360 * math.pi  ) ) ))
        y1_osm = math.floor( 2**zoom / (2* math.pi) * ( math.pi - math.log( math.tan(math.pi / 4 + y2/360 * math.pi  ) ) ))
        
        y1_osm = max(0,y1_osm)
        y2_osm = min(2**zoom-1,y2_osm)
        x1_osm = max(0,x1_osm)
        x2_osm = min(2**zoom-1,x2_osm)

        xs = np.arange(x1_osm, x2_osm + 1)
        ys = np.arange(y1_osm, y2_osm +1)

        ids = [ (x,y) for x in xs for y in ys ]

        xs = [x[0] for x in ids]
        ys = [y[1] for y in ids]


        y2s = [(2* math.atan( math.e**(math.pi - (y) * 2*math.pi / 2**zoom) ) - math.pi/2) * 360/ (2* math.pi)  for y in ys]
        y1s = [(2* math.atan( math.e**(math.pi - (y+1) * 2*math.pi / 2**zoom) ) - math.pi/2) * 360/ (2* math.pi) for y in ys]
        x1s = [x * 360/2**zoom - 180 for x in xs] 
        x2s = [(x +1) * 360/2**zoom - 180 for x in xs]

        tiles = [ geometry.Polygon([(x1s[i],y1s[i]), (x1s[i],y2s[i]), (x2s[i],y2s[i]), (x2s[i],y1s[i])]) for i in np.arange(len(y1s))]


        tiles = gpd.GeoDataFrame({'geometry':tiles, 'tileX': xs, 'tileY':ys, 'x1':x1s, 'x2':x2s,'y1':y1s, 'y2':y2s})
        tiles.crs = {'init': 'epsg:4326'}
        tiles_merc = tiles.to_crs({'init': 'epsg:3857'})
        bounds = tiles_merc.bounds
        tiles['x1_merc'] = bounds['minx'].values
        tiles['x2_merc'] = bounds['maxx'].values
        tiles['y1_merc'] = bounds['miny'].values
        tiles['y2_merc'] = bounds['maxy'].values


        tiles_total = tiles_total + [tiles]


    covering = pd.concat(tiles_total)
    covering = covering.drop_duplicates(['tileX','tileY'])

    covering['tileZoom'] = zoom

    covering['id'] = np.arange(covering.shape[0])
    return(covering)
    

def getTileData(blockId, captureId, tileX, tileY, tileZoom, token, visualizationId = None ):
    
    if type(token) != type('x'):
        raise ValueError('token must be of type string')

    if type(visualizationId) == type(None):
        visualizationId = 'data'


    token_inurl = '?token=' + token.replace('Bearer ', '')
    url_req = url + '/tileService/' + blockId + '/' + str(captureId) + '/' + visualizationId + '/' + str(tileZoom) + '/' + str(tileX) + '/' + str(tileY) + token_inurl
    r = s.get(url_req , timeout = 10 )
    if int(str(r).split('[')[1].split(']')[0]) == 403:
            return({'status':403, 'message':'Insufficient permission'})
    elif int(str(r).split('[')[1].split(']')[0]) != 200:
            return({'status':400, 'message':'Tile not found'})
    elif visualizationId == 'data':
        r = np.transpose(tifffile.imread(BytesIO(r.content)), [1,2,0] )      
    else:
       r = np.array(Image.open(BytesIO(r.content)), dtype = 'uint8')


    return({'status':200, 'message':r})
    
    
    
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

__version__ = '0.1.0'
url = 'https://api.ellipsis-drive.com/v3'

s = requests.Session()

cacheZoom = {}
cacheBands = {}

    

def getZoom(pathId, timestampId, token = None):
    
    pathId = el.sanitize.validUuid('pathId', pathId, True)
    timestampId = el.sanitize.validUuid('timestampId', timestampId, True)
    token = el.validString('token', token, False)    
    
    blockId = pathId
    captureId = timestampId
    
    key = blockId + '_' + captureId
    if key in cacheZoom.keys():
        return(cacheZoom[key])

    metadata = el.path.get(pathId = blockId, token = token)
    
    if metadata['type'] != 'raster':
        raise ValueError('pathId is of type vector but must be of type raster')
    
    captures = [c for c in metadata['raster']['timestamps'] if c['id'] == captureId]
    
    if len(captures) == 0:
        raise ValueError('given timestampId does not exist')

    zoom = captures[0]['zoom']
    
    
    cacheZoom[key] = zoom
    return(zoom)





def getBounds(pathId, timestampId, token = None):
    
    pathId = el.sanitize.validUuid('pathId', pathId, True)
    timestampId = el.sanitize.validUuid('timestampId', timestampId, True)
    token = el.sanitize.validString('token', token, False)    
    
    
    blockId = pathId
    captureId = timestampId
    metadata = el.path.get(blockId, token)
    if metadata['type'] == 'folder':
        raise ValueError('pathId is of type folder must be of type raster or vector')


    captures = [c for c in metadata['raster']['timestamps'] if c['id'] == captureId]
    
    if len(captures) == 0:
        raise ValueError('given captureId does not exist')

    timestamp = captures[0]['id']
    
    bounds = el.path.raster.timestamp.getBounds(pathId = blockId, timestampId = timestamp, token = token )
    
    return(bounds)

def applyModel(model, bounds, targetPathId, classificationZoom, token, tempFolder, modelNoDataValue = -1, targetDate = None):
    def f():
        return

    if type(targetDate) == type(None):
        targetStartDate = datetime.now()
        targetEndDate = targetStartDate



    if(type(model) != type(f)):
        raise ValueError('model must be a function')
        
    targetPathId = el.sanitize.validUuid('targetPathId', targetPathId, True)
    bounds = el.sanitize.validShapely('bounds', bounds, True)
    classificationZoom = el.sanitize.validInt('classificationZoom', classificationZoom, True)
    token = el.sanitize.validString('token', token, False)
    tempFolder = el.sanitize.validString('tempFolder', tempFolder, True)
    modelNoDataValue = el.sanitize.validFloat('modelNoDataValue', modelNoDataValue,  True)
    targetDate = el.sanitize.validDateRange('targetDate', targetDate, False)



    targetNoDataValue = modelNoDataValue
    
    if not 'float' in str(type(targetNoDataValue)) and not 'int' in str(type(targetNoDataValue)) :
        raise ValueError('targetNoDataValue must be of type float')
        
        
    print('creating a capture to write in')

    targetCaptureId = el.path.raster.timestamp.add(pathId = targetPathId, date= {'from':targetStartDate, 'to':targetEndDate}, token=token)['id']
    print('writing to capture ' + targetCaptureId)
    if  str(type(bounds)) != "<class 'shapely.geometry.polygon.Polygon'>" and str(type(bounds)) != "<class 'shapely.geometry.multipolygon.MultiPolygon'>":
        raise ValueError('Bounds must be a shapely polygon or multipolygon')
        
    if str(type(bounds)) == "<class 'shapely.geometry.polygon.Polygon'>":
        bounds = [bounds]
    else:
        bounds = [b for b in bounds]

    output = model({'tileX':0, 'tileY':0, 'zoom':classificationZoom})

    if str(type(output)) != "<class 'numpy.ndarray'>":
        raise ValueError('Output of model funciton must be a 3 dimensional numpy array, with the band number in the first dimension')
        
    if output.shape[1] != output.shape[2]:
        raise ValueError('Second and third dimension of the resutling numpy array of model should have equal length.')
    if len(output.shape) != 3:
        raise ValueError('Output of model function mus ba a 3 dimensional numpy array, with the band number in the first dimension')
    outputWidth = output.shape[1]
    bands_out = output.shape[0]    
    
    if outputWidth >2048 or bands_out > 40:
        raise ValueError("output of model may not exceed 40 by 2048 by 2048.")


    bound = bounds[0]        
    for bound in bounds:
        print('applying model to a connected component of the bounds')
        x1, y1, x2, y2  = bound.bounds
        x1_osm =  math.floor((x1 +180 ) * 2**classificationZoom / 360 )
        x2_osm =  math.floor( (x2 +180 ) * 2**classificationZoom / 360)
        y2_osm = math.floor( 2**classificationZoom / (2* math.pi) * ( math.pi - math.log( math.tan(math.pi / 4 + y1/360 * math.pi  ) ) ))
        y1_osm = math.floor( 2**classificationZoom / (2* math.pi) * ( math.pi - math.log( math.tan(math.pi / 4 + y2/360 * math.pi  ) ) ))        
        y1_osm = max(0,y1_osm)
        y2_osm = min(2**classificationZoom-1,y2_osm)
        x1_osm = max(0,x1_osm)
        x2_osm = min(2**classificationZoom-1,x2_osm)
        
        total = (x2_osm - x1_osm+1 + (10 - (x2_osm - x1_osm+1)%10 ) ) * (y2_osm-y1_osm +1 + (10 - (y2_osm-y1_osm +1) % 10) )
        frac = 0
        
        metadata = el.path.get(targetPathId, token)
        if metadata['type'] != 'raster':
            raise ValueError('pathId is of type folder must be of type raster or vector')
        
        x = x1_osm
        while x < x2_osm:
            y=y1_osm
            while y < y2_osm:
                r_out = np.zeros(( bands_out, 10*outputWidth, 10*outputWidth))

                N = 0
                for N in np.arange(10):
                    M=0
                    for M in np.arange(10):
                        frac = frac+1
                        el.util.loadingBar( frac, total)
                        tile = {'zoom': int(classificationZoom), 'tileX': float(x+N), 'tileY': float(y+M)}
                        r_out[:,M*outputWidth:(M+1)*outputWidth, N*outputWidth:(N+1)*outputWidth] = model( tile)



                xMin = x/2**classificationZoom *2* 2.003751e+07 - 2.003751e+07
                xMax = (x + 10)/2**classificationZoom *2* 2.003751e+07 - 2.003751e+07
                yMin = (2**classificationZoom - y-10)/2**classificationZoom * 2 * 2.003751e+07 - 2.003751e+07
                yMax = (2**classificationZoom - y )/2**classificationZoom * 2*2.003751e+07 - 2.003751e+07
                trans = rasterio.transform.from_bounds(xMin, yMin, xMax, yMax, r_out.shape[2], r_out.shape[1])
                crs = "EPSG:3857"
                file = tempFolder + '/' + str(frac) + ".tif"
                dtype = r_out.dtype
                
                with rasterio.open( file, 'w', compress="lzw", tiled=True, blockxsize=256, blockysize=256, count = bands_out, width=10*outputWidth, height=10*outputWidth, dtype = dtype, transform=trans, crs=crs) as dataset:
                    dataset.write(r_out)
                el.path.raster.timestamp.file.add(pathId = targetPathId, timestampId = targetCaptureId, filePath = file, token = token, fileFormat='tif', noDataValue =  targetNoDataValue)
                os.remove(file)
                
                y = y+10                
            x = x+10


        print('activating capture')
        el.path.raster.timestamp.activate(pathId = targetPathId, timestampId=targetCaptureId, token = token)
        print('capture activated result will be available soon')



def getTiles(bounds, classificationZoom):
    
    bounds = el.sanitize.validShapely('bounds', bounds, True)
    classificationZoom = el.sanitize.validInt('classificationZoom', classificationZoom, True)    

    
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
        x1_osm =  math.floor((x1 +180 ) * 2**classificationZoom / 360 )
        x2_osm =  math.floor( (x2 +180 ) * 2**classificationZoom / 360)
        y2_osm = math.floor( 2**classificationZoom / (2* math.pi) * ( math.pi - math.log( math.tan(math.pi / 4 + y1/360 * math.pi  ) ) ))
        y1_osm = math.floor( 2**classificationZoom / (2* math.pi) * ( math.pi - math.log( math.tan(math.pi / 4 + y2/360 * math.pi  ) ) ))
        
        y1_osm = max(0,y1_osm)
        y2_osm = min(2**classificationZoom-1,y2_osm)
        x1_osm = max(0,x1_osm)
        x2_osm = min(2**classificationZoom-1,x2_osm)

        xs = np.arange(x1_osm, x2_osm + 1)
        ys = np.arange(y1_osm, y2_osm +1)

        ids = [ (x,y) for x in xs for y in ys ]

        xs = [x[0] for x in ids]
        ys = [y[1] for y in ids]


        y2s = [(2* math.atan( math.e**(math.pi - (y) * 2*math.pi / 2**classificationZoom) ) - math.pi/2) * 360/ (2* math.pi)  for y in ys]
        y1s = [(2* math.atan( math.e**(math.pi - (y+1) * 2*math.pi / 2**classificationZoom) ) - math.pi/2) * 360/ (2* math.pi) for y in ys]
        x1s = [x * 360/2**classificationZoom - 180 for x in xs] 
        x2s = [(x +1) * 360/2**classificationZoom - 180 for x in xs]

        tiles = [ geometry.Polygon([(x1s[i],y1s[i]), (x1s[i],y2s[i]), (x2s[i],y2s[i]), (x2s[i],y1s[i])]) for i in np.arange(len(y1s))]


        tiles = gpd.GeoDataFrame({'geometry':tiles, 'tileX': xs, 'tileY':ys})
        tiles.crs = {'init': 'epsg:4326'}
        #tiles_merc = tiles.to_crs({'init': 'epsg:3857'})
        tiles_merc = tiles
        bounds = tiles_merc.bounds


        tiles_total = tiles_total + [tiles]


    covering = pd.concat(tiles_total)
    covering = covering.drop_duplicates(['tileX','tileY'])

    covering['tileZoom'] = classificationZoom

    return(covering)
    
    
    

def getTileData(pathId, timestampId, tile, token = None ):
    
    pathId = el.sanitize.validUuid('pathId', pathId, True)
    timestampId = el.sanitize.validUuid('timestampId', timestampId, True)
    tile = el.sanitize.validObject('tile', tile, True)
    token = el.sanitize.validString('token', token, False)
    if not 'tileX' in tile.keys() or not 'tileY' in tile.keys() or not 'zoom' in tile.keys():
        raise ValueError('tile parameter must contain keys, tileX, tileY and zoom, and must be float')
    if type(tile['tileX']) != type(2.5) and type(tile['tileX']) != type(2) :
        raise ValueError('tileX key in tile must be of type float')
    if type(tile['tileY']) != type(2.5) and type(tile['tileY']) != type(2) :
        raise ValueError('tileY key in tile must be of type float')
    if type(tile['zoom']) != type(2) :
        raise ValueError('zoom key in tile must be of type int')
    
    tileX = tile['tileX']
    tileY = tile['tileY']
    zoom = tile['zoom']
    
    if( type(token) != type(None) and 'Bearer' in token):
        token = token.replace('Bearer', '')
        token = token.replace(' ', '')
    url_req = url + '/path/' + pathId + '/raster/timestamp/' + timestampId + '/tile/' + str(zoom) + '/' + str(tileX) + '/' + str(tileY)
    
    if (token != None):
       url_req = url_req + '?token=' +  token
       
       
    r = s.get(url_req , timeout = 10 )
    if int(str(r).split('[')[1].split(']')[0]) == 403:
            raise ValueError('Insufficient permission for layer ' + pathId)
    elif r.status_code == 204:
            return {'status':204, 'result':'no data'}
    elif r.status_code != 200:
            raise ValueError(r.text)            
    
    r = tifffile.imread(BytesIO(r.content))


    return({'status':200, 'result':r})
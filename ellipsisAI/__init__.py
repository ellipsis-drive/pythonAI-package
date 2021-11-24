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

__version__ = '0.0.2'
url = 'https://api.ellipsis-drive.com/v1'

s = requests.Session()

cacheZoom = {}
cacheBands = {}


def getZoom(blockId, captureId, token):
    key = blockId + '_' + captureId
    if key in cacheZoom.keys():
        return(cacheZoom[key])

    metadata = el.metadata(blockId, False, token)
    
    if metadata['isShape']:
        raise ValueError('blockId is of type vector but must be of type raster')
    
    captures = [c for c in metadata['timestamps'] if c['id'] == captureId]
    
    if len(captures) == 0:
        raise ValueError('given captureId does not exist')

    zoom = captures[0]['zoom']
    
    
    cacheZoom[key] = zoom
    return(zoom)


def getNumBands(blockId, captureId, token):
    key = blockId + '_' + captureId
    if key in cacheBands.keys():
        return(cacheBands[key])

    metadata = el.metadata(blockId, False, token)
    
    if metadata['isShape']:
        raise ValueError('blockId is of type vector but must be of type raster')
    

    numBands = len(metadata['bands'])
        
    cacheBands[key] = numBands
    return(numBands)



def getBounds(blockId, captureId, token):
    metadata = el.metadata(blockId, False, token)
    captures = [c for c in metadata['timestamps'] if c['id'] == captureId]
    
    if len(captures) == 0:
        raise ValueError('given captureId does not exist')

    timestamp = captures[0]['timestamp']
    
    bounds = el.getBounds(projectId = blockId, timestamp = timestamp, token = token )
    
    return(bounds)

def applyModel(model, bounds, targetBlockId, classificationZoom, token, temp_folder, visualizationId = None, targetNoDataValue = 0, targetStartDate = None, targetEndDate = None):

    if type(targetStartDate) == type(None):
        targetStartDate = datetime.now()
    if type(targetEndDate) == type(None):
        targetEndDate = targetStartDate
    
    
    if not 'float' in str(type(targetNoDataValue)) and not 'int' in str(type(targetNoDataValue)) :
        raise ValueError('targetNoDataValue must be of type float')
        
        
    if type(visualizationId) == type(None):
        visualizationId = 'data'

    print('creating a capture to write in')

    targetCaptureId = el.addTimestamp(mapId = targetBlockId, startDate=targetStartDate, endDate = targetEndDate, token=token)['id']
    print('writing to capture ' + targetCaptureId)
    if  str(type(bounds)) != "<class 'shapely.geometry.polygon.Polygon'>" and str(type(bounds)) != "<class 'shapely.geometry.multiPolygon.MultiPolygon'>":
        raise ValueError('Bounds must be a shapely polygon or multipolygon')
        
    if str(type(bounds)) == "<class 'shapely.geometry.polygon.Polygon'>":
        bounds = [bounds]
    else:
        bounds = [b for b in bounds]

    output = model({'tileX':0, 'tileY':0, 'zoom':classificationZoom})

    if str(type(output)) != "<class 'numpy.ndarray'>":
        raise ValueError('Output of model funciton must be a 3 dimensional numpy array')
        
    if output.shape[0] != output.shape[1]:
        raise ValueError('First and second dimension of the resutling numpy array of model should have equal length.')
    if len(output.shape) != 3:
        raise ValueError('Output of model funciton mus ba a 3 dimensional numpy array')
    outputWidth = output.shape[0]
    bands_out = output.shape[2]    
    
    if outputWidth >2048 or bands_out > 40:
        raise ValueError("output width of model may not exceed 2048 by 2048 by 40.")


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
        
        x = x1_osm
        while x < x2_osm:
            y=y1_osm
            while y < y2_osm:
                r_out = np.zeros(( 10*outputWidth, 10*outputWidth, bands_out+1))

                N = 0
                for N in np.arange(10):
                    M=0
                    for M in np.arange(10):
                        frac = frac+1
                        el.loadingBar( frac, total)
                        tile = {'zoom':classificationZoom, 'tileX':x+N, 'tileY':y+M}
                        r_out[M*outputWidth:(M+1)*outputWidth, N*outputWidth:(N+1)*outputWidth, 0:bands_out] = model(tile)


                r_out[r_out[:,:,-2] !=targetNoDataValue,-1] = 1
                r_out = np.transpose(r_out, [2,0,1])
                r_out = r_out.astype('float32')
                xMin = x/2**classificationZoom *2* 2.003751e+07 - 2.003751e+07
                xMax = (x + 10)/2**classificationZoom *2* 2.003751e+07 - 2.003751e+07
                yMin = (2**classificationZoom - y-10)/2**classificationZoom * 2 * 2.003751e+07 - 2.003751e+07
                yMax = (2**classificationZoom - y )/2**classificationZoom * 2*2.003751e+07 - 2.003751e+07
                trans = rasterio.transform.from_bounds(xMin, yMin, xMax, yMax, r_out.shape[2], r_out.shape[1])
                crs = "EPSG:3857"
                file = temp_folder + '/' + str(frac) + ".tif"

                
                with rasterio.open( file, 'w', compress="lzw", tiled=True, blockxsize=256, blockysize=256, count = bands_out+1, width=10*outputWidth, height=10*outputWidth, dtype = 'float32', transform=trans, crs=crs) as dataset:
                    dataset.write(r_out)
                el.uploadRasterFile(mapId = targetBlockId, timestampId = targetCaptureId, file = file, token = token)
                os.remove(file)
                
                y = y+10                
            x = x+10

        metadata = el.metadata(targetBlockId, False, token)
        captures = [c for c in metadata['timestamps'] if c['finished']]
        if len(captures) ==0:
            r = s.post(url + '/settings/projects/includesTransparent', headers = {"Authorization":token},
                             json = {"mapId":  targetBlockId, 'includesTransparent':True})
            if int(str(r).split('[')[1].split(']')[0]) != 200:
                raise ValueError(r.text)

        print('activating capture')
        el.activateTimestamp(mapId = targetBlockId, timestampId=targetCaptureId, active = True, token = token)
        print('capture activated result will be available soon')



def getTiles(bounds, classificationZoom):
    
    if  str(type(bounds)) != "<class 'shapely.geometry.polygon.Polygon'>" and str(type(bounds)) != "<class 'shapely.geometry.multiPolygon.MultiPolygon'>":
        raise ValueError('Bounds must be a shapely polygon or multipolygon')

    
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
        tiles_merc = tiles.to_crs({'init': 'epsg:3857'})
        bounds = tiles_merc.bounds


        tiles_total = tiles_total + [tiles]


    covering = pd.concat(tiles_total)
    covering = covering.drop_duplicates(['tileX','tileY'])

    covering['tileZoom'] = classificationZoom

    return(covering)
    
    
    

def getTileData(blockId, captureId, tile, token, visualizationId = None, downsampleFactor = 1 ):

    
    tileX = tile['tileX']
    tileY = tile['tileY']
    tileZoom = tile['zoom']
    
    def getTile(token_inurl, blockId, captureId, visualizationId,x,y,zoom, num_bands ):
        url_req = url + '/tileService/' + blockId + '/' + str(captureId) + '/' + visualizationId + '/' + str(zoom) + '/' + str(x) + '/' + str(y) + token_inurl
        r = s.get(url_req , timeout = 10 )
        if int(str(r).split('[')[1].split(']')[0]) == 403:
                raise ValueError('Insufficient permission for block ' + blockId)
        elif int(str(r).split('[')[1].split(']')[0]) != 200:
                r = np.zeros((256,256,num_bands))
        elif visualizationId == 'data':
            r = np.transpose(tifffile.imread(BytesIO(r.content)), [1,2,0] )      
        else:
           r = np.array(Image.open(BytesIO(r.content)), dtype = 'uint8')
        return(r)
        

    if type(token) != type('x'):
        raise ValueError('token must be of type string')

    token_inurl = '?token=' + token.replace('Bearer ', '')

    if type(visualizationId) == type(None):
        visualizationId = 'data'
    
    
    
    zoom = getZoom(blockId, captureId, token)
    num_bands = getNumBands(blockId, captureId, token)

    if not downsampleFactor in np.arange(1,zoom+1):
        raise ValueError('downsampleFactor must be in ' + str(np.arange(1,zoom+1)))
    
    
    nativeZoom = zoom - downsampleFactor + 1

    if nativeZoom >= tileZoom:
        factor = 2**(nativeZoom - tileZoom)            
        r_total = np.zeros((256*factor , 256*factor, num_bands))
        for x in np.arange(factor):
            for y in np.arange(factor):
                r = getTile(token_inurl, blockId, captureId, visualizationId, tileX*factor + x, tileY*factor+y,nativeZoom, num_bands )
                r_total[ y*256: (y*256 + 256), x*256: (x*256 + 256) ,:] = r

    else:
        factor = 2**(tileZoom-nativeZoom)

        x = math.floor(tileX/factor)
        y = math.floor(tileY/factor)
        r = getTile(token_inurl, blockId, captureId, visualizationId, x, y,nativeZoom )                
      
        starty =   (tileY - y*factor) * 256/factor
        endy = (tileY - y*factor + 1) * 256/factor
        startx =   (tileX - x*factor) * 256/factor
        endx = (tileX - x*factor + 1) * 256/factor

        endy = math.floor(max(endy, starty+1))
        endx = math.floor(max(endx, startx+1))
        
        r_total = r[starty:endy,startx:endx,:]
        

    return(r_total)
    
    
    
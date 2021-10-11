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

__version__ = '0.0.1'

s = requests.Session()


def applyModel(model, blockId, captureId, targetBlockId, visualizationId, inputWidth, token, temp_folder):

    inputWidth = int(inputWidth)    
    if inputWidth % 256 != 0 or inputWidth <=0:
        raise ValueError("inputWidth needs to be a multiple of 256 and must be larger than zero.")

    if type(token) != type('x'):
        raise ValueError('token must be of type string')

    token_inurl = '?token=' + token.replace('Bearer ', '')


    w = int(inputWidth / 256)

    metadata = el.metadata(blockId, False, token)
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
    num_bands = len(metadata['bands'])
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
                                
                                url_req = 'https://api.ellipsis-drive.com/v1/tileService/' + blockId + '/' + str(timestampNumber) + '/data/' + str(zoom) + '/' + str(x+N*w+ i) + '/' + str(y+M*w+j) + token_inurl
                                r = s.get(url_req , timeout = 10 )
                                if int(str(r).split('[')[1].split(']')[0]) == 403:
                                        raise ValueError('insufficient access')
                                elif int(str(r).split('[')[1].split(']')[0]) != 200:
                                    r = np.zeros((256,256,num_bands))
                                else:
                                    r = np.transpose(tifffile.imread(BytesIO(r.content)), [1,2,0] )      
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
                os.remove(file)
                y = y+10*w
                
            x = x+10*w
        print('activating timestamp')
        el.activateTimestamp(mapId = targetBlockId, timestampId=targetCaptureId, active = True, token = token)
        print('capture activated result will be available soon')

        


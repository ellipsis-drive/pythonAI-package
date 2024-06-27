import ellipsisAI as ai
import ellipsis as el
import numpy as np

import sys


pathId = 'b95ea2fb-8415-4c54-a6cc-f3d11258b7f8'
timestampId = "dc32dc29-1664-449a-a09e-ae5042c60f62"
targetPathId = "4262bc2e-66df-438d-8550-b224462c3722"
token = "epat_0UdLYCO6WCKS7H52ra30WxJBqMYjmJgsWTndJV8PrplLYjnn7qfgYMo4hcTDrGJb"


pathId = sys.argv[1]
timestampId =  int(sys.argv[2])
targetPathId = int(sys.argv[3])
token = int(sys.argv[4])



#retrieve the zoom and bounds of the capture you wish to classify
classificationZoom = ai.getReccomendedClassificationZoom(pathId = pathId, timestampId = timestampId, token = token)
bounds = el.path.raster.timestamp.getBounds(pathId, timestampId, token)


#we create a dummy model. We use the identity function mapping an image to itself. We use the getTleData function to retirve the image for the given input tile ofthe model.
def model(tile):
    result = ai.getTileData(pathId = pathId, timestampId = timestampId, tile = tile, token  = token)
    if result['status'] == 204:
        output =  np.zeros((1,256,256))
        output[:,:,:] = -1
    else:
        r = result['result']

        output = (r[7,:,:] -r[3,:,:]) / (r[7,:,:] + r[3,:,:])
    return(output)


#apply the model on the given bounds on the given zoomlevel
ai.applyModel(model = model, bounds = bounds, targetPathId = targetPathId, classificationZoom = classificationZoom, token=token)


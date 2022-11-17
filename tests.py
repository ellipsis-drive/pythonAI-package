import numpy as np
import ellipsisAI as ai
import ellipsis as el

pathId = '27e49a17-fae9-48d4-a861-b6da59ae5994'
timestampId = "109af860-da06-4c4e-ae01-b5703cdb3da0"

targetPathId = "27d150d4-bc0f-4dcf-9b00-80452c02f14b"
temp_folder = '/home/daniel/Downloads'

token = el.account.logIn('daan','')

classificationZoom = ai.getZoom(pathId, timestampId, token)

bounds = ai.getBounds(pathId, timestampId, token)


#we create a dummy model. We use the identity funciton mapping an image to itself
def model(bounds):
    #for raster use getTileData
    #for vector use el.path.vector.timestamp.getFeaturesByExtent(pathId, timestampId, extent)
    #insert some super integelgent logic here
    return(image)
    

#model is a function mapping a tile to a 3D numpy array, width by height by bands
#bounds is a shapely polygon or multipolygon of the region to classify
#temfolder is some temporary folder the script can use (sorry bit ugly I should be using memory files)
# classificationZoom is the zoomlevel on which to classify the layer
#targetPathId where to create the classification layer


ai.applyModel(model, bounds, targetPathId, classificationZoom, token, temp_folder)



r = getTileData(pathId=blockId, timestampId=captureId, tile={'tileX':0, 'tileY':0, 'zoom':0}, token=token )

el.path.vector.timestamp.getFeaturesByExtent(pathId, timestampId, extent)



print(np.unique(r))

tiles = ai.getTiles(bounds, classificationZoom)




#########
features = el.path.vector.timestamp.listFeatures(pathId, timestampId)

el.path.vector.featureProperty.add(pathId, 'classification', 'string' )

classifications = []
for feature in featuers:
    extent = feature.bounds + some buffer
    
    r = el.path.raster.timestamp.getRaster(pathId, timestampId, extent)
    #repeat for other layers you would want to use
    classification = model()
    #apply some logic to create classification
    classifcations = classifications + [classification]    

features['classifications'] = classifications
el.path.vector.timestamp.feature.edit(pathId, timestampId, featureIds = features['id'].values, token, features)
    







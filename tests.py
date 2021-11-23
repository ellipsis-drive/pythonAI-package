import ellipsisAI as ai
import ellipsis as el

blockId = '170aadad-8eaa-4509-9c0e-c1536d58a1fe'
captureId = "633b4b9f-d939-4c4a-8d90-0e9fceb64b83"
targetBlockId = "066458f4-f018-4f49-a1f0-dedfa71b3368"
temp_folder = 'YOUR_PATH'

token = el.logIn('YOUR_USERNAME','YOUR_PASSWORD')

classificationZoom = ai.getZoom(blockId, captureId, token)

bounds = ai.getBounds(blockId, captureId, token)


#we create a dummy model. We use the identity funciton mapping an image to itself
def model(tile):
    image = ai.getTileData(blockId, captureId, tile, token)
    return(image)
    


ai.applyModel(model, bounds, targetBlockId, classificationZoom, token, temp_folder)







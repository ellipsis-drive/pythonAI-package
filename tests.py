import ellipsisAI as ai
import ellipsis as el

blockId = '170aadad-8eaa-4509-9c0e-c1536d58a1fe'
captureId = "633b4b9f-d939-4c4a-8d90-0e9fceb64b83"
targetBlockId = "066458f4-f018-4f49-a1f0-dedfa71b3368"


inputWidth = 1024
temp_folder = '/home/daniel/Downloads'
token = ellipsis.logIn('','')

def model(r):
    return(r)

ai.applyModel(model, blockId, captureId, targetBlockId, inputWidth, token, temp_folder, visualizationId = None)

tiles = ai.getTiles(blockId, captureId, inputWidth, token)


tileX = 0
tileY = 0
tileZoom = 0
nativeZoom = 5

t = ai.getTileData(blockId, captureId, tileX, tileY, tileZoom,  inputWidth, nativeZoom, token)








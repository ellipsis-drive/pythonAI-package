import ellipsisAI
import ellipsis

blockId = '170aadad-8eaa-4509-9c0e-c1536d58a1fe'
captureId = "633b4b9f-d939-4c4a-8d90-0e9fceb64b83"
targetBlockId = "066458f4-f018-4f49-a1f0-dedfa71b3368"
inputWidth = 256
temp_folder = '/home/daniel/Downloads'
token = ellipsis.logIn('','')

def model(r):
    return(r)

ellipsisAI.applyModel(model, blockId, captureId, targetBlockId, inputWidth, token, temp_folder, visualizationId = None)


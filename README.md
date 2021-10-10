This package is meant to help you run models on Ellipsis Drive content.


applyModel(model, blockId, captureId, targetBlockId, targetCaptureId, visualizationId, inputWidth, token)

model must be a function mapping a (inputWidth,inputWidth,b) numpy array to an (inputWidth,inputWidth) numpy array.

model: a function mapping a inputWidth by inputWidth by bands numpy array to a 3 dimensional numpy array. The resulting numpy array should always have the same shape.
blockId: the id of the block to classify
captureId: the id of the capture to classify
targetBlockId: the id of the block to write the classifications to
targetCaptureId: the id of the capture to write the classifications to
inputWidth: the size of the input array. Must be a number divisible by 256
visualizationId: id of the visualization to use as input. If not specified the original raster is used.
token: your token



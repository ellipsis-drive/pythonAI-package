This package is meant to help you run models on Ellipsis Drive content. It should be used in combination with the ellipsis package.


applyModel(model, blockId, captureId, targetBlockId, targetCaptureId, visualizationId, inputWidth, token)

model: a function mapping an inputWidth by inputWidth by bandNumber numpy array to a 3 dimensional numpy array. The resulting numpy array should always have the same shape, but can difer from the input shape. The bandNumber must be the number of bands of the input block.
blockId: the id of the block to classify
captureId: the id of the capture to classify
targetBlockId: the id of the block to write the classifications to
inputWidth: the size of the input array. Must be a number divisible by 256
visualizationId: id of the visualization to use as input. If not specified the original raster is used.
token: your token

This function applies the model function to the raster in the specified capture of the specified block. The results will be written in a new capture of the specified target block.

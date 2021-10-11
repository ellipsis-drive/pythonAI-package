This package is meant to help you run models on Ellipsis Drive content. It should be used in combination with the ellipsis package.

```python
applyModel(model, blockId, captureId, targetBlockId, targetCaptureId, visualizationId, inputWidth, token)
```

This function applies the given model to the raster in the specified capture of the specified block. The results will be written in a new capture of the specified target block.

| Name        | Description |
| ----------- | -----------|
| model        | A function mapping mapping a 3 dimensional numpy array to some other 3 dimensional numpy array |
| blockId     | The id of the block to classify |
| captureId     | The id of the capture to classify |
| targetBlockId        | The id of the block to write the result to |
| inputWidth        | input width and height of numpy array|
| visualizationId        | visualization to use as input, if not given original raster is used|
| token        | Your token|







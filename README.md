This package is meant to help you run models on Ellipsis Drive content. It should be used in combination with the ellipsis package.


### Install
```python
pip install ellipsis-AI
```

### Functions

#### applyModel

```python
applyModel(model, blockId, captureId, targetBlockId, targetCaptureId, inputWidth, token, visualizationId= None)
```

This function applies the given model to the raster in the specified capture of the specified block. The results will be written in a new capture of the specified target block.

| Name        | Description |
| ----------- | -----------|
| model        | A function mapping mapping a 3 dimensional numpy array to some other 3 dimensional numpy array |
| blockId     | The id of the block to classify |
| captureId     | The id of the capture to classify |
| targetBlockId        | The id of the block to write the result to |
| inputWidth        | input width and height of the numpy array|
| token        | Your token|
| visualizationId        | visualization to use as input, if not given original raster is used|



#### getTiles

```python
getTiles(blockId, captureId, inputWidth, token)
```

This function gets all ids of tiles of size inputWidth covering the specified capture. 

| Name        | Description |
| ----------- | -----------|
| blockId     | The id of the block of the capture to cover |
| captureId     | The id of the capture to cover |
| inputWidth        | input width and height of the numpy array|
| token        | Your token|

#### getTileData

```python
getTileData(blockId, captureId, tileX, tileY, tileZoom, token, visualizationId= None )
```

This function gets all ids of tiles of size inputWidth covering the specified capture. 

| Name        | Description |
| ----------- | -----------|
| blockId     | The id of the block of the capture to cover |
| captureId     | The id of the capture to cover |
| tileX        | tileX as found in the tileId|
| tileY        | tileY as found in the tileId|
| tileZoom        | tileZoom as found in the tileId|
| token        | Your token|
| visualizationId        | visualization to retrieve, if not specified original data of raster is returned|




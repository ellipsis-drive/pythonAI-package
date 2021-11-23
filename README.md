This package is meant to help you run models on Ellipsis Drive content. It should be used in combination with the ellipsis package.


### Install
```python
pip install ellipsisAI
```

### Example
```python
import ellipsisAI as ai
import ellipsis as el

blockId = '170aadad-8eaa-4509-9c0e-c1536d58a1fe'
captureId = "633b4b9f-d939-4c4a-8d90-0e9fceb64b83"
targetBlockId = "066458f4-f018-4f49-a1f0-dedfa71b3368"
temp_folder = 'YOUR_PATH'

#login to get a authentication token
token = el.logIn('YOUR_USERNAME','YOUR_PASSWORD')

#retrieve the zoom and bounds of the capture you wish to classify
classificationZoom = ai.getZoom(blockId, captureId, token)
bounds = ai.getBounds(blockId, captureId, token)


#we create a dummy model. We use the identity function mapping an image to itself. We use the getTleData function to retirve the image for the given input tile ofthe model.
def model(tile):
    image = ai.getTileData(blockId, captureId, tile, token)
    return(image)

#apply the model on the given bounds on the given zoomlevel
ai.applyModel(model, bounds, targetBlockId, classificationZoom, token, temp_folder)
```


### Functions

#### getZoom

```python
getZoom(blockId, captureId, token)
```

This function retrieves the max zoomlevel of the specified capture. The result can be used as classificationgZoom argument in the applyModel or getTiles function.

| Name        | Description |
| ----------- | -----------|
| blockId     | The id of the block the capture is in |
| captureId     | The id of the capture |
| token        | Your token|


#### getBounds

```python
getBounds(blockId, captureId, token)
```

This function retrieves the bounds of the specified capture. The result can be used as bounds argument in the applyModel function.

| Name        | Description |
| ----------- | -----------|
| blockId     | The id of the block the capture is in |
| captureId     | The id of the capture |
| token        | Your token|


#### applyModel

```python
applyModel(model, bounds, targetBlockId, classificationZoom, token, temp_folder, visualizationId = None, targetNoDataValue = 0, targetStartDate = None, targetEndDate = None)
```

This function applies the given model on all tiles of zoomlevel classificationZoom withing the specified bounds. The results will be written in a new capture of the specified target block.

| Name        | Description |
| ----------- | -----------|
| model        | A function mapping mapping a tile object to a 3 dimensional numpy array. The dimensions of the numpy array should be independent of the tile id. A tile object is a dictionary with keys 'tileX', 'tileY' and 'zoom' as integers. |
| bounds        | A shapely polygon or multipolygon indicating the region you wish to classify |
| targetBlockId        | The id of the block to write the result to |
| classificationZoom        | The zoomlevel of the tiles you wish to use for the model input as integer. |
| token        | Your token|
| temp_folder        | A path where temporary files can be written|
| visualizationId        | visualization to use as input, if not given original raster is used|
| targetNoDataValue        | Which number of the model output to interpret as transparent|
| targetStartDate        | datetime object with date to use for the capture to which the results will be written. Defaults to current date|
| targetEndDate        | datetime object with date to use for the capture to which the results will be written. Defaults to targetStartDate|



#### getTileData

```python
getTileData(blockId, captureId, tile, token, visualizationId = None, downsampleFactor = 1 )
```

This function retrieves data for the given tile as numpy array. This function can be used within your model function te retireve relevant data for the given tile.

| Name        | Description |
| ----------- | -----------|
| blockId     | the id of the block to get data from |
| captureId     | the id of the capture to get data from |
| tile     | A dictionary with keys tileX, tileY and zoom as int |
| token        | Your token|
| visualizationId        | The id of the visualization you wish to retrieve. If not given raw data is used|
| downsampleFactor        | A factor with which to downsample the data. Default 1 (no downsampling)|


#### getTiles

```python
getTiles(bounds, classificationZoom)
```

This function covers a given bounds with tiles of the given zoomlevel. You can use the result to get tile arguments for the getTileData function

| Name        | Description |
| ----------- | -----------|
| bounds     | A shapely polygon or multipolygon |
| classificationZoom        | The zoomlevel of the tiles to cover with as int |



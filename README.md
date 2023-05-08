This package is meant to help you run models on Ellipsis Drive content. It should be used in combination with the ellipsis package.


### Install
```python
pip install ellipsisAI
```

### Example
```python
import ellipsisAI as ai
import ellipsis as el

pathId = '170aadad-8eaa-4509-9c0e-c1536d58a1fe'
timestampId = "633b4b9f-d939-4c4a-8d90-0e9fceb64b83"
targetPathId = "066458f4-f018-4f49-a1f0-dedfa71b3368"
tempFolder = 'YOUR_PATH'

#login to get a authentication token
token = el.account.logIn('YOUR_USERNAME','YOUR_PASSWORD')

#retrieve the zoom and bounds of the capture you wish to classify
classificationZoom = ai.getReccomendedClassificationZoom(pathId = pathId, timestampId = timestampId, token = token)
bounds = el.path.raster.timestamp.getBounds(pathId, timestampId, token)


#we create a dummy model. We use the identity function mapping an image to itself. We use the getTleData function to retirve the image for the given input tile ofthe model.
def model(tile):
    result = ai.getTileData(pathId = pathId, timestampId = timestampId, tile = tile, token  = token)
    if result['status'] == 204:
        output =  np.zeros((1,256,256))
    else:
        r = result['result']

        output = r[0:1,:,:] * 2
    return(output)


#apply the model on the given bounds on the given zoomlevel
ai.applyModel(model, bounds, targetPathId, classificationZoom, token, tempFolder)
```


### Functions

#### applyModel

```python
applyModel(model, bounds, targetPathId, classificationZoom, token, tempFolder, modelNoDataValue = -1, targetFromDate = None, targetToDate = None)
```

This function applies the given model on all tiles of zoomlevel classificationZoom withing the specified bounds. The results will be written in a new capture of the specified target block.

| Name        | Description |
| ----------- | -----------|
| model        | A function mapping given bounds to a 3D numpy array. |
| bounds        | A shapely polygon or multipolygon indicating the region you wish to classify |
| targetPathId        | The id of the path to write the result to |
| classificationZoom        | The zoomlevel of the tiles you wish to use for the model input as integer. |
| token        | Your token|
| tempFolder        | A path where temporary files can be written|
| modelNoDataValue        | Which number of the model output to interpret as transparent|
| targetDate        | Dictionary with keys from and to, both must be of type datetime. Defaults to current date|



#### getTiles

```python
getTiles(bounds, classificationZoom)
```

This function covers a given bounds with tiles of the given zoomlevel. You can use the result to get tile arguments for the getTileData function

| Name        | Description |
| ----------- | -----------|
| bounds     | A shapely polygon or multipolygon |
| classificationZoom        | The zoomlevel of the tiles to cover with as int |



#### getTileData

```python
getTileData(pathId, timestampId, tile, token = None )
```

This function retrieves raster data for a certain tile.

| Name        | Description |
| ----------- | -----------|
| PathId     | Id of the layer to retrieve the raster for |
| timestampId        | Id of the timestamp to retrieve the raster for |
| tile        | A dictionary with tileX, tileY and zoom as integers |
| token        | Your token (optional) |

#### getReccomendedClassificationZoom

```python
getReccomendedClassificationZoom(pathId, timestampId, token = None)
```

This function retrieves raster data for a certain tile.

| Name        | Description |
| ----------- | -----------|
| PathId     | Id of the layer to retrieve the raster for |
| timestampId        | Id of the timestamp to retrieve the raster for |
| token        | Your token (optional) |




import os
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection


def _save_geopackage(gdf, folder_path, filename, driver=None):
    ## Saving the file
    os.makedirs(folder_path, exist_ok=True)  # make sure folder exists
    filepath = os.path.join(folder_path, filename)  # we use .gpkg instead of .shp in order to keep column names
    # if driver is "GPKG":
    #     layername = filename.split('.')[0]
    #     filepath = os.path.join(filepath, layername)

    gdf.to_file(filepath, driver=driver)
    print(f'\n---- Saved {filepath}')

def _geomcollection_to_multipolygon(geom):
    if isinstance(geom, Polygon):
        return MultiPolygon([geom])          # convert single Polygon to MultiPolygon
    elif isinstance(geom, MultiPolygon):
        return geom                          # already fine
    elif isinstance(geom, GeometryCollection):
        # extract only Polygon/MultiPolygon parts
        polygons = [g for g in geom.geoms if isinstance(g, (Polygon, MultiPolygon))]
        if polygons:
            return MultiPolygon([p for poly in polygons for p in
                                 (poly.geoms if isinstance(poly, MultiPolygon) else [poly])])
        else:
            return None                       # no polygons inside
    else:
        return None                            # other geometry types


def _polygon_to_multipolygon(gdf):
# turn everything into MultiPolygon.
    gdf["geometry"] = gdf["geometry"].apply(lambda geom:
                                            MultiPolygon([geom]) if isinstance(geom, Polygon) else geom)


import json
import os.path

import geopandas as gpd

from .utils import _save_geopackage


# Define the regex pattern for categories of interest
filter_pattern = r'store|hospital|church|restaurant|salon|food|retailer|shop|post_office|gas_station|park|bar|barber|school|market'

def preprocess_POI_data(POI_path):
    ### WE NEED TO MAKE A SHAPEFILE FOR THE POI DATA From given geojson WA WE CAN USE IN ARC GIS PRO
    #### How did Panick get this data? did the website give poi for the specific study area?
    print('\n---- reading POI geojson data')
    # method1
    POI_gdf = gpd.read_file(POI_path)
    # this reads the geojson file and skips columns that have bad types (lists)
    # now we convert it into shapefile so that arcGisPro can read it (todo or make geopackage)
    _save_geopackage(POI_gdf, os.path.join(save_path, "poi_data"), 'POI_data.shp')
    print('saved POI_data.shp')

    # method 2  --- open geojson using Json to Features tool -- recommended
    # import arcpy
    # ans = arcpy.conversion.JSONToFeatures(
    #     in_json_file=r"C:\Users\Soheil99\OneDrive - UW\0 Research\UW Tacoma\my copy - Satellite Communities Project\Data\POI Data\WA_Study_Area.geojson",
    #     out_features=r"C:\Users\Soheil99\OneDrive - UW\0 Research\UW Tacoma\my copy - Satellite Communities Project\Analysis\RuralATGapFinder\ArcGIS_test\ArcGIS_test.gdb\WA_Study_Area_JSONToFeatures",
    #     geometry_type="POINT"
    # )


def parse_categories(cat_str):
    # Parse the JSON 'categories' Column ---
    # Create a function to safely parse the JSON string in each row
    try:
        return json.loads(cat_str)
    except (json.JSONDecodeError, TypeError):
        # Return a default structure if JSON is malformed or not a string
        return {'primary': None, 'alternate': []}


def filter_SR_POI(POI_SR_path, save_path=None):
    print('\n---- Processing SR-buffered POI data')
    ### AFTER GETTING THE SHAPEFILE OF POI WITHIN 300 FT OF _ **SR**_ FROM ARCGIS PRO,
    # WE NEED TO FILTER THEM OUT HERE TO KEEP ONLY THOSE THAT COULD BE CONSIDERED AS PRIMARY POI
    POI_Within_SR_Buffer_0 = gpd.read_file(POI_SR_path)
    POI_Within_SR_Buffer_1 = POI_Within_SR_Buffer_0.copy()
    POI_Within_SR_Buffer_1['categories_json'] = POI_Within_SR_Buffer_1['categories'].apply(parse_categories)
    POI_Within_SR_Buffer_1['primary_category'] = POI_Within_SR_Buffer_1['categories_json'].apply(
        lambda x: x.get('primary'))
    POI_Within_SR_Buffer_1['alternate_categories'] = POI_Within_SR_Buffer_1['categories_json'].apply(
        lambda x: x.get('alternate', []))

    # If you want to explore the data using Excel, check the following.
    if save_path:
        poi_export = POI_Within_SR_Buffer_1.drop(columns='geometry')
        # Convert the list of alternate categories to a comma-separated string
        poi_export['alternate_categories'] = poi_export['alternate_categories'].apply(
            lambda x: ', '.join(map(str, x)) if isinstance(x, list) else x)
        excel_path = os.path.join(save_path, "POI_Within_SR_Buffer_1.xlsx")
        poi_export.to_excel(excel_path, index=False)
        print(f"Saved intermediate data for exploration to Excel at:\n{excel_path}")

    unique_categories = POI_Within_SR_Buffer_1['primary_category'].unique()
    print(f"\nFound {len(unique_categories)} unique primary categories. 10 examples:{unique_categories[:10]}")
    # Overture is organized around approximately 22 top-level categories. We need to use the primary categories
    # to filter the data. There are 349 unique primary categories in our shapefile for 1616 POI

    print('Filter POIs Based on Primary Category')
    # Use .str.contains() to filter the GeoDataFrame
    POI_Within_SR_Buffer_2 = POI_Within_SR_Buffer_1[
        POI_Within_SR_Buffer_1['primary_category'].str.contains(
            filter_pattern,
            case=False,  # ignore_case = TRUE
            na=False,  # Don't match on NaN values
            regex=True
        )
    ].copy()
    print(f"Filtered down to {len(POI_Within_SR_Buffer_2)} relevant POIs.")

    # Cleanup for Shapefile Export ---- Probably not needed at all
    # Shapefiles do not support list or dictionary columns, so we flatten them.
    POI_Within_SR_Buffer_3 = POI_Within_SR_Buffer_2.copy()
    # Flatten the 'categories_json' dictionary into a string
    POI_Within_SR_Buffer_3['categories_json'] = POI_Within_SR_Buffer_3['categories_json'].apply(
        lambda x: json.dumps(x)  # Re-serialize the dictionary to a clean JSON string
    )
    # Flatten the 'alternate_categories' list into a string
    POI_Within_SR_Buffer_3['alternate_categories'] = POI_Within_SR_Buffer_3['alternate_categories'].apply(
        lambda x: ', '.join(map(str, x)) if isinstance(x, list) else ''
    )

    print(f"Final data head before writing to shapefile has {len(POI_Within_SR_Buffer_3)} features.")
    _save_geopackage(POI_Within_SR_Buffer_3, save_path,'POI_Within_SR_Buffer_Filtered.gpkg', driver="GPKG")
    print(f"-----> Successfully wrote filtered poi data to: POI_Within_SR_Buffer_Filtered.gpkg")
    return POI_Within_SR_Buffer_3


def filter_CR_POI():
    pass


def filter_POIs(POI_SR_path, POI_CR_path, save_path):
    sr_POIs = filter_SR_POI(POI_SR_path, save_path)
    print('debuggg')
    pass


if __name__ == '__main__':
    POI_SR_path = r"C:/Users/Soheil99/OneDrive - UW/0 Research/UW Tacoma/my copy - Satellite Communities Project/Data/POI Within 300 ft SR/POI_CBG_Right_Outside_PC_SR_Buffer.shp"
    POI_CR_path = r"C:/Users/Soheil99/OneDrive - UW/0 Research/UW Tacoma/my copy - Satellite Communities Project/Data/POI Within 300 ft CR/POI_CBG_Right_Outside_PC_CR_Buffer.shp"
    save_path = r"C:\Users\Soheil99\OneDrive - UW\0 Research\UW Tacoma\my copy - Satellite Communities Project\Analysis\RuralATGapFinder\out"
    filter_POIs(POI_SR_path, POI_CR_path, save_path=save_path)
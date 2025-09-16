import json
import geopandas as gpd

def parse_categories(cat_str):
    # Parse the JSON 'categories' Column ---
    # Create a function to safely parse the JSON string in each row
    try:
        return json.loads(cat_str)
    except (json.JSONDecodeError, TypeError):
        # Return a default structure if JSON is malformed or not a string
        return {'primary': None, 'alternate': []}

def filter_SR_POI():
    ### AFTER GETTING THE SHAPEFILE OF POI WITHIN 300 FT OF _ **SR**_ FROM ARCGIS PRO,
    # WE NEED TO FILTER THEM OUT HERE TO KEEP ONLY THOSE THAT COULD BE CONSIDERED AS PRIMARY POI
    POI_Within_SR_Buffer_0 = gpd.read_file(POI_SR_path)
    pass


def filter_CR_POI():
    pass


def filter_POIs():
    pass


if __name__ == '__main__':

    POI_path = r"C:/Users/Soheil99/OneDrive - UW/0 Research/UW Tacoma/my copy - Satellite Communities Project/Data/POI Data/WA_Study_Area.geojson"
    POI_SR_path = r"C:/Users/Soheil99/OneDrive - UW/0 Research/UW Tacoma/my copy - Satellite Communities Project/Data/POI Within 300 ft SR/POI_CBG_Right_Outside_PC_SR_Buffer.shp"
    POI_CR_path = r"C:/Users/Soheil99/OneDrive - UW/0 Research/UW Tacoma/my copy - Satellite Communities Project/Data/POI Within 300 ft CR/POI_CBG_Right_Outside_PC_CR_Buffer.shp"
    save_path = r"C:\Users\Soheil99\OneDrive - UW\0 Research\UW Tacoma\my copy - Satellite Communities Project\Analysis\RuralATGapFinder\out"

    filter_POIs(state_in, counties_in, sld_gdb_path, pop_ctr_path, nces_WA_path, save_path=save_path)
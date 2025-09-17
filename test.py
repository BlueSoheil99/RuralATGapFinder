from RuralATGapFinder import RuralActiveTransportAnalysis

if __name__ == '__main__':
    # state_name = parameters[0]
    # county_field = parameters[1]
    # county_names = parameters[2]
    # population_fc = parameters[3]
    # sld_cbg_path = parameters[4]
    # state_roads_fc = parameters[5]
    # county_roads_fc = parameters[6]
    # parcel_fc = parameters[7]
    # parcel_field = parameters[8]
    # poi_fc = parameters[9]
    # road_buffer_dist = float(parameters[10].value or 300)
    # nces_path = parameters[11]
    # output_gdb = parameters[12]
    # save_path = parameters[13]

    state_in = 'WA'
    counties_in = ["King", "Pierce", "Snohomish", "Kitsap", "Skagit",
                   "Island", "Thurston", "Lewis", "Mason", "Whatcom",
                   "San Juan", "Clallam", "Jefferson", "Grays Harbor",
                   "Pacific", "Wahkiakum", "Cowlitz", "Clark", "Skamania"]
    # -------------
    sld_gdb_path = r"C:/Users/Soheil99/OneDrive - UW/0 Research/UW Tacoma/my copy - Satellite Communities Project/Data/SmartLocationDatabase.gdb"
    pop_ctr_path = r"C:/Users/Soheil99/OneDrive - UW/0 Research/UW Tacoma/my copy - Satellite Communities Project/Data/WSDOT_-_Population_Centers/WSDOT_-_Population_Centers.shp"
    POI_path = r"C:/Users/Soheil99/OneDrive - UW/0 Research/UW Tacoma/my copy - Satellite Communities Project/Data/POI Data/WA_Study_Area.geojson"
    state_roads_fc= r"C:\Users\Soheil99\OneDrive - UW\0 Research\UW Tacoma\my copy - Satellite Communities Project\Data\WSDOT_-_Legacy_State_Highways\WSDOT_-_Legacy_State_Highways.shp"
    county_roads_fc = r"C:\Users\Soheil99\OneDrive - UW\0 Research\UW Tacoma\my copy - Satellite Communities Project\Data\WSDOT_-_County_Road_(CRAB)\WSDOT_-_County_Road_(CRAB).shp"
    bike_roads_along_SR = r"C:\Users\Soheil99\OneDrive - UW\0 Research\UW Tacoma\my copy - Satellite Communities Project\Data\WSDOT_-_Bike_Paths_Along_State_Routes\WSDOT_-_Bike_Paths_Along_State_Routes.shp"
    parcel_fc = r"C:\Users\Soheil99\OneDrive - UW\0 Research\UW Tacoma\my copy - Satellite Communities Project\Data\Current_Parcels\Parcels_2024.shp"
    road_buffer_dist = 300
    nces_WA_path = r"C:/Users/Soheil99/OneDrive - UW/0 Research/UW Tacoma/my copy - Satellite Communities Project/Data/edge_locale24_nces_WA"
    output_gdb = r"C:\Users\Soheil99\OneDrive - UW\0 Research\UW Tacoma\my copy - Satellite Communities Project\Analysis\RuralATGapFinder\out\out.gdb"
    save_path = r"C:\Users\Soheil99\OneDrive - UW\0 Research\UW Tacoma\my copy - Satellite Communities Project\Analysis\RuralATGapFinder\out"

    test = RuralActiveTransportAnalysis()
    parameters = [state_in, 'COUNTY', counties_in, pop_ctr_path, sld_gdb_path,
                  state_roads_fc, county_roads_fc, parcel_fc, 'LANDUSE_CD', POI_path,
                  road_buffer_dist, nces_WA_path, output_gdb, save_path]
    test.execute(parameters, None)


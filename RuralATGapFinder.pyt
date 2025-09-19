import os
import arcpy
import geopandas as gpd
import yaml


from src.preprocess import preprocess
from src.process_poi import filter_POIs


class Toolbox(object):
    def __init__(self):
        self.label = "Rural Active Transportation Analysis"
        self.alias = "rural_transport_tool"
        self.tools = [RuralActiveTransportAnalysis]


class RuralActiveTransportAnalysis(object):
    def __init__(self):
        self.label = "Rural Active Transportation Infrastructure Gap Analysis"
        self.description = ("Analyzes active transportation infrastructure gaps in rural areas "
                            "by identifying residential clusters outside population centers and "
                            "their relationship to state/county roads and accessible POIs.")
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameters following the exact workflow requirements"""

        # Input 0: config file -- if you want to load preset input quickly.
        config_file = arcpy.Parameter(
            displayName="config_file_address",
            name="config_file",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        return [config_file]

#         # Input 1: State Counties
#         state_name = arcpy.Parameter(
#             displayName="state_name",
#             name="state_name",
#             datatype="GPString",
#             parameterType="Required",
#             direction="Input"
#         )
#
#         # Input 2: County Name Field #todo soheil: don't know what this is
#         county_field = arcpy.Parameter(
#             displayName="County Name Field",
#             name="county_field",
#             datatype="Field",
#             parameterType="Required",
#             direction="Input"
#         )
#         county_field.parameterDependencies = [state_name.name]
#
#         # Input 3: Selected Counties
#         county_names = arcpy.Parameter(
#             displayName="County Names (comma separated)",
#             name="county_names",
#             datatype="GPString",
#             parameterType="Required",
#             direction="Input"
#         )
#
#         # Input 4: Population Centers
#         population_fc = arcpy.Parameter(
#             displayName="Population Centers Layer",
#             name="population_fc",
#             datatype="DEFeatureClass",
#             parameterType="Required",
#             direction="Input"
#         )
#
#         # # Input 5: CBGs Outside Population Centers (User Input Parameter)
#         # cbg_outside_pop = arcpy.Parameter(
#         #     displayName="Census Block Groups Outside Population Centers",
#         #     name="cbg_outside_pop",
#         #     datatype="DEFeatureClass",
#         #     parameterType="Required",
#         #     direction="Input"
#         # )
#         # Input 5: Census Block Groups data from smart location dataset
#         sld_cbg_path = arcpy.Parameter(
#             displayName="Census Block Groups data from smart location dataset",
#             name="cbg_path",
#             datatype="DEFeatureClass",
#             parameterType="Required",
#             direction="Input"
#         )
#
#         # Input 6: State Roads
#         state_roads_fc = arcpy.Parameter(
#             displayName="State Roads Layer",
#             name="state_roads_fc",
#             datatype="DEFeatureClass",
#             parameterType="Required",
#             direction="Input"
#         )
#
#         # Input 7: County Roads
#         county_roads_fc = arcpy.Parameter(
#             displayName="County Roads Layer",
#             name="county_roads_fc",
#             datatype="DEFeatureClass",
#             parameterType="Required",
#             direction="Input"
#         )
#
#         # Input 8: Parcels
#         parcel_fc = arcpy.Parameter(
#             displayName="Parcels Layer",
#             name="parcel_fc",
#             datatype="DEFeatureClass",
#             parameterType="Required",
#             direction="Input"
#         )
#
#         # Input 9: Parcel Land Use Field -- todo: could be deleted
#         parcel_field = arcpy.Parameter(
#             displayName="Parcel Land Use Field",
#             name="parcel_field",
#             datatype="Field",
#             parameterType="Required",
#             direction="Input"
#         )
#         parcel_field.parameterDependencies = [parcel_fc.name]
#
#         # Input 10: POIs
#         poi_geojson = arcpy.Parameter(
#             displayName="Points of Interest (POI) Layer (geojson)",
#             name="poi_fc",
#             datatype="DEFeatureClass",
#             parameterType="Required",
#             direction="Input"
#         )
#
#         # Input 11: Road Buffer Distance
#         road_buffer_dist = arcpy.Parameter(
#             displayName="Buffer Distance around Roads for POI Analysis (feet)",
#             name="road_buffer_dist",
#             datatype="GPDouble",
#             parameterType="Optional",
#             direction="Input"
#         )
#         road_buffer_dist.value = 300
#
#         # Input 12: NCES Locale data for area type identification
#         nces_path = arcpy.Parameter(
#             displayName="NCES Locale data for area type identification",
#             name="nces_path",
#             datatype="DEFeatureClass",
#             parameterType="Required",
#             direction="Input"
#         )
#
#         # Output: Results Geodatabase
#         output_gdb = arcpy.Parameter(
#             displayName="Output Geodatabase",
#             name="output_gdb",
#             datatype="DEWorkspace",
#             parameterType="Optional",
#             direction="Input"
#         )
#         # Output: directory to save outputs
#         save_path = arcpy.Parameter(
#             displayName="Output save directory",
#             name="save_path",
#             datatype="DEWorkspace",
#             parameterType="Optional",
#             direction="Input"
#         )
#
#         return [
#             state_name, county_field, county_names, population_fc,
#             sld_cbg_path, state_roads_fc, county_roads_fc, parcel_fc,
#             parcel_field, poi_geojson, road_buffer_dist, nces_path, output_gdb, save_path
#         ]

    def execute(self, parameters, messages):
        """Execute the rural active transportation analysis following the exact workflow"""
        try:
            # Set environment settings
            arcpy.env.overwriteOutput = True

            # ###### option1: input all file names ######
#             self._extract_params_from_arcGIS(parameters)
            ## Uncomment when passing all inputs from ArcGIS (when .pyt file)


            ###### option2: input just a config file address ######
            parameters = _extract_params_from_config(parameters[0].valueAsText)
            ## uncomment when passing a config file from ArcGIS
            self._extract_params_from_list(parameters)
            ## uncomment when passing a config file from ArcGIS OR passing a list of inputs from test.py

            # Create output geodatabase if specified and doesn't exist
            if self.output_gdb != arcpy.env.scratchGDB and not arcpy.Exists(self.output_gdb):
                gdb_path = os.path.dirname(self.output_gdb)
                gdb_name = os.path.basename(self.output_gdb)
                os.makedirs(gdb_path, exist_ok=True)  # make sure folder exists
                arcpy.CreateFileGDB_management(gdb_path, gdb_name)

            arcpy.AddMessage("Starting Rural Active Transportation Infrastructure Analysis...")
            arcpy.AddMessage("=" * 60)

            # ==============================================================
            # STEP 0: PRE-PROCESSING
            # ==============================================================
            arcpy.AddMessage("Step 0: preprocessing...")

            # for developement, you can run this code once and then comment it for future runs when
            # outputs are still saved in save_path
#             preprocess(self.state_name, self.county_names, self.sld_cbg_path,
#                        self.population_fc, self.nces_path, self.parcel_fc, save_path=self.save_path)

            # ==============================================================
            # STEP 1: SELECT COUNTIES
            # ==============================================================
            arcpy.AddMessage("Step 1: Selecting Counties...")

            # the geodata for selected counties come from preprocessing where data is fetched from the internet
            # here we only load counties
            self.selected_counties = self.add_fc_from_geopackage('Step1_Selected_Counties',
                                                                 'studyarea.gpkg')
            county_count = int(arcpy.GetCount_management(self.selected_counties)[0])
            arcpy.AddMessage(f"   Selected {county_count} counties")

            # ==============================================================
            # STEP 2: POPULATION CENTERS
            # ==============================================================
            arcpy.AddMessage("Step 2: Finding Population Centers within Selected Counties...")

            # the geodata for pop centers within study area CAN come from preprocessing but if you prefer,
            # just uncomment the commented codes above and ignore the line below
            self.pop_centers_selected = self.add_fc_from_geopackage('Step2_Population_Centers',
                                                                    'POPULATION_CENTERS_STUDY_AREA.gpkg')
            pop_count = int(arcpy.GetCount_management(self.pop_centers_selected)[0])
            arcpy.AddMessage(f"   Found {pop_count} population centers")

            # ==============================================================
            # STEP 3: HIGHLIGHT CENSUS BLOCK GROUPS
            # ==============================================================
            arcpy.AddMessage("Step 3: Processing Census Block Groups outside Population Centers...")

            # use preprocessed data to obtain parts of CBGs within the study area that are right outside of
            # population centers, the parts of CBGs that intersect with pop centers are clipped in preprocessing

            # self.cbg_clipped = self.add_fc_from_geopackage('Step3_CBG_Right_Outside_PopCenters',
            #                                                'CBGs_RIGHT_OUTSIDE_PCs.gpkg')
            #todo 'CBGs_RIGHT_OUTSIDE_PCs.gpkg' has issues. go back to preprocessing -
            #  for now we can open CBGs_RIGHT_OUTSIDE_PCs.shp instead, but be aware of the bad column names in .shp file

            self.cbg_clipped = os.path.join(self.output_gdb, 'Step3_CBG_Right_Outside_PopCenters')
            cbg_out_pc_path = os.path.join(self.save_path, 'cbg_out_pc_shapefile', 'CBGs_RIGHT_OUTSIDE_PCs.shp')
            self._delete_if_exists(self.cbg_clipped)  # overwrite existing
            arcpy.CopyFeatures_management(cbg_out_pc_path, self.cbg_clipped)

            # CBGs that have no intersection with any pop center ('study_CBGs_outside' variable in preprocessing)
            self.cbg_out = self.add_fc_from_geopackage('Step3_CBG_not_intersect_PopCenters',
                                                       'CBGs_NOT_INTERSECT_PCs.gpkg')
            cbg_count = int(arcpy.GetCount_management(self.cbg_clipped)[0])
            arcpy.AddMessage(f"   {cbg_count} CBGs outside population centers in selected counties")

            # ==============================================================
            # STEP 4: ROADS - State and County Roads Outside Population Centers
            # ==============================================================
            arcpy.AddMessage("Step 4: Processing State and County Roads outside Population Centers...")

            # Process state and county roads
            state_roads_processed = self.process_roads(self.state_roads_fc, "State")
            county_roads_processed = self.process_roads(self.county_roads_fc, "County")

            # Merge state and county roads
            self.all_roads_outside_pop = os.path.join(self.output_gdb, "Step4_All_Roads_Outside_PopCenters")
            self._delete_if_exists(self.all_roads_outside_pop)
            arcpy.Merge_management([state_roads_processed, county_roads_processed], self.all_roads_outside_pop)

            # Intersect roads with CBGs outside population centers
            self.roads_final = os.path.join(self.output_gdb, "Step4_Roads_Final_In_CBG_Outside_PopCenters")
            self._delete_if_exists(self.roads_final)
            arcpy.Intersect_analysis([self.all_roads_outside_pop, self.cbg_clipped], self.roads_final)

            # Calculate road length
            total_length = 0
            with arcpy.da.SearchCursor(self.roads_final, ["SHAPE@LENGTH"]) as cursor:
                for row in cursor:
                    total_length += row[0]
            total_miles = total_length / 5280

            arcpy.AddMessage(f"   Rural roads network: {total_miles:.2f} miles")

            # ==============================================================
            # STEP 5: PARCELS DATA IN CBGs OUTSIDE POPULATION CENTERS
            # ==============================================================
            arcpy.AddMessage("Step 5: Filtering Residential Parcels in rural CBGs...")

            # # Clip parcels to CBGs outside population centers
            # parcels_in_cbg = os.path.join(self.output_gdb, "Temp_Parcels_In_CBG")
            # self._delete_if_exists(parcels_in_cbg)
            # arcpy.AddMessage(f"\t clipping parcels in rural CBGs...")
            # arcpy.Clip_analysis(self.parcel_fc, self.cbg_clipped, parcels_in_cbg)
            # # throws an error - fix it - also suggest to use union of selected_counties as the mask
            # # Filter residential parcels (land use codes 11-15) # todo: suggestion: filter first
            # self.residential_parcels = os.path.join(self.output_gdb, "Step5_Residential_Parcels_Rural")
            # self._delete_if_exists(self.residential_parcels)
            # # Create selection for residential land use codes
            # arcpy.MakeFeatureLayer_management(parcels_in_cbg, "parcels_temp_lyr")
            # residential_where = f"{self.parcel_field} >= 11 AND {self.parcel_field} <= 15"
            # arcpy.SelectLayerByAttribute_management("parcels_temp_lyr", "NEW_SELECTION", residential_where)
            # arcpy.CopyFeatures_management("parcels_temp_lyr", self.residential_parcels)
            # # Clean up
            # self._delete_if_exists(parcels_in_cbg)


            ## soheil: the code above was not working on my system for problems in parcel data geometry. I added a
            ## preprocess_parcel function to preprocess tool and saved the clipped residential parcels. This speeds up
            ## debugging since we can run preprocess once and then have it commented.
            # Also, I used make_valid function there and fixed the issue. I think using 'repair geometry' tool is also
            # helpful but that takes very long time (15 mins) compared to gdf.make_valid()
            # above: returns 11587 as parcel_count IF arcpy.management.RepairGeometry() (either here or in arcgis)
            # is previously applied to the data
            # preprocess.preprocess_parcels(): also returns 11587 parcel counts
            # todo: check this with panick's outputs

            self.residential_parcels = self.add_fc_from_geopackage("Step5_Residential_Parcels_all",
                                                                   'parcels_in_studyarea.gpkg')
#             self.residential_parcels = self.add_fc_from_geopackage("Step5_Residential_Parcels_Rural",
#                                                                    'parcels_out_pc.gpkg')

            parcel_count = int(arcpy.GetCount_management(self.residential_parcels)[0])
            arcpy.AddMessage(f"   {parcel_count} residential parcels in rural CBGs")

            # ==============================================================
            # STEP 6: POIs ALONG STATE AND COUNTY ROADS (300ft Buffer)
            # ==============================================================
            arcpy.AddMessage(f"Step 6: Finding POIs within {self.road_buffer_dist}ft of rural roads...")

            self.pois_accessible_filtered = self.step6_process_POIs()
            poi_count = int(arcpy.GetCount_management(self.pois_accessible_filtered)[0])
            arcpy.AddMessage(f"   {poi_count} POIs accessible from rural roads")

            # ==============================================================
            # ADD RESULTS TO MAP AND GENERATE SUMMARY
            # ==============================================================
            arcpy.AddMessage("Adding results to map...")

            try:
                aprx = arcpy.mp.ArcGISProject("CURRENT")
                map_obj = aprx.activeMap

                # Add key layers to map with descriptive names
                layer_info = [
                    (self.selected_counties, "Selected Counties"),
                    (self.pop_centers_selected, "Population Centers"),
                    (self.cbg_clipped, "Rural CBGs (Outside Pop Centers)"),
                    (self.roads_final, "Rural Roads Network"),
                    (self.residential_parcels, "Rural Residential Parcels--FIX IT"),
                    (self.roads_buffer, "Road Access Buffer Zone"),
                    (self.pois_accessible_filtered, "Accessible POIs")
                ]

                for layer_path, layer_name in layer_info:
                    if arcpy.Exists(layer_path):
                        layer = map_obj.addDataFromPath(layer_path)
                        if hasattr(layer, 'name'):
                            layer.name = layer_name

                # Zoom to extent of selected counties
                map_view = aprx.activeView
                if map_view:
                    map_view.zoomToAllLayers()

            except Exception as e:
                arcpy.AddWarning(f"Could not add layers to map: {str(e)}")

            # ==============================================================
            # FINAL SUMMARY
            # ==============================================================
            arcpy.AddMessage("=" * 60)
            arcpy.AddMessage("RURAL ACTIVE TRANSPORTATION ANALYSIS COMPLETE!")
            arcpy.AddMessage("=" * 60)
            arcpy.AddMessage(f"Counties Analyzed: {county_count}")
            arcpy.AddMessage(f"Population Centers: {pop_count}")
            arcpy.AddMessage(f"Rural CBGs (outside pop centers): {cbg_count}")
            arcpy.AddMessage(f"Rural Road Network: {total_miles:.2f} miles")
            arcpy.AddMessage(f"Residential Parcels in Rural Areas: {parcel_count}")
            arcpy.AddMessage(f"POIs Accessible from Rural Roads: {poi_count}")
            arcpy.AddMessage(f"Results saved to: {self.output_gdb}")
            arcpy.AddMessage("=" * 60)

            # Key outputs summary
            key_outputs = [
                f"✓ Step 1: {self.selected_counties}",
                f"✓ Step 2: {self.pop_centers_selected}",
                f"✓ Step 3: {self.cbg_clipped}",
                f"✓ Step 4: {self.roads_final}",
                f"✓ Step 5: {self.residential_parcels}",
                f"✓ Step 6: {self.pois_accessible_filtered}",
                f"✓ Buffer Zone: {self.roads_buffer}"
            ]

            arcpy.AddMessage("KEY OUTPUTS:")
            for output in key_outputs:
                arcpy.AddMessage(f"  {output}")

            arcpy.AddMessage("\n🎯 Analysis Focus: Active transportation infrastructure gaps")
            arcpy.AddMessage("   between rural residential clusters and accessible services")

        except Exception as e:
            arcpy.AddError(f"Error in Rural Active Transportation Analysis: {str(e)}")
            import traceback
            arcpy.AddError(traceback.format_exc())
            raise

    def add_fc_from_geopackage(self, fc_layer_name: str,
                               geopackage_filename: str) -> str:
        """
        reads the first layer of the geopackge file inside the save_path used during the preprocessing,
        and then adds a new feature class to the output_gdb of the class

        :param fc_layer_name: the layer name your want to add to the output_gdb
        :param geopackage_filename: the geopackage file saved in self.save_path
        :return: fc_layer_path: use it for future references to the added feature class layer
        """
        fc_layer_path = os.path.join(self.output_gdb, fc_layer_name)
        geopackage_layer_path = os.path.join(self.save_path, geopackage_filename)
        gpkg_layer = gpd.list_layers(geopackage_layer_path)['name'][0]
        geopackage_layer_path = os.path.join(geopackage_layer_path, gpkg_layer)
        self._delete_if_exists(fc_layer_path) # overwrite existing
        # arcpy.MakeFeatureLayer_management(geopackage_layer_path, fc_layer_path)
        # #todo this is wrong-- to fix, use the line below to copy data and actualy save steps in the out.gdb.
        #  However, it does not work becuase CBGs_out_pc are not correctly generated for some reason.
        #  See preprocess.filter_CBGs_by_pop_center()
        arcpy.CopyFeatures_management(geopackage_layer_path, fc_layer_path)
        return fc_layer_path

        # fc_layer_path = os.path.join(self.output_gdb, fc_layer_name)
        # geopackage_layer_path = os.path.join(self.save_path, geopackage_filename)
        # # find first layer name in gpkg
        # gpkg_layer = gpd.list_layers(geopackage_layer_path)['name'][0]
        # # build full "path|layer" reference for arcpy
        # gpkg_layer_path = f"{geopackage_layer_path}|layername={gpkg_layer}"
        # # overwrite existing
        # self._delete_if_exists(fc_layer_path)
        # # export to gdb
        # arcpy.conversion.FeatureClassToFeatureClass(
        #     in_features=gpkg_layer_path,
        #     out_path=self.output_gdb,
        #     out_name=fc_layer_name
        # )
        # return fc_layer_path

    def process_roads(self, roads_fc: str, road_type: str) -> str:
        """
        Function to process roads (clip to counties, remove from pop centers)
        :param roads_fc: path to the roads dataset (user input)
        :param road_type: road type name (string)
        :return:
        """
        # Clip roads to selected counties
        roads_clipped = os.path.join(self.output_gdb, f"Temp_{road_type}_Roads_Clipped")
        self._delete_if_exists(roads_clipped)
        arcpy.Clip_analysis(roads_fc, self.selected_counties, roads_clipped)

        # Remove roads inside population centers
        roads_outside_pop = os.path.join(self.output_gdb, f"Step4_{road_type}_Roads_Outside_PopCenters")
        self._delete_if_exists(roads_outside_pop)
        arcpy.Erase_analysis(roads_clipped, self.pop_centers_selected, roads_outside_pop)
        # C:\Users\Soheil99\OneDrive - UW\0
        # Research\UW
        # Tacoma\my
        # copy - Satellite
        # Communities
        # Project\Analysis\RuralATGapFinder\out\out.gdb\Temp_State_Roads_Clipped
        self._delete_if_exists(roads_clipped)  # Clean up temporary data
        return roads_outside_pop

    def step6_process_POIs(self):
        poi_fc = os.path.join(self.output_gdb, "Temp_POIs_all")
        # POI data that we have originally is in geojson format so I first turn it into feature layer
        arcpy.conversion.JSONToFeatures(
            in_json_file=self.poi_geojson,
            out_features=poi_fc,
            geometry_type="POINT"
        )

        # Remove POIs inside population centers -
        # todo: people may want to travel into pop center's I don't think this step is needed
        pois_outside_pop = os.path.join(self.output_gdb, "Temp_POIs_Outside_PopCenters")
        self._delete_if_exists(pois_outside_pop)
        arcpy.Erase_analysis(poi_fc, self.pop_centers_selected, pois_outside_pop)
        # Create buffer around rural roads
        self.roads_buffer = os.path.join(self.output_gdb, "Step6_Roads_Buffer_Zone")
        self._delete_if_exists(self.roads_buffer)
        arcpy.Buffer_analysis(self.roads_final, self.roads_buffer,
                              f"{self.road_buffer_dist} Feet",
                              "FULL", "ROUND", "ALL")
        # Find POIs within buffer of rural roads
        temp_name = "Temp_POIs_Accessible_From_Rural_Roads"
        pois_accessible = os.path.join(self.output_gdb, temp_name)
        self._delete_if_exists(pois_accessible)
        arcpy.Clip_analysis(pois_outside_pop, self.roads_buffer, pois_accessible)

        # Clean up
        self._delete_if_exists(pois_outside_pop)
        self._delete_if_exists(poi_fc)

        ## new -- filter POIs from R analysis codes
        _, filtered_POIs_filename = filter_POIs(self.output_gdb,
                                                temp_name,
                                                self.save_path)
        # In R files CR and SR roads were analysed separately tho todo: check this
        pois_accessible_filtered_path = (
            self.add_fc_from_geopackage("Step6_POIs_Accessible_From_Rural_Roads_Filtered",
                                        filtered_POIs_filename)
        )
        self._delete_if_exists(poi_fc)
        return pois_accessible_filtered_path

    def _delete_if_exists(self, dataset):
        """Helper function to delete dataset if it exists"""
        if arcpy.Exists(dataset):
            try:
                arcpy.Delete_management(dataset)
            except:
                pass  # Continue if deletion fails

    def _extract_params_from_list(self, parameters):
        self.state_name = parameters[0]
        # county_field = parameters[1]
        self.county_names = parameters[2]
        self.population_fc = parameters[3]
        self.sld_cbg_path = parameters[4]
        self.state_roads_fc = parameters[5]
        self.county_roads_fc = parameters[6]
        self.parcel_fc = parameters[7]
        self.parcel_field = parameters[8]
        self.poi_geojson = parameters[9]
        self.road_buffer_dist = float(parameters[10] or 300)
        self.nces_path = parameters[11]
        self.output_gdb = parameters[12]
        self.save_path = parameters[13]

    def _extract_params_from_arcGIS(self, parameters):
        """
        :param parameters: all parameters that are passed from ArcGIS
        :return:
        """
        self.state_name = parameters[0].valueAsText
        # self.county_field = parameters[1].valueAsText
        self.county_names = parameters[2].valueAsText
        self.county_names = [f'{c.strip()}' for c in self.county_names.split(",")]
        arcpy.AddMessage(self.county_names)
        self.population_fc = parameters[3].valueAsText
        #self.cbg_outside_pop = parameters[4].valueAsText
        self.sld_cbg_path = parameters[4].valueAsText
        self.state_roads_fc = parameters[5].valueAsText
        self.county_roads_fc = parameters[6].valueAsText
        self.parcel_fc = parameters[7].valueAsText
        # self.parcel_field = parameters[8].valueAsText
        self.poi_geojson = parameters[9].valueAsText
        self.road_buffer_dist = float(parameters[10].value or 300)
        self.nces_path = parameters[11].valueAsText
        self.output_gdb = parameters[12].valueAsText or arcpy.env.scratchGDB
        self.save_path = parameters[13].valueAsText



def _extract_params_from_config(config_file):
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    return list(config.values())
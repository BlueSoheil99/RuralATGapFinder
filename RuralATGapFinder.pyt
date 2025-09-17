import os
import arcpy
import geopandas as gpd

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

        # Input 1: State Counties
        state_name = arcpy.Parameter(
            displayName="state_name",
            name="state_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )

        # Input 2: County Name Field #todo soheil: don't know what this is
        county_field = arcpy.Parameter(
            displayName="County Name Field",
            name="county_field",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
        county_field.parameterDependencies = [state_name.name]

        # Input 3: Selected Counties
        county_names = arcpy.Parameter(
            displayName="County Names (comma separated)",
            name="county_names",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )

        # Input 4: Population Centers
        population_fc = arcpy.Parameter(
            displayName="Population Centers Layer",
            name="population_fc",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
        )

        # # Input 5: CBGs Outside Population Centers (User Input Parameter)
        # cbg_outside_pop = arcpy.Parameter(
        #     displayName="Census Block Groups Outside Population Centers",
        #     name="cbg_outside_pop",
        #     datatype="DEFeatureClass",
        #     parameterType="Required",
        #     direction="Input"
        # )
        # Input 5: Census Block Groups data from smart location dataset
        sld_cbg_path = arcpy.Parameter(
            displayName="Census Block Groups data from smart location dataset",
            name="cbg_path",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
        )

        # Input 6: State Roads
        state_roads_fc = arcpy.Parameter(
            displayName="State Roads Layer",
            name="state_roads_fc",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
        )

        # Input 7: County Roads
        county_roads_fc = arcpy.Parameter(
            displayName="County Roads Layer",
            name="county_roads_fc",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
        )

        # Input 8: Parcels
        parcel_fc = arcpy.Parameter(
            displayName="Parcels Layer",
            name="parcel_fc",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
        )

        # Input 9: Parcel Land Use Field
        parcel_field = arcpy.Parameter(
            displayName="Parcel Land Use Field",
            name="parcel_field",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
        parcel_field.parameterDependencies = [parcel_fc.name]

        # Input 10: POIs
        poi_gjson = arcpy.Parameter(
            displayName="Points of Interest (POI) Layer (geojson)",
            name="poi_fc",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
        )

        # Input 11: Road Buffer Distance
        road_buffer_dist = arcpy.Parameter(
            displayName="Buffer Distance around Roads for POI Analysis (feet)",
            name="road_buffer_dist",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input"
        )
        road_buffer_dist.value = 300

        # Input 12: NCES Locale data for area type identification
        nces_path = arcpy.Parameter(
            displayName="NCES Locale data for area type identification",
            name="nces_path",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
        )

        # Output: Results Geodatabase
        output_gdb = arcpy.Parameter(
            displayName="Output Geodatabase",
            name="output_gdb",
            datatype="DEWorkspace",
            parameterType="Optional",
            direction="Input"
        )
        # Output: directory to save outputs
        save_path = arcpy.Parameter(
            displayName="Output save directory",
            name="save_path",
            datatype="DEWorkspace",
            parameterType="Optional",
            direction="Input"
        )

        return [
            state_name, county_field, county_names, population_fc,
            sld_cbg_path, state_roads_fc, county_roads_fc, parcel_fc,
            parcel_field, poi_gjson, road_buffer_dist, nces_path, output_gdb, save_path
        ]

    def execute(self, parameters, messages):
        """Execute the rural active transportation analysis following the exact workflow"""
        
        try:
            # Set environment settings
            arcpy.env.overwriteOutput = True
            
            # Get parameters
            state_name = parameters[0].valueAsText
            # county_field = parameters[1].valueAsText
            county_names = parameters[2].valueAsText
            county_names = [f"'{c.strip()}'" for c in county_names.split(",")]
            population_fc = parameters[3].valueAsText
            # cbg_outside_pop = parameters[4].valueAsText
            sld_cbg_path = parameters[4].valueAsText
            state_roads_fc = parameters[5].valueAsText
            county_roads_fc = parameters[6].valueAsText
            parcel_fc = parameters[7].valueAsText
            parcel_field = parameters[8].valueAsText
            poi_fc = parameters[9].valueAsText
            road_buffer_dist = float(parameters[10].value or 300)
            nces_path = parameters[11].valueAsText
            output_gdb = parameters[12].valueAsText or arcpy.env.scratchGDB
            save_path = parameters[13].valueAsText

#             # Get parameters --- uncomment this section when debugging through a python .py file
#             state_name = parameters[0]
#             # county_field = parameters[1]
#             county_names = parameters[2]
#             population_fc = parameters[3]
#             sld_cbg_path = parameters[4]
#             state_roads_fc = parameters[5]
#             county_roads_fc = parameters[6]
#             parcel_fc = parameters[7]
#             parcel_field = parameters[8]
#             poi_gjson = parameters[9]
#             road_buffer_dist = float(parameters[10] or 300)
#             nces_path = parameters[11]
#             output_gdb = parameters[12]
#             save_path = parameters[13]

            # Create output geodatabase if specified and doesn't exist
            if output_gdb != arcpy.env.scratchGDB and not arcpy.Exists(output_gdb):
                gdb_path = os.path.dirname(output_gdb)
                gdb_name = os.path.basename(output_gdb)
                arcpy.CreateFileGDB_management(gdb_path, gdb_name)
            
            arcpy.AddMessage("Starting Rural Active Transportation Infrastructure Analysis...")
            arcpy.AddMessage("="*60)

            # ==============================================================
            # STEP 0: PRE-PROCESSING
            # ==============================================================
            arcpy.AddMessage("Step 0: preprocessing...")

            (studyarea, study_CBGs, study_CBGs_outside_PCs, study_CBGs_outside,
             study_CBGs_with_PCs, pop_centers_study_area) = (
                preprocess(state_name, county_names, sld_cbg_path,
                           population_fc, nces_path, save_path=save_path))

            # ==============================================================
            # STEP 1: SELECT COUNTIES
            # ==============================================================
            arcpy.AddMessage("Step 1: Selecting Counties...")

            # # Parse county names and create selection
            # counties_list = [f"'{c.strip()}'" for c in county_names.split(",")]
            # where_clause = f"{county_field} IN ({','.join(counties_list)})"
            #
            # # Create feature layer and select counties
            # arcpy.MakeFeatureLayer_management(state_counties_fc, "counties_temp_lyr")
            # arcpy.SelectLayerByAttribute_management("counties_temp_lyr", "NEW_SELECTION", where_clause)
            #
            # # Save selected counties
            # selected_counties = os.path.join(output_gdb, "Step1_Selected_Counties")
            # self._delete_if_exists(selected_counties)
            # arcpy.CopyFeatures_management("counties_temp_lyr", selected_counties)

            selected_counties = os.path.join(output_gdb, 'Step1_Selected_Counties')
            # read 'studyarea.gpkg' only layer
            studyarea_layer_path = os.path.join(save_path, 'studyarea.gpkg')
            gpkg_layer=gpd.list_layers(studyarea_layer_path)['name'][0]
            studyarea_layer_path = os.path.join(studyarea_layer_path, gpkg_layer)
            arcpy.MakeFeatureLayer_management(studyarea_layer_path, selected_counties)

            county_count = int(arcpy.GetCount_management(selected_counties)[0])
            arcpy.AddMessage(f"   Selected {county_count} counties")
            
            # ==============================================================
            # STEP 2: POPULATION CENTERS
            # ==============================================================
            arcpy.AddMessage("Step 2: Finding Population Centers within Selected Counties...")
            
            # # Find population centers within selected counties
            # arcpy.MakeFeatureLayer_management(population_fc, "pop_centers_temp_lyr")
            # arcpy.SelectLayerByLocation_management("pop_centers_temp_lyr", "INTERSECT", selected_counties)
            # # Save population centers in selected counties
            # pop_centers_selected = os.path.join(output_gdb, "Step2_Population_Centers")
            # self._delete_if_exists(pop_centers_selected)
            # arcpy.CopyFeatures_management("pop_centers_temp_lyr", pop_centers_selected)

            pop_centers_selected = os.path.join(output_gdb, 'Step2_Population_Centers')
            pop_centers_layer_path = os.path.join(save_path, 'POPULATION_CENTERS_STUDY_AREA.gpkg')
            gpkg_layer = gpd.list_layers(pop_centers_layer_path)['name'][0]
            pop_centers_layer_path = os.path.join(pop_centers_layer_path, gpkg_layer)
            arcpy.MakeFeatureLayer_management(pop_centers_layer_path, pop_centers_selected)

            pop_count = int(arcpy.GetCount_management(pop_centers_selected)[0])
            arcpy.AddMessage(f"   Found {pop_count} population centers")
            
            # ==============================================================
            # STEP 3: HIGHLIGHT CENSUS BLOCK GROUPS
            # ==============================================================
            arcpy.AddMessage("Step 3: Processing Census Block Groups outside Population Centers...")

            # # Clip user-provided CBGs outside population centers to selected counties
            # cbg_clipped = os.path.join(output_gdb, "Step3_CBG_Outside_PopCenters")
            # self._delete_if_exists(cbg_clipped)
            # arcpy.Clip_analysis(cbg_outside_pop, selected_counties, cbg_clipped)

            cbg_clipped = os.path.join(output_gdb, 'Step3_CBG_Outside_PopCenters')
            cbg_out_pc_layer_path = os.path.join(save_path, 'CBGs_RIGHT_OUTSIDE_PCs.gpkg')
            gpkg_layer = gpd.list_layers(cbg_out_pc_layer_path)['name'][0]
            cbg_out_pc_layer_path = os.path.join(cbg_out_pc_layer_path, gpkg_layer)
            arcpy.MakeFeatureLayer_management(cbg_out_pc_layer_path, cbg_clipped)
            
            cbg_count = int(arcpy.GetCount_management(cbg_clipped)[0])
            arcpy.AddMessage(f"   {cbg_count} CBGs outside population centers in selected counties")
            
            # ==============================================================
            # STEP 4: ROADS - State and County Roads Outside Population Centers
            # ==============================================================
            arcpy.AddMessage("Step 4: Processing State and County Roads outside Population Centers...")
            
            # Function to process roads (clip to counties, remove from pop centers)
            def process_roads(roads_fc, road_type):
                # Clip roads to selected counties
                roads_clipped = os.path.join(output_gdb, f"Temp_{road_type}_Roads_Clipped")
                self._delete_if_exists(roads_clipped)
                arcpy.Clip_analysis(roads_fc, selected_counties, roads_clipped)
                
                # Remove roads inside population centers
                roads_outside_pop = os.path.join(output_gdb, f"Step4_{road_type}_Roads_Outside_PopCenters")
                self._delete_if_exists(roads_outside_pop)
                arcpy.Erase_analysis(roads_clipped, pop_centers_selected, roads_outside_pop)
                
                # Clean up temporary data
                self._delete_if_exists(roads_clipped)
                
                return roads_outside_pop
            
            # Process state and county roads
            state_roads_processed = process_roads(state_roads_fc, "State")
            county_roads_processed = process_roads(county_roads_fc, "County")
            
            # Merge state and county roads
            all_roads_outside_pop = os.path.join(output_gdb, "Step4_All_Roads_Outside_PopCenters")
            self._delete_if_exists(all_roads_outside_pop)
            arcpy.Merge_management([state_roads_processed, county_roads_processed], all_roads_outside_pop)
            
            # Intersect roads with CBGs outside population centers
            roads_final = os.path.join(output_gdb, "Step4_Roads_Final_In_CBG_Outside_PopCenters")
            self._delete_if_exists(roads_final)
            arcpy.Intersect_analysis([all_roads_outside_pop, cbg_clipped], roads_final)
            
            # Calculate road length
            total_length = 0
            with arcpy.da.SearchCursor(roads_final, ["SHAPE@LENGTH"]) as cursor:
                for row in cursor:
                    total_length += row[0]
            total_miles = total_length / 5280
            
            arcpy.AddMessage(f"   Rural roads network: {total_miles:.2f} miles")
            
            # ==============================================================
            # STEP 5: PARCELS DATA IN CBGs OUTSIDE POPULATION CENTERS
            # ==============================================================
            arcpy.AddMessage("Step 5: Filtering Residential Parcels in rural CBGs...")
            
            # Clip parcels to CBGs outside population centers
            parcels_in_cbg = os.path.join(output_gdb, "Temp_Parcels_In_CBG")
            self._delete_if_exists(parcels_in_cbg)
            arcpy.Clip_analysis(parcel_fc, cbg_clipped, parcels_in_cbg)
            
            # Filter residential parcels (land use codes 11-15)
            residential_parcels = os.path.join(output_gdb, "Step5_Residential_Parcels_Rural")
            self._delete_if_exists(residential_parcels)
            
            # Create selection for residential land use codes
            arcpy.MakeFeatureLayer_management(parcels_in_cbg, "parcels_temp_lyr")
            residential_where = f"{parcel_field} >= 11 AND {parcel_field} <= 15"
            arcpy.SelectLayerByAttribute_management("parcels_temp_lyr", "NEW_SELECTION", residential_where)
            arcpy.CopyFeatures_management("parcels_temp_lyr", residential_parcels)
            
            # Clean up
            self._delete_if_exists(parcels_in_cbg)
            
            parcel_count = int(arcpy.GetCount_management(residential_parcels)[0])
            arcpy.AddMessage(f"   {parcel_count} residential parcels in rural CBGs")
            
            # ==============================================================
            # STEP 6: POIs ALONG STATE AND COUNTY ROADS (300ft Buffer)
            # ==============================================================
            arcpy.AddMessage(f"Step 6: Finding POIs within {road_buffer_dist}ft of rural roads...")
            poi_fc = poi_gjson # todo   -- read poi
            # Remove POIs inside population centers
            pois_outside_pop = os.path.join(output_gdb, "Temp_POIs_Outside_PopCenters")
            self._delete_if_exists(pois_outside_pop)
            arcpy.Erase_analysis(poi_fc, pop_centers_selected, pois_outside_pop)

            # Create buffer around rural roads
            roads_buffer = os.path.join(output_gdb, "Step6_Roads_Buffer_Zone")
            self._delete_if_exists(roads_buffer)
            arcpy.Buffer_analysis(roads_final, roads_buffer, f"{road_buffer_dist} Feet", "FULL", "ROUND", "ALL")
            
            # Find POIs within buffer of rural roads
            pois_accessible = os.path.join(output_gdb, "Step6_POIs_Accessible_From_Rural_Roads")
            self._delete_if_exists(pois_accessible)
            arcpy.Clip_analysis(pois_outside_pop, roads_buffer, pois_accessible)
            
            # Clean up
            self._delete_if_exists(pois_outside_pop)
            
            poi_count = int(arcpy.GetCount_management(pois_accessible)[0])
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
                    (selected_counties, "Selected Counties"),
                    (pop_centers_selected, "Population Centers"),
                    (cbg_clipped, "Rural CBGs (Outside Pop Centers)"),
                    (roads_final, "Rural Roads Network"),
                    (residential_parcels, "Rural Residential Parcels"),
                    (roads_buffer, "Road Access Buffer Zone"),
                    (pois_accessible, "Accessible POIs")
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
            arcpy.AddMessage("="*60)
            arcpy.AddMessage("RURAL ACTIVE TRANSPORTATION ANALYSIS COMPLETE!")
            arcpy.AddMessage("="*60)
            arcpy.AddMessage(f"Counties Analyzed: {county_count}")
            arcpy.AddMessage(f"Population Centers: {pop_count}")
            arcpy.AddMessage(f"Rural CBGs (outside pop centers): {cbg_count}")
            arcpy.AddMessage(f"Rural Road Network: {total_miles:.2f} miles")
            arcpy.AddMessage(f"Residential Parcels in Rural Areas: {parcel_count}")
            arcpy.AddMessage(f"POIs Accessible from Rural Roads: {poi_count}")
            arcpy.AddMessage(f"Results saved to: {output_gdb}")
            arcpy.AddMessage("="*60)
            
            # Key outputs summary
            key_outputs = [
                f"✓ Step 1: {selected_counties}",
                f"✓ Step 2: {pop_centers_selected}",
                f"✓ Step 3: {cbg_clipped}",
                f"✓ Step 4: {roads_final}",
                f"✓ Step 5: {residential_parcels}",
                f"✓ Step 6: {pois_accessible}",
                f"✓ Buffer Zone: {roads_buffer}"
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
    
    def _delete_if_exists(self, dataset):
        """Helper function to delete dataset if it exists"""
        if arcpy.Exists(dataset):
            try:
                arcpy.Delete_management(dataset)
            except:
                pass  # Continue if deletion fails
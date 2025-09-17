import os

import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pygris
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection
from shapely.ops import unary_union
from shapely.validation import make_valid

from .utils import _save_geopackage, _polygon_to_multipolygon, _geomcollection_to_multipolygon


CRS = 32610
# todo check the order of .to_crs functions
sld_selected_columns = ['GEOID10', 'CSA_Name', 'CBSA_Name', 'Ac_Land', 'Ac_Unpr', 'Ac_Water', 'TotPop', 'CountHU',
                        'HH', 'P_WrkAge', 'White', 'Male', 'Residents', 'Drivers', 'Vehicles', 'GasPrice', 'Pct_AO0',
                        'R_LowWageWk', 'R_MedWageWk', 'R_HiWageWk', 'R_PCTLOWWAGE', 'E_LowWageWk', 'E_MedWageWk',
                        'E_HiWageWk', 'E_PctLowWage', 'D3A', 'D3AAO', 'D3AMM', 'D3APO', 'D3B', 'D3BAO', 'D3BMM3',
                        'D3BMM4', 'D3BPO3', 'D3BPO4', 'D4A', 'D4B025', 'D4B050', 'D4C', 'D4D', 'D4E', 'D5AR', 'D5AE',
                        'D5BR', 'D5BE', 'geometry']
columns_to_keep = [
    'GEOID10', 'CSA_Name', 'CBSA_Name', 'R_PCTLOWWAGE', 'E_PctLowWage',
    'LowWage_Category_Home', 'LowWage_Category_Work', 'LowWage_Combined_home_work', 'LOCALE'
]



def _custom_summary(x):
    return pd.Series({
        "N": x.count(),
        "Q1": x.quantile(0.25),
        "Q3": x.quantile(0.75),
        "Mean": x.mean(),
        "SD": x.std(),
        "Median [Min, Max]": f"{x.median():.2f} [{x.min():.2f}, {x.max():.2f}]"
    })


def _categorical_summary(df, col4rows, col4columns):
    counts = (
        df
        .groupby([df[col4rows], df[col4columns]], observed=True)
        .size()
        .unstack(fill_value=0)
    )
    percentages = counts.div(counts.sum(axis=0), axis=1) * 100
    # Combine "count (pct%)"
    combined = counts.astype(str) + " (" + percentages.round(1).astype(str) + "%)"
    return combined


def get_study_area(state, counties, save_map_path=None):
    print("\n---- loading study area")
    # Get TIGER/Line file for counties in a specific state
    state_counties = pygris.counties(state = state, cb=True, year=2023)
    # using cb=True we can exclude water bodies to some extent
    studyarea = state_counties[state_counties["NAME"].isin(counties)]
    state_FIPS = studyarea.STATEFP.iloc[0]

    if save_map_path:
        fig, ax = plt.subplots(figsize=(8, 8))
        studyarea.plot(ax=ax, facecolor="white", edgecolor="gray")
        for _, row in studyarea.iterrows():
            plt.annotate(
                row["NAME"],
                (row.geometry.centroid.x, row.geometry.centroid.y),
                fontsize=8, color="blue", fontweight='bold',
                ha="center",   # horizontal alignment
                va="center"    # vertical alignment
            )
        ax.annotate('N', xy=(0.1, 0.95), xytext=(0.1, 0.85),
                    arrowprops=dict(facecolor='black', width=3, headwidth=10),
                    ha='center', va='center', fontsize=12,
                    xycoords='axes fraction')
        plt.axis("off")
        plt.title(f"{state} Study Area Counties")
        plt.savefig(save_map_path)
        print("---- \t map saved to {}".format(save_map_path))
    return studyarea, state_FIPS


def get_smart_location_db(database_path, state_fips, database_layer="EPA_SLD_Database_V3"):
    print("\n---- loading EPA smart location database for state_fips={}".format(state_fips))
    US_SLD_CBG = gpd.read_file(database_path, layer=database_layer)
    # filter selected state only (example: WA = 53)
    state_SLD_CBG = US_SLD_CBG[US_SLD_CBG["STATEFP"] == state_fips]
    return state_SLD_CBG


def filter_CBGs_by_area_and_columns(SLD_gdf, studyarea_gdf):
    SLD_gdf = SLD_gdf.to_crs(studyarea_gdf.crs)
    # filter CBGs based on county code and land area
    study_CBGs = SLD_gdf[SLD_gdf['COUNTYFP'].isin(studyarea_gdf['COUNTYFP'])]
    # Remove water from geometries as much as possible  TODO can we do better?
    study_CBGs = study_CBGs[study_CBGs['Ac_Land'] > 0]
    study_CBGs = gpd.clip(study_CBGs, studyarea_gdf)
    #todo remove it or keep it? if remove, results of this file will be identical with Panick's R file
    # remove water from land by clipping (NEW** not present in R file)
    # we can do this because we had cb=True in pygris.counties(state = state_in, cb=True, year=2023)
    # turn everything into MultiPolygon.
    print(f'\n---- loaded {len(study_CBGs)} census block groups in the following '
          f'core-based statistical areas: {study_CBGs["CBSA_Name"].unique()}')
    _polygon_to_multipolygon(study_CBGs)
    study_CBGs = study_CBGs.loc[:, sld_selected_columns]
    return study_CBGs


def filter_CBGs_by_pop_center(CBG_gdf, pop_center_gdf):
    print(f'\n---- Interescting census block groups and population centers')
    # Let see the CBGs that do not intersect population centers
    # Find intersections
    CBG_gdf['intersects_w_pop_center'] = CBG_gdf.geometry.apply(lambda x: pop_center_gdf.intersects(x).any())

    # Keep only those that do NOT intersect
    CBGs_outside = CBG_gdf[CBG_gdf.intersects_w_pop_center == False]
    print(f'----\t {len(CBGs_outside)} census block groups have no intersection with population centers')
    # I want to keep only CBGs that intercept population centers out.
    CBGs_with_PCs = CBG_gdf[CBG_gdf.intersects_w_pop_center == True]
    print(f'----\t {len(CBGs_with_PCs)} census block groups intersect with population centers')
    # 3590 CBGs, about 96.77% of the initial number of CBGs

    ## Get the parts of CBGs that are Just *outside* the population centers
    # based on the original example, we should get 1335 rows in the output dataframe.
    # ## 1- One way is to use overlay() function.  -------------------------------------------------------------------------
    # diff = gpd.overlay(study_CBGs[WA_SLD_study.intersects_w_pop_center==True].to_crs(CRS),
    #                    pop_center_gdf, how='difference')
    # diff = gpd.overlay(WA_SLD_study_PC, population_centers,
    #                    keep_geom_type=True, how='difference')
    # diff.explore()  # if we look at the map, there will be super small polygons, on Seattle for example,
    # # that are not in the R file and the original example
    ## 2- The other way is to exactly replicate the R file  --------------------------------------------------------------
    pop_union = unary_union(pop_center_gdf.geometry)  # Union all population centers into one geometry
    CBGs_outside_PCs = CBGs_with_PCs.copy()
    # CBGs_outside_PCs = study_CBGs[CBGs_with_PCs.intersects_w_pop_center==True].to_crs(32610)
    # if we use this which is the study CBGs with water, we can get exactly 1335 rows
    CBGs_outside_PCs["geometry"] = CBGs_outside_PCs.geometry.difference(pop_union)
    # Geometric difference: keep only the "outside" part
    # This line removes non polygons from geometrycollection entries
    CBGs_outside_PCs = CBGs_outside_PCs[~CBGs_outside_PCs.geometry.is_empty]  # this results in a similar map with 1333 rows.
    # if we use: WA_CBG_outside_PCs = study_CBGs[WA_SLD_study.intersects_w_pop_center==True].to_crs(32610)
    # which is the study CBGs with water, we can get exactly 1335 rows
    # if we get geometryCollection entries (which may contain lines) we remove those lines and only keep polygons
    mask = (
            CBGs_outside_PCs.geometry.type == 'GeometryCollection'
    )
    CBGs_outside_PCs.loc[mask, "geometry"] = (
        CBGs_outside_PCs.loc[mask, "geometry"].apply(_geomcollection_to_multipolygon)
    )
    WA_CBG_outside_PCs = CBGs_outside_PCs[~CBGs_outside_PCs.geometry.is_empty]
    # now let's keep everything as MultiPolygons
    _polygon_to_multipolygon(WA_CBG_outside_PCs)
    print(f'----\t {len(WA_CBG_outside_PCs)} census block groups intersect with population centers, but not fully '
          f'(Attention: there are still some CBGs that their land fully intersects with population centers but are'
          f'still counted here for their water portions)')

    return CBGs_outside_PCs, CBGs_with_PCs, CBGs_outside


def filter_CBGs_by_area_type(CBG_gdf, area_type_gdf):
    print(f'\n---- Filtering CBGs by their area type (city, suburban, town, rural)')
    # Ensure both GeoDataFrames use the same Coordinate Reference System (CRS)
    if CBG_gdf.crs != area_type_gdf.crs:
        area_type_gdf = area_type_gdf.to_crs(CBG_gdf.crs)
    # Fix any invalid geometries to prevent errors during intersection
    CBG_gdf.geometry = CBG_gdf.geometry.make_valid()
    area_type_gdf.geometry = area_type_gdf.geometry.make_valid()
    # Use simplify with a tolerance of 0 as an extra step to repair geometries
    area_type_gdf.geometry = area_type_gdf.geometry.simplify(tolerance=0)

    # R: sf::sf_use_s2(FALSE)
    # Note: This is not needed in Geopandas, which uses a planar geometry engine by default.
    intersection_gdf = gpd.overlay(CBG_gdf, area_type_gdf, how='intersection')
    intersection_gdf['area'] = intersection_gdf.geometry.area
    # Find the row with the largest area for each GEOID10
    # A common pandas method is to sort and drop duplicates.
    intersection_gdf = intersection_gdf.sort_values('area', ascending=False)
    largest_intersection_df = intersection_gdf.drop_duplicates(subset='GEOID10', keep='first')
    # We only need the key and the column to be merged ('GEOID10', 'LOCALE', and 'area' for the next step)
    # This mimics the creation of 'largest_intersection_df' in R.
    largest_intersection_df = largest_intersection_df[['GEOID10', 'LOCALE', 'area']].rename(
        columns={'area': 'max_area'})
    CBG_gdf = CBG_gdf.merge(
        largest_intersection_df,
        on='GEOID10',
        how='left'
    )
    CBG_gdf = CBG_gdf.drop(columns=['max_area'])
    print(f"Number of rows: {len(CBG_gdf)}")

    # Fixing missing LOCALEs
    CBG_gdf.geometry = CBG_gdf.geometry.make_valid()
    area_type_gdf.geometry = area_type_gdf.geometry.make_valid()
    area_type_gdf.geometry = area_type_gdf.geometry.simplify(tolerance=0)

    missing_locale_mask = CBG_gdf['LOCALE'].isna()
    cbgs_to_fix = CBG_gdf[missing_locale_mask]
    print(f'fixing missing LOCALE for GEOID10s:{cbgs_to_fix.GEOID10.to_list()}')

    if not cbgs_to_fix.empty:
        # `sjoin_nearest` does all the distance calculations, finds the minimum,
        # and joins the attributes in one efficient step.
        joined = gpd.sjoin_nearest(cbgs_to_fix, area_type_gdf, how="left")
        # Update the original GeoDataFrame using the results from the join.
        # The locale from the nearest 'area_type' polygon is in the 'LOCALE_right' column.
        CBG_gdf.loc[missing_locale_mask, 'LOCALE'] = joined['LOCALE_right'].values

    missing_locale_mask = CBG_gdf['GEOID10'].isna()
    print("\nChecking for any remaining missing locales:")
    if not missing_locale_mask.any():
        print("No missing locales found. ✅")
    else:
        print(missing_locale_mask)
    print(CBG_gdf['LOCALE'].value_counts().reset_index())
    return CBG_gdf


def add_income_to_CBGs(SLD_CBG_gdf):
    # LowWage_Category_Home
    median_low_wage_home = SLD_CBG_gdf["R_PCTLOWWAGE"].median(skipna=True)
    # Percentage of low-wage workers who live in these census tracts.

    # Create a new categorical column
    SLD_CBG_gdf["LowWage_Category_Home"] = np.where(SLD_CBG_gdf["R_PCTLOWWAGE"] > median_low_wage_home,
                                                    "Above Median", "Below Median"
                                                    )
    # LowWage_Category_Work
    median_low_wage_work = SLD_CBG_gdf["E_PctLowWage"].median(skipna=True)
    # Percentage of low-wage workers who work in these census tracts.
    SLD_CBG_gdf["LowWage_Category_Work"] = np.where(SLD_CBG_gdf["E_PctLowWage"] > median_low_wage_work,
                                                    "Above Median", "Below Median"
                                                    )
    SLD_CBG_gdf['LowWage_Combined_home_work'] = (SLD_CBG_gdf["LowWage_Category_Home"].astype(str) + "_" +
                                                 SLD_CBG_gdf["LowWage_Category_Work"].astype(str))
    SLD_CBG_gdf = SLD_CBG_gdf.to_crs(CRS)
    return SLD_CBG_gdf


def read_population_centers(database_path):
    '''
    This out layer assists WSDOT in prioritizing active transportation improvements in areas where people congregate
     and access destinations, and where travel distances between destinations align with typical distances travelled
     by users of pedestrian and bicycle modes. These areas are a priority because they serve the broadest range of users
    and potential users of the transportation system, including the very young, very old, and people with disabilities.
    :param database_path: address of the dataset
    :return: geo dataframe of pop centers
    '''
    print(f'\n---- Reading population centers from {database_path}')
    population_centers = gpd.read_file(database_path)
    population_centers = population_centers.to_crs(CRS)
    return population_centers


def read_area_type_data(nces_path):
    print(f'\n---- Reading area type data (EDGE Locale dataset) from {nces_path}')

    nces_0 = gpd.read_file(nces_path)
    nces_0 = nces_0.to_crs(CRS)
    area_type = nces_0.copy()
    area_type["LOCALE"] = area_type["LOCALE"].astype(int)
    # Define conditions
    conditions = [
        area_type["LOCALE"].isin([11, 12, 13]),
        area_type["LOCALE"].isin([21, 22, 23]),
        area_type["LOCALE"].isin([31, 32, 33]),
        area_type["LOCALE"].isin([41, 42, 43])
    ]
    # Define corresponding choices
    choices = ["City", "Suburban", "Town", "Rural"]
    # Apply np.select
    area_type["LOCALE"] = np.select(conditions, choices, default=nces_0["LOCALE"].astype(str))
    return area_type


def export_summary_statistics(CBG_gdf):
    result = {}
    for col in ["R_PCTLOWWAGE", "E_PctLowWage"]:
        summary = (
            CBG_gdf
            .groupby("LowWage_Combined_home_work", observed=True)[col]
            .apply(_custom_summary)
            .unstack(level=0)  # groups (Above/Below Median) become columns
        )
        result[col] = summary

    locale_summary = _categorical_summary(CBG_gdf, "LOCALE", "LowWage_Combined_home_work")

    descript_summary = pd.concat({**result, "LOCALE": locale_summary}, axis=0)
    return descript_summary


def save_files(save_dir, descript_summary, studyarea, CBG_outside_pc_gdf, CBG_outside_gdf, population_centers_study_area):
    print('\n ---- saving files:')
    path = os.path.join(save_dir,'descript_category_0.xlsx')
    descript_summary.to_excel(path)
    print(f"saved {path}")

    _save_geopackage(studyarea, save_dir, "studyarea.gpkg", driver="GPKG")
    print(f"saved study area data to studyarea.gpkg")


    path = os.path.join(save_dir, 'CBG_outside_PCs_data_0.xlsx')
    CBG_gdf_data_0 = CBG_outside_pc_gdf.drop(columns='geometry')
    CBG_gdf_data_0.to_excel(path, index=False)
    print(f"saved data to {path}")

    path = os.path.join(save_dir, 'CBG_outside_PCs_data_1.xlsx')
    CBG_outside_pc_data_1 = CBG_outside_pc_gdf[columns_to_keep]
    CBG_outside_pc_data_1.to_excel(path, index=False)
    print(f"saved subsetted data to CBG_outside_PCs_data_1.xlsx")

    _save_geopackage(population_centers_study_area, save_dir,
                     "POPULATION_CENTERS_STUDY_AREA.gpkg", driver="GPKG")
    _save_geopackage(CBG_outside_gdf, save_dir, "CBGs_NOT_INTERSECT_PCs.gpkg", driver='GPKG')
    _save_geopackage(CBG_outside_pc_gdf, save_dir, "CBGs_RIGHT_OUTSIDE_PCs.gpkg", driver='GPKG')
    # print('saved POPULATION_CENTERS_WA_AREA.gpkg, CBGs_NOT_INTERSECT_PCs.gpkg, CBGs_RIGHT_OUTSIDE_PCs.gpkg')




def preprocess(state_in, counties_in, sld_gdb_path, pop_ctr_path, nces_path, save_path=None):
    # studyarea, state_FIPS = gpd.read_file(os.path.join(save_path, 'temp.shp')), '53'
    studyarea, state_FIPS = get_study_area(state_in, counties_in)
    state_SLD_CBGs = get_smart_location_db(sld_gdb_path, state_FIPS)
    study_CBGs = filter_CBGs_by_area_and_columns(state_SLD_CBGs, studyarea)
    # _save_geopackage(study_CBGs, save_path, "study_area_CBGs_inital.gpkg", driver="GPKG") #todo move to save function
    study_CBGs = add_income_to_CBGs(study_CBGs)
    _save_geopackage(study_CBGs, save_path, "study_area_CBGs_INCOME.gpkg", driver="GPKG") #todo move to save function
    # a = study_CBGs['LowWage_Combined_home_work'].value_counts().reset_index() #debug
    population_centers = read_population_centers(pop_ctr_path)
    pop_centers_study_area = gpd.clip(population_centers, study_CBGs) # Unnessecary
    # population centers within the study area
    study_CBGs_outside_PCs, study_CBGs_with_PCs, study_CBGs_outside = (
        filter_CBGs_by_pop_center(study_CBGs, pop_centers_study_area)
    )
    area_type = read_area_type_data(nces_path)
    # now we find the area type of each CBG that intersects with population centers
    study_CBGs_outside_PCs = filter_CBGs_by_area_type(study_CBGs_outside_PCs, area_type)

    descript_summary = export_summary_statistics(study_CBGs_outside_PCs)
    if save_path:
        save_files(save_path, descript_summary, studyarea, study_CBGs_outside_PCs,
                   study_CBGs_outside, pop_centers_study_area)

    return studyarea, study_CBGs, study_CBGs_outside_PCs, study_CBGs_outside, study_CBGs_with_PCs, pop_centers_study_area



if __name__ == '__main__':
    state_in = 'WA'
    counties_in = ["King", "Pierce", "Snohomish", "Kitsap", "Skagit",
                   "Island", "Thurston", "Lewis", "Mason", "Whatcom",
                   "San Juan", "Clallam", "Jefferson", "Grays Harbor",
                   "Pacific", "Wahkiakum", "Cowlitz", "Clark", "Skamania"]
    # -------------
    sld_gdb_path = r"C:/Users/Soheil99/OneDrive - UW/0 Research/UW Tacoma/my copy - Satellite Communities Project/Data/SmartLocationDatabase.gdb"
    pop_ctr_path = r"C:/Users/Soheil99/OneDrive - UW/0 Research/UW Tacoma/my copy - Satellite Communities Project/Data/WSDOT_-_Population_Centers/WSDOT_-_Population_Centers.shp"
    nces_WA_path = r"C:/Users/Soheil99/OneDrive - UW/0 Research/UW Tacoma/my copy - Satellite Communities Project/Data/edge_locale24_nces_WA"
    POI_path = r"C:/Users/Soheil99/OneDrive - UW/0 Research/UW Tacoma/my copy - Satellite Communities Project/Data/POI Data/WA_Study_Area.geojson"
    save_path = r"C:\Users\Soheil99\OneDrive - UW\0 Research\UW Tacoma\my copy - Satellite Communities Project\Analysis\RuralATGapFinder\out"

    # sld_gdb_path = r"/Users/soheil/Library/CloudStorage/OneDrive-UW/0 Research/UW Tacoma/my copy - Satellite Communities Project/Data/SmartLocationDatabase.gdb"
    # pop_ctr_path = r"/Users/soheil/Library/CloudStorage/OneDrive-UW/0 Research/UW Tacoma/my copy - Satellite Communities Project/Data/WSDOT_-_Population_Centers/WSDOT_-_Population_Centers.shp"
    # nces_WA_path = r"/Users/soheil/Library/CloudStorage/OneDrive-UW/0 Research/UW Tacoma/my copy - Satellite Communities Project/Data/edge_locale24_nces_WA"
    # save_path = r"/Users/soheil/Library/CloudStorage/OneDrive-UW/0 Research\UW Tacoma\my copy - Satellite Communities Project\Analysis\RuralATGapFinder\out"
    preprocess(state_in, counties_in, sld_gdb_path, pop_ctr_path, nces_WA_path, save_path=save_path)


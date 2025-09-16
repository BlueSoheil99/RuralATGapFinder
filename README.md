# RuralATGapFinder
A tool to analyze and visualize active transportation disparity for rural residential communities in Washington state

## environment setup
``conda activate "C:\Users\Soheil99\AppData\Local\Programs\ArcGIS\Pro\bin\Python\envs\arcgispro-py3"
``

clone an environment from 'package manager' in arcgis
``conda activate arcgispro-cloned
``
```angular2html
conda activate arcgispro-cloned
conda install geopandas 
pip install pygris
```

## how to use the code
- open arcgis pro
- activate environemnt
- add new tools 
- ...

### data preparation:
- SLD 
- population centers
- POI data (geojson)
- 

## some notes:

be mindful of crs conversions in the notebook file

some CBGs after filtering steps only have water. somehow we should remove them

in filter_CBGs_by_area_and_columns function, the line `
    study_CBGs = gpd.clip(study_CBGs, studyarea_gdf)` results in a removing more water area. If we remove this line,
results will be identical with the R file
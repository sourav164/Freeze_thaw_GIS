import pandas as pd
import math
import warnings
import shapely
import geopandas
from shapely.geometry import Point
import numpy

warnings.filterwarnings('ignore')

inputs = pd.read_csv("Inputs.csv")
inputs["Rain_Duration"] = numpy.nan
inputs["Rain_Intensity"] = numpy.nan
inputs["Saturation"] = numpy.nan
inputs["MR"] = numpy.nan

weather  = pd.read_excel("Weather_2020_MnROAD.xlsx")
inputs["date"] = pd.to_datetime(inputs["date"])

#fixed value 
a = -0.3123
b = 0.3
km = 6.8157


def saturation_cal(cell_no, rain_int, rain_dur, hydrlic_conduc=None):
    if cell_no==188:
        saturation = 22.31+2.70*rain_int+3.31*rain_dur
    
    elif cell_no==189:
        saturation = 20.65+3.61*rain_int+3.15*rain_dur
    
    elif cell_no==127:
        saturation = 18.97+3.27*rain_int+2.71*rain_dur
    
    else:
        if isinstance(hydrlic_conduc, (int, float)): 
            saturation = 21.63+3.60*rain_int+2.83*rain_dur-0.34*hydrlic_conduc
        else:
            raise Exception("Provide correct hydraulic conductivity value")            
    return saturation/100


# calculation starts

for index, row in inputs.iterrows():
    cell_no = int(row["Cell No/identifier"])
    date = row["date"]
    SOPT = row["SOPT"]
    MROPT = row["MROPT"]
    hydrlic_conduc = row["hydrlic_conduc"]
    
    
    #weather information extracts here
    day_weather = weather.loc[weather["DAY"]  == date]
    
    # print (weather.loc[weather["DAY"] == inputs["date"][0]]) #see day weather
    rain_dur = (day_weather['PRECIP_100TH_INCH'] != 0).sum()/4
    
    if rain_dur == 0:
        rain_int = 0 # no rainfall, 0 intensity
    else:
        rain_int = day_weather['PRECIP_100TH_INCH'].sum()/rain_dur
    
    
    #saturation and MR calculation
    saturation = saturation_cal(cell_no, rain_int, rain_dur, hydrlic_conduc=hydrlic_conduc)    
    
    right_side= a+(b-a)/(1+math.exp(math.log10(-b/a)+km*(saturation-SOPT)))
    MR = MROPT*math.pow(10, right_side)
       
    inputs["Saturation"][index] = round(saturation, 5)
    inputs["MR"][index] = round(MR, 2)
    inputs["Rain_Duration"][index] = rain_dur
    inputs["Rain_Intensity"][index] = rain_int
    
    #print (cell_no,rain_int, rain_dur,  saturation, right_side, round(MR, 2) )
print (inputs)


# shapefile creation
# combine lat and lon column to a shapely Point() object
inputs["date"] = inputs["date"].dt.strftime('%m-%d-%Y')
inputs['geometry'] = inputs.apply(lambda x: Point((float(x.Longitude), float(x.Latitude))), axis=1)
inputs_geo = geopandas.GeoDataFrame(inputs, geometry='geometry')
inputs.to_csv("output.csv")
inputs_geo.crs= "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
inputs_geo.to_file('MyGeometries.shp', driver='ESRI Shapefile')
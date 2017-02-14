#building off of calc/contracts/management/commands
import os
import logging
import asyncio
import pandas as pd
import math
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.core.management import BaseCommand
from optparse import make_option
from django.core.management import call_command
import statistics as st
import numpy as np
from price_prediction.models import LaborCategory, OverallSpread
import plotly
from plotly.graph_objs import Bar,Layout,Scatter, Box, Annotation,Marker,Font,XAxis,YAxis 
import shutil
from scipy import stats

def bar_plot(data,filename):
    filename = "/Users/ericschles/Documents/projects/calc/price_prediction/"+filename
    x_vals = [elem[0] for elem in  data]
    y_vals = [elem[1] for elem in data]
        
    plotly.offline.plot({
        "data":[Bar(x=x_vals,y=y_vals)],
        "layout":Layout(
            title=filename.split(".")[0]
        )
    },auto_open=False)
    shutil.move("temp-plot.html",filename)

#write tests for this -

# make sure each of these functions performs appropriately
# - smoke test
# - (minimal) doc tests
# - edge cases
# - check to make sure data is saved to the database

def is_nan(obj):
    if type(obj) == type(float()):
        return math.isnan(obj)
    else:
        return False


def count_outliers(data):
    outliers_num = 0
    mean = st.mean(data)
    stdev = st.stdev(data)
    for elem in data:
        if (elem > mean + (2*stdev)) or (elem < mean - (2*stdev)):
            outliers_num += 1
    return outliers_num


def first_quartile(List):
    if len(List) >= 4:
        List.sort()
        if len(List) % 2 != 0:
            middle_number = st.median(List)
            return st.median(List[:List.index(middle_number)])
        else:
            middle_index = len(List)//2
            middle_number = List[middle_index]
            return st.median(List[:List.index(middle_number)])
    else:
        return None    

#Question 9
#Write a python function implementing a function that returns the first quantile of a set of numbers
def third_quartile(List):
    if len(List) >= 4:
        List.sort()
        if len(List) % 2 != 0:
            middle_number = st.median(List)
            return st.median(List[List.index(middle_number):])
        else:
            middle_index = len(List)//2
            middle_number = List[middle_index]
            return st.median(List[List.index(middle_number):])
    else:
        return None    

def quartile_analysis(data):
    if len(data) < 5:
        return None
    q1 = first_quartile(data)
    q3 = third_quartile(data)
    median = st.median(data)
    if abs(median - q1) > abs(median - q3):
        return abs(median - q1)
    else:
        return abs(median - q3)

def big_picture_analysis(labor_data):
    categories = set([elem.labor_category for elem in labor_data])
    central_tendency = []
    spread = []
    outliers = []
    iqrs = []
    for category in categories:
        data = LaborCategory.objects.filter(labor_category=category).all()
        prices = [round(float(elem.price),2) for elem in data]
        if len(prices) > 5 and stats.normaltest(prices).pvalue > 0.05:
            spread.append([category, st.stdev(prices)])
            central_tendency.append([category, st.mean(prices)])
        else:
            spread.append([category, quartile_analysis(prices)])
            central_tendency.append([category, st.median(prices)])
        outliers.append([category, count_outliers(prices)])
    bar_plot(central_tendency,"center.html")
    bar_plot(spread,"spread.html")
    bar_plot(outliers,"outlier_count.html")
    print("central tendency",st.median([elem[1] for elem in  central_tendency]))
    print("spread",st.median([elem[1] for elem in spread]))
    print("outliers",st.median([elem[1] for elem in outliers]))

def plot_all_timeseries(data,years,categories):
    for_scatter = []
    for category in categories:
        x_vals = years
        y_vals = [data[category][year] for year in years]
        for_scatter.append(Scatter(x=x_vals,y=y_vals,name=category))
    plotly.offline.plot({
        "data":for_scatter,
        "layout":Layout(
            title="Time Series analysis of all categories"
        )
    },auto_open=False)
    shutil.move("temp-plot.html","/Users/ericschles/Documents/projects/calc/price_prediction/viz/all_categories.html")

def plot_individual_timeseries(data,years,category):
    x_vals = []
    y_vals = []
    for year in years:
        try:
            y_vals.append(data[year])
            x_vals.append(year)
        except:
            continue
    plotly.offline.plot({
        "data":[Scatter(x=x_vals,y=y_vals)],
        "layout":Layout(
            title=category
        )
    },auto_open=False)
    category = category.replace("/","_").replace(",","_")
    
    category = "_".join(category.lower().split())
    if len(category) > 40:
        category = category.split("_")[0]
    shutil.move("temp-plot.html","/Users/ericschles/Documents/projects/calc/price_prediction/viz/"+category+".html")

def min_max(data):
    data.sort()
    return abs(data[-1] - data[0])


async def main(category, years): 
    data = LaborCategory.objects.filter(labor_category=category).all()
    for year in years:
        prices = [round(float(elem.price),2) for elem in data if elem.date.year==year]
        if len(prices) > 8 and stats.normaltest(prices).pvalue > 0.05:
            spread = OverallSpread(labor_category=category, year=year, spread=st.stdev(prices))
            spread.save()
        elif len(prices) > 5:
            try:
                if not is_nan(quartile_analysis(prices)):
                    spread = OverallSpread(labor_category=category, year=year, spread=quartile_analysis(prices))
                    spread.save()
                else:
                    spread = OverallSpread(labor_category=category, year=year, spread=min_max(prices))
                    spread.save()
            except:
                spread = OverallSpread(labor_category=category, year=year, spread=min_max(prices))
                spread.save()
        elif len(prices) >= 2:
            spread = OverallSpread(labor_category=category, year=year, spread=min_max(prices))
            spread.save()
        else:
            continue
     

class Command(BaseCommand):
    #do year over year analysis
    def handle(self, *args, **options):
        OverallSpread.objects.all().delete()
        labor_data = LaborCategory.objects.all()
        categories = set([elem.labor_category for elem in labor_data])
        years = list(set([float(elem.date.year) for elem in labor_data]))
        years.sort()
        overall_spread = {}.fromkeys(categories,{}.fromkeys(years,0))

        loop = asyncio.get_event_loop()
        for category in categories:
            loop.run_until_complete(main(category, years))
        loop.close()
        
        

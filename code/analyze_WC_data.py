#!/usr/bin/env python

# Imports for parsing WC players data from PDFs
import io
import sys
import PyPDF2
import re
from datetime import datetime, timedelta
from random import random
import time
from time import localtime, strftime
from time import sleep

# Imports for using Selenium to do the automatic entrance
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Imports for writing out to csv file
import os
import glob
import unicodecsv as csv

# The dates have the pattern of "MM.DD.YYYY"
DATE_PATTERN = '\d{2}\.\d{2}\.\d{4}'
# The dates have the pattern of "15 Jul 1981"
ALPHA_NUM_DATE_PATTERN = '\d{2}\s+\w{3}\s+\d{4}'
# The keyword to find the end of column headers (Height and Weight)
HEIGHT_WEIGHT = 'Height Weight'
COUNTRY_PATTERN = '(\D+)'
HEIGHT_WEIGHT_PATTERN = '(\d{3}\s\d{2,3}\s)'
PDF_FILE_SUFFIX = '.pdf'
# Lookup table to convert three-letter month into MM format. 
MONTH_LOOKUP = {'Jan': '01', 'Feb':'02', 'Mar':'03', 'Apr':'04', 'May':'05', 'Jun':'06', 'Jul':'07', 'Aug':'08', 'Sep':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'}
CSV_FILE_NAME ='World_Cup_Players_Data.csv'

#############################################################
# Return the position after the search keyword.             #
#############################################################
def get_end_position(full_string, keyword):
    return full_string.find(keyword) + len(keyword)

#############################################################
# Add an expense item to expense_items dictionary           #
# expense_date_string is converted to DateTime object for   #
# sorting purpose.                                          #
#############################################################
def add_value_to_expenses(category, expense_date_string, expense_amount):
    expense_date = datetime.strptime(expense_date_string, '%m/%d/%Y')
    # Parse expense to a float number, and we know that a refund will have '-' appended at the end. 
    if expense_amount.find('-')>-1:
        expense_amount = -1 * float(expense_amount.replace('-', ''))
    else:
        expense_amount = float(expense_amount)

    # Add expense item based on category and expense date with expense $ amounts stored in a list.
    if len(expense_items[category])==0 or not (expense_date in expense_items[category]):
        expense_items[category][expense_date] = [expense_amount]
    else:
        expense_items[category][expense_date] = expense_items[category][expense_date] + [expense_amount]

#############################################################
# Determine whether the data is for 2018 WC which has       #
# different layout from other years.                        #
#############################################################
def is_18(file_name):
    return file_name.find('2018')>-1

#############################################################
# Calculate players' ages and zodiac signs according to     #
# their birthdays on file.                                  #
#############################################################
def calculate_age_and_zodiac(wc_year, dob_string):
    dob_date = datetime.strptime(dob_string, '%d.%m.%Y')
    age = wc_year - dob_date.year

    if ((dob_date.month==12 and dob_date.day >= 22) or (dob_date.month==1 and dob_date.day <= 19)):
        zodiac_sign = "Capricorn"
    elif ((dob_date.month==1 and dob_date.day >= 20) or (dob_date.month==2 and dob_date.day <= 17)):
        zodiac_sign = "aquarium"
    elif ((dob_date.month==2 and dob_date.day >= 18) or (dob_date.month==3 and dob_date.day <= 19)):
        zodiac_sign = "Pices"
    elif ((dob_date.month==3 and dob_date.day >= 20) or (dob_date.month==4 and dob_date.day <= 19)):
        zodiac_sign = "Aries"
    elif ((dob_date.month==4 and dob_date.day >= 20) or (dob_date.month==5 and dob_date.day <= 20)):
        zodiac_sign = "Taurus"
    elif ((dob_date.month==5 and dob_date.day >= 21) or (dob_date.month==6 and dob_date.day <= 20)):
        zodiac_sign = "Gemini"
    elif ((dob_date.month==6 and dob_date.day >= 21) or (dob_date.month==7 and dob_date.day <= 22)):
        zodiac_sign = "Cancer"
    elif ((dob_date.month==7 and dob_date.day >= 23) or (dob_date.month==8 and dob_date.day <= 22)): 
        zodiac_sign = "Leo"
    elif ((dob_date.month==8 and dob_date.day >= 23) or (dob_date.month==9 and dob_date.day <= 22)): 
        zodiac_sign = "Virgo"
    elif ((dob_date.month==9 and dob_date.day >= 23) or (dob_date.month==10 and dob_date.day <= 22)):
        zodiac_sign = "Libra"
    elif ((dob_date.month==10 and dob_date.day >= 23) or (dob_date.month==11 and dob_date.day <= 21)): 
        zodiac_sign = "Scorpio"
    elif ((dob_date.month==11 and dob_date.day >= 22) or (dob_date.month==12 and dob_date.day <= 21)):
        zodiac_sign = "Sagittarius"

    return str(age), zodiac_sign

#############################################################
# Parse the players data on each page for 2018 data         #
#############################################################
def parse_PDF_page(writer, page_i):
    # Remove the header row
    rows = page_i[page_i.find(HEIGHT_WEIGHT)+len(HEIGHT_WEIGHT):]
    country_name = re.search(COUNTRY_PATTERN, rows).group(0).strip()
    while (re.search(country_name, rows) is not None):
        dob = re.search(DATE_PATTERN, rows).group(0).strip()
        height_weight = re.search(HEIGHT_WEIGHT_PATTERN, rows).group(0).strip()
        age, zodiac_sign = calculate_age_and_zodiac(2018, dob)
        writer.writerow(['2018', country_name, dob, height_weight.split(' ')[0], age, zodiac_sign, height_weight.split(' ')[1]])
        rows = rows[rows.find(height_weight)+len(height_weight):]

#############################################################
# Parse the players data from txt file generated from PDF   #
#############################################################
def parse_txt_file(file_name):
    wc_year = int(file_name[0:4])
    with open(CSV_FILE_NAME, 'a') as f:
        writer = csv.writer(f)
        tf = open(file_name, 'r')
        found_line_of_players = False
        dobs = []
        heights = []
        for line in tf:
            line = line.strip()
            if line == 'List of Players':
                # We are getting data for a new country so we need to clean the slate
                found_line_of_players = True
                if len(dobs) != len(heights):
                    print "Problem with the country of: " + country_name
                    print dobs, heights
                else:
                    for idx, dob in enumerate(dobs):
                        age, zodiac_sign = calculate_age_and_zodiac(wc_year, dob)
                        writer.writerow([wc_year, country_name, dob, heights[idx], age, zodiac_sign])
                dobs = []
                heights = []
            elif found_line_of_players:
                if (line != ''):
                    country_name = line
                    found_line_of_players = False
            else:
                if re.search(DATE_PATTERN, line) is not None: 
                    dobs.append(re.search(DATE_PATTERN, line).group(0))
                elif re.search(ALPHA_NUM_DATE_PATTERN, line) is not None: 
                    dob = re.search(ALPHA_NUM_DATE_PATTERN, line).group(0)
                    day = dob[0:2]
                    month = MONTH_LOOKUP[dob[3:6]]
                    year = '19' + dob[-2:]
                    dobs.append(day + '.' + month + '.' + year)
                elif line.isdigit() and int(line) > 155 and int(line) <210:
                    heights.append(int(line))

###############################################################
# Use PdfFileReader to parse each page for WC players data.   #
###############################################################
def parse_pdf(data_file):
    if not data_file.lower().endswith(PDF_FILE_SUFFIX):
        raise Exception("Input file must be in PDF format!")

    if is_18(data_file):
        prf = PyPDF2.PdfFileReader(open(data_file, "rb"))
        with open(CSV_FILE_NAME, 'a') as f:
            writer = csv.writer(f)
            for i in range(prf.getNumPages()):
                page_i = re.sub(r'\s+', ' ', prf.getPage(i).extractText().replace('\n', ' '))
                parse_PDF_page(writer, page_i)
    else:
        # Convert pdf files to txt files because they cannot be ready by PyPDF2.PdfFileReader
        file_name = data_file.lower().replace('.pdf', '.txt')
        os.popen('pdftotext ' + data_file + ' ' + file_name)
        parse_txt_file(file_name)

if __name__ == '__main__':
    try:
        # Uncomment to process PDF files containing players data
        # if os.path.isfile(CSV_FILE_NAME):
        #     os.remove(CSV_FILE_NAME)
        # for pdf_file in glob.glob(sys.argv[1]):
        #     parse_pdf(pdf_file)
        print "placeholder"        
    except Exception, e:
        print e
        print "Please call the module in the format of \"python analyze_WC_data.py \'2*WC.pdf\'\""

import click
import pandas as pd
import sqlite3
import requests

#BeautifulSoup is a library that helps parse HTML web pages and XML files
from bs4 import BeautifulSoup 

#

display = print

def DailySR_read(f):
    return pd.ExcelFile(f)

def DailySR_parse(xl,sheet,skiprows=13,header=None):
    #In the spreadsheet, there are two types of sheet that differ in header treatment
    xlclass={'A&E closures':0,
             'A&E diverts':0,
             'G&A beds':1,
             'Beds Occ by long stay patients':1,
             'D&V, Norovirus':1,
             'Adult critical care':1,
             'Paediatric intensive care':1,
             'Neonatal intensive care ':1,
             'Ambulance Arrivals and Delays':1,#,
             #'Macro1':-1
             }
    if sheet not in xlclass: return pd.DataFrame()
    
    dfx=xl.parse(sheet,skiprows=skiprows,header=header)
    dfx.dropna(how='all',inplace=True)
    dfx.dropna(how='all',axis=1,inplace=True)
    cols=[]
    
    #Drop England row and possible blank row if it hasn't been dropped already
    dfx.drop([2,3],inplace=True, errors='ignore')
    
    if xlclass[sheet]==0:
        dfx.dropna(how='all',axis=1,inplace=True)
        dfx.columns=dfx.iloc[0].values
        dfx=dfx[1:]
        #Transpose rows and columns
        dfx=dfx.T
        #Set the column names
        dfx.columns=pd.MultiIndex.from_arrays(dfx[:3].values, names=['Area','Code','Name']) 
        #And then throw away the metadata rows used to create columns headers
        dfx=dfx[3:]
        #Cast cols to numeric
        dfx = dfx.apply(pd.to_numeric, errors='ignore')
        dfx = pd.melt(dfx.reset_index(),id_vars=['index'])
        dfx['value'] = pd.to_numeric(dfx['value'],errors='coerce')
        dfx.columns = ['Date']+dfx.columns[1:].tolist()
        dfx['Category']=sheet
        dfx['Report']=sheet
    elif xlclass[sheet]==1:
        #This is a real hack, trying to think what a sensible shape is and how to get there
        dfx.dropna(how='all',axis=0,inplace=True)
        #Get rid of empty columns
        dfx.dropna(how='all',axis=1,inplace=True)
        #Fill across on dates
        dfx.iloc[0] = dfx.iloc[0].fillna(method='ffill')
        #Patch the leading empty columns
        dfx.loc[:1] = dfx.loc[:1].fillna('Metadata')
        #Generate a multi-index across the columns from the first two rows
        ##TO DO
        #Some of the dates are dates (weekdays) and correctly get parsed as dates
        #Others are periods (over a weekend) and need handling somehow
        #May be best to convert them to dates corresponding to last date in period?
        #  Then perhaps also build a small helper that searches on a date and 
        #  if it falls into weekend period, rewrite it as the last date in the period?
        dfx.columns=pd.MultiIndex.from_arrays(dfx.iloc[:2].values, names=['Date','Category'])
        #Drop the rows we used to make the multi-index
        dfx=dfx[2:]
        #Transpose rows and columns
        dfx=dfx.T
        #Set the column names
        dfx.columns=pd.MultiIndex.from_arrays(dfx[:3].values, names=['Area','Code','Name'])
        #And then throw away the metadata rows used to create columns headers
        dfx=dfx[3:]
        #Tidy up by throwing away any empty columns we created
        dfx.dropna(how='all',axis=1,inplace=True)
        dfx = pd.melt(dfx.reset_index(),id_vars=['Date','Category'])
        #Cast value to numeric
        dfx['value'] = pd.to_numeric(dfx['value'],errors='coerce')
        dfx['Report']=sheet
    return dfx
    

def dailySR_NHS111_parse(xl,sheet,skiprows=12,header=None):
    dfx=xl.parse(sheet,skiprows=skiprows,header=header)
    dfx.dropna(how='all',inplace=True)
    dfx.dropna(how='all',axis=1,inplace=True)
    dfx.iloc[:2]=dfx.iloc[:2].fillna(method='ffill',axis='index')
    dfx.iloc[:1]=dfx.iloc[:1].fillna(method='ffill',axis='columns')
    dfx.columns=pd.MultiIndex.from_arrays(dfx.iloc[:2].values, names=['Category', 'Date'])
    dfx.drop([0,1,2],inplace=True)
    dfx['Report'] = sheet
    dfx.set_index([('Region','Region'),('Code','Code'),
                   ('NHS 111 area name','NHS 111 area name'), 'Report'],inplace=True)
    dfx = dfx.T.reset_index()
    dfx = dfx.melt(id_vars=['Category','Date'])
    dfx.rename(columns={('Region', 'Region'): 'Region',
                       ('Code', 'Code'):'Code',
                       ('NHS 111 area name', 'NHS 111 area name'):'NHS 111 area name'}, inplace=True)
    
    dfx['value'] = pd.to_numeric(dfx['value'],errors='coerce')
    return dfx
    
def get_report(xl,sheet):
    return DailySR_parse(xl,sheet)
    

def sqlise_sitrep(url, conn, table):
	try:
		xl=DailySR_read(url)
		reports = [n for n in  xl.sheet_names if n !='Macro1']

		df= pd.DataFrame()
		for reportname in reports:
			report = get_report(xl,reportname)
			report.to_sql(table, conn, index=False, if_exists='append')
	except: pass

def sqlise_sitrep_nhs111(url, conn, table):
	try:
		xl=DailySR_read(url)
		reports = [n for n in  xl.sheet_names]
		df= pd.DataFrame()
		for reportname in reports:
			report =  dailySR_NHS111_parse(xl,reportname)
			report.to_sql(table, conn, index=False, if_exists='append')
	except: pass

def droptable(conn,table):
	cursor = conn.cursor()
	cursor.execute('''DROP TABLE IF EXISTS {}'''.format(table))
	conn.commit()

def _getLinksFromPage(url):
    
    page = requests.get(url)

    #The file we have grabbed in this case is a web page - that is, an HTML file
    #We can get the content of the page and parse it
    soup=BeautifulSoup(page.content, "html5lib")
    #BeautifulSoup has a routine - find_all() - that will find all the HTML tags of a particular sort
    #Links are represented in HTML pages in the form <a href="http//example.com/page.html">link text</a>
    #Grab all the <a> (anchor) tags...
    souplinks=soup.find_all('a')
    #links=[link.get('href') for link in souplinks]
    return souplinks
    
def links_winter_sitrep_2017_18(url='https://www.england.nhs.uk/statistics/statistical-work-areas/winter-daily-sitreps/winter-daily-sitrep-2017-18-data/'):
    return _getLinksFromPage(url)

def get_url_winter_sitrep_2017_18(typ, links=None):
	if links is None:
		links = links_winter_sitrep_2017_18()
	
	filetype='xlsx'
	reps = {'winter_sitrep':'Acute Time series', 'winter_sitrep_nhs111':'NHS111 Time series'}
	if typ not in reps: 
		display("I don't recognise that type: {}".format(typ))
		return None, None
	
	for link in links:
		if link['href'].endswith('.{filetype}'.format(filetype=filetype)):
			if 'Winter SitRep'.lower() in link.text.lower() and reps[typ].lower() in link.text.lower():
				display('Grabbing data for {}'.format(link.text))
				return(link.text, link['href'])
	return None, None
                
@click.command()
@click.option('--dbname', default='nhs_sitrepdb.db',  help='SQLite database name')
@click.option('--sitrepurl', default=None, help='Winter sitrep URL')
@click.option('--sitreptable',default='sitrep', help='Winter sitrep db table name')
@click.option('--sitrep111url', default=None, help='NHS111 Winter sitrep URL')
@click.option('--sitrep111table',default='nhs111', help='Winter sitrep db table name')
@click.argument('command')	
def cli(dbname, sitrepurl, sitreptable, sitrep111url, sitrep111table, command):
	display = click.echo
	conn = sqlite3.connect(dbname)
	display('Using SQLite3 database: {}'.format(dbname))
	if command == 'collect':
		links = links_winter_sitrep_2017_18()
		if sitrepurl is None:
			linktext,sitrepurl = get_url_winter_sitrep_2017_18('winter_sitrep', links)
		if sitrep111url is None:
			linktext,sitrep111url = get_url_winter_sitrep_2017_18('winter_sitrep_nhs111', links)
			
		if sitrepurl is not None:
			droptable(conn,sitreptable)
			sqlise_sitrep(sitrepurl, conn, sitreptable)
		if sitrep111url is not None:
			droptable(conn,sitrep111table)
			sqlise_sitrep_nhs111(sitrep111url, conn, sitrep111table)
	


from flask import Flask, render_template
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import mechanize
import json

app = Flask(__name__)
timeDeltaDays = 7

def filterRows(row):
    today = datetime.now()
    return row['agenda'] and row['date'] and ((today - timedelta(days=timeDeltaDays)) <= row['date'])

def TryCatchStrpTime(dateString):
    date = ''
    try:
        date = datetime.strptime(dateString, '%b %d, %Y')
    except:
        try:
            date = datetime.strptime(dateString, '%B %d, %Y')
        except:
            return None
    return date

outputDateFormat = '%B %d, %Y'


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/davidson")
def davidson():
    source = requests.get('https://nashville.legistar.com/Calendar.aspx').text
    soup = BeautifulSoup(source, 'html.parser')
    def davidson_rows(css_class):
        return css_class == "rgRow" or css_class == "rgAltRow"
    rows = soup.find_all('tr', class_=davidson_rows)
    def createRowObject(row):
        tds = row.find_all('td')
        name = tds[0].text
        dateString = "{} {}".format(tds[1].text, tds[3].text.replace("\n", ""))
        dateFormat = '%m/%d/%Y %I:%M %p'
        date = datetime.strptime(dateString, dateFormat)
        agenda = tds[7].find('a').get('href')
        return {"name": name, "date": date, "dateString": date.strftime(dateFormat), "agenda": agenda}
    
    agendaList = filter(filterRows, map(createRowObject, rows))
    return render_template('davidson.html', agendaList=agendaList)

@app.route("/murfreesboro")
def murfreesboro():
    source = requests.get('https://www.murfreesborotn.gov/agendacenter').text
    soup = BeautifulSoup(source, 'html.parser')
    def murfreesboro_rows(css_class):
        return css_class == "catAgendaRow"
    rows = soup.find_all('tr', class_=murfreesboro_rows)
    def createRowObject(row):
        tds = row.find_all('td')
        name = tds[0].p.text
        dateString = tds[0].h4.strong.text
        dateFormat = '%b %d, %Y'
        date = datetime.strptime(dateString, dateFormat)
        agenda = tds[-1].find('a', class_="pdf").get('href')
        council = row.find_parent('div').h2.text[1:]
        return {"name": name, "date": date, "dateString": date.strftime(dateFormat), "agenda": agenda, "council": council}
    agendaList = filter(filterRows, map(createRowObject, rows))
    return render_template('murfreesboro.html', agendaList=agendaList)

@app.route("/williamson")
def williamson():
    source = requests.get('https://www.williamsoncounty-tn.gov/AgendaCenter').text
    soup = BeautifulSoup(source, 'html.parser')
    def murfreesboro_rows(css_class):
        return css_class == "catAgendaRow"
    rows = soup.find_all('tr', class_=murfreesboro_rows)
    def createRowObject(row):
        tds = row.find_all('td')
        name = tds[0].p.text
        dateString = tds[0].h4.strong.text
        dateFormat = '%b %d, %Y'
        date = datetime.strptime(dateString, dateFormat)
        agenda = tds[-1].find('a', class_="pdf").get('href')
        council = row.find_parent('div').h2.text[1:]
        return {"name": name, "date": date, "dateString": date.strftime(dateFormat), "agenda": agenda, "council": council}
    agendaList = filter(filterRows, map(createRowObject, rows))
    return render_template('williamson.html', agendaList=agendaList)

@app.route("/williamson_schools")
def williamson_schools():
    source = requests.get('https://meeting.boeconnect.net/Public/Organization/566').text
    soup = BeautifulSoup(source, 'html.parser')
    rows = soup.find_all('tr', class_=lambda classes: "header" not in classes)
    def createRowObject(row):
        title = row.td.div.text.split(' - ')
        name = title[1]
        dateString = title[0].replace(' at', '').strip()
        dateFormat = '%B %d, %Y %I:%M %p'
        date = datetime.strptime(dateString, dateFormat)
        link = row.find_all('td')[-1].find('a')['href']
        return {"name": name, "date": date, "dateString": dateString, "agenda": link}
    agendaList = filter(filterRows, map(createRowObject, rows))
    return render_template('williamson_schools.html', agendaList=agendaList)

@app.route("/rutherford_schools")
def rutherford_schools():
    source = requests.get('https://www.rcschools.net/apps/pages/index.jsp?uREC_ID=523332&type=d&pREC_ID=2400524').text
    soup = BeautifulSoup(source, 'html.parser')
    sections = soup.find_all('ul', class_="attachment-list-public")
    agendas = sections[0].find_all('a', class_='attachment-type-pdf')
    minutes = sections[1].find_all('a', class_='attachment-type-pdf')
    def createRowObject(row, isMinutes=False):
        title = row.text.split('-')
        name = title[1 if isMinutes else 0].strip()
        dateString = title[0 if isMinutes else 1].strip()
        dateFormat = '%b %d, %Y'
        date = TryCatchStrpTime(dateString)
        href = row['href']
        return {"name": name, "date": date, "dateString": dateString, "agenda": href, "isMinutes": isMinutes}
    agendaList = filter(filterRows, list(map(createRowObject, agendas)) + list(map(lambda row: createRowObject(row, True), minutes)))
    return render_template('rutherford_schools.html', agendaList=agendaList)

@app.route("/maury")
def maury():
    dateFormat = '%Y-%m-%dT%H:%M:%S'
    returnedDateFormat = '%Y-%m-%d %H:%M:%S'
    outputDateFormat = '%m/%d/%Y %I:%M %p'
    today = datetime.now()
    start = (today - timedelta(days=timeDeltaDays))
    requestString = ''
    groups = requests.get('https://playapi.champds.com/maurycotn/archive/1').json()['ArchiveGroups']
    overallResponse = []
    for group in groups:
        requestString = 'https://playapi.champds.com/maurycotn/archiveGroupDate/{}/LOCAL/{}/{}'.format(group['CustomerArchiveGroupID'], start.strftime(dateFormat), today.strftime(dateFormat))
        groupResponse = requests.get(requestString).json()
        def createRowObject(row):    
            date = row['EventDateTimeLocal']
            name = row['EventTitle']
            eventId = row['CustomerEventID']
            council = group['GroupName']
            return {"name": name, "dateString": date, "eventId": eventId, "council": council}
        overallResponse += list(map(createRowObject, groupResponse))
    return render_template('maury.html', agendaList=overallResponse)





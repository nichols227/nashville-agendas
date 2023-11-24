from flask import Flask, render_template
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

def filterRows(row):
        today = datetime.now()
        return row['agenda'] and ((today - timedelta(days=7)) <= row['date'] <= today)

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

#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time
import multiprocessing
from multiprocessing.managers import BaseManager
import json
import sqlite3
from datetime import datetime, date, time
import settings
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.gen
from tornado.options import define, options
import tornado.web as web
import npbc_communication
import setBoilerTemperature
import SetModeAndPriority
from  tornado.escape import json_decode
from  tornado.escape import json_encode


define("port", default=settings.WEB_UI_PORT, help="run on the given port", type=int)

# TODO: fix this, the security of this is F-ed
# class BaseHandler(tornado.web.RequestHandler):
#     def get_current_user(self):
#         return self.get_secure_cookie("user")
#
# class MainHandler(BaseHandler):
#     def get(self):
#         # if not self.current_user:
#         #     self.render('indexGuest.html')
#         # else:
#         #     self.render('index.html')
#         self.render('index.html')
#
# class LoginHandler(BaseHandler):
#     def get(self):
#         self.write('<html><body><form action="/login" method="post">'
#                    'Name: <input type="text" name="name">'
#                    'Password: <input type="password" name="password">'
#                    '<input type="submit" value="Sign in">'
#                    '</form></body></html>')
#
#     def post(self):
#         # TODO: salt and hash the password before storing in the DB, then salt
#         # and hash the user's input password before comparing.
#         username = self.get_argument("name")
#         password = self.get_argument("password")
#         doc = True #Implement login
#         if doc:
#             self.set_secure_cookie("user", username)
#             self.redirect("/")
#         else:
#             # No such user or wrong password.
#             self.redirect("/")

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class GetInfoHandler(tornado.web.RequestHandler):
    def get(self):
        dbconn = sqlite3.connect(settings.DATABASE)
        cursor = dbconn.cursor()
        cursor.row_factory=sqlite3.Row
        cursor.execute("SELECT [SwVer], [Power], [Flame], [Tset], [Tboiler], [State], [Status], [DHW], [Mode],[CHPump],[BF],[FF], [DHWPump], [Fan] \
                          FROM [BurnerLogs] WHERE [Date] >= datetime('now', '-1 minutes') ORDER BY [Date] DESC LIMIT 1")

        result = []
        rows = cursor.fetchall()
        for row in rows:
            d = dict(zip(row.keys(), row))
            result.append(d)

        self.write(json.dumps(result))
        self.set_header("Content-Type", "application/json")
        cursor.connection.close()


class GetStatsHandler(tornado.web.RequestHandler):
    def get(self):
        dbconn = sqlite3.connect(settings.DATABASE)
        cursor = dbconn.cursor()
        cursor.row_factory=sqlite3.Row

        timestamp = self.get_argument('timestamp', None)
        # print (timestamp)

        if ( timestamp == "null"):
            cursor.execute("SELECT strftime('%Y-%m-%dT%H:%M:%f', [Date]) AS [Date], [Power], [Flame], [Tset], [Tboiler], [DHW] \
                          FROM [BurnerLogs] WHERE [Date] > datetime('now', '-24 hours') ORDER BY [Date] ASC")
        else:
            timestamp = datetime.fromtimestamp(float(timestamp))
            cursor.execute("SELECT strftime('%Y-%m-%dT%H:%M:%f', [Date]) AS [Date], [Power], [Flame], [Tset], [Tboiler], [DHW] \
                          FROM [BurnerLogs] WHERE [Date] >:tstamp ORDER BY [Date] ASC", {"tstamp": timestamp})

        result = []
        rows = cursor.fetchall()
        for row in rows:
            d = dict(zip(row.keys(), row))
            result.append(d)

        self.write(json.dumps(result))
        self.set_header("Content-Type", "application/json")
        cursor.connection.close()

class GetConsumptionByMonthHandler(tornado.web.RequestHandler):
    def get(self):
        dbconn = sqlite3.connect(settings.DATABASE)
        cursor = dbconn.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute("SELECT [MonthYear] AS yr_mon, [FFWorkTime] as FFWork FROM [MonthConsumption];")
        result = []
        rows = cursor.fetchall()
        for row in rows:
            d = dict(zip(row.keys(), row))
            result.append(d)

        self.write(json.dumps(result))
        self.set_header("Content-Type", "application/json")
        cursor.connection.close()

class SetBoilerTemperatureHandler(tornado.web.RequestHandler):
    def post(self):
        json_obj = json_decode(self.request.body)
        boilerTemperature = json_obj["boilerTemperature"]
        sp = setBoilerTemperature.SerialProcessSet(int(boilerTemperature))
        sp.start()

        self.write(json.dumps(boilerTemperature))

class SetModeAndPriorityHandler(tornado.web.RequestHandler):
    def post(self):
        json_obj = json_decode(self.request.body)
        mode = json_obj["Mode"]
        priority = json_obj["Priority"]
        sp = SetModeAndPriority.SerialProcessSet(int(mode),int(priority))
        sp.start()
        self.write(json.dumps(json_obj))

# Work by hours
# SELECT sum(FFWorkTime), strftime ('%H',Date) hour
# FROM BurnerLogs
# GROUP BY strftime ('%H',Date)


class GetConsumptionStatsHandler(tornado.web.RequestHandler):
    def get(self):
        dbconn = sqlite3.connect(settings.DATABASE)
        cursor = dbconn.cursor()
        cursor.row_factory=sqlite3.Row
        cursor.execute("SELECT strftime('%Y-%m-%dT%H:%M:%f', datetime(t.[Date])) AS [Timestamp], \
                               ifnull((SELECT SUM([FFWorkTime]) \
                                         FROM [BurnerLogs] AS BL \
                                        WHERE BL.[TimeStamp] BETWEEN datetime(t.[Date]) AND datetime(t.[Date], '+3599 seconds')), \
                                      0) as [FFWorkTime] \
                          FROM (SELECT datetime('now', '-' || strftime('%M', 'now') || ' minutes', '-' || strftime('%S', 'now') || ' seconds', '-24 hours', '+' || (1 * (a.[a] + (10 * b.[a]) + (100 * c.[a]))) || ' hours') AS [Date] \
                                  FROM (SELECT 0 AS a UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) AS a \
                                 CROSS JOIN (SELECT 0 AS a UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) AS b \
                                 CROSS JOIN (SELECT 0 AS a UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) AS c \
                               ) AS t \
                         WHERE t.[Date] BETWEEN datetime('now', '-' || strftime('%M', 'now') || ' minutes', '-' || strftime('%S', 'now') || ' seconds', '-24 hours') AND datetime('now', '-' || strftime('%M', 'now') || ' minutes', '-' || strftime('%S', 'now') || ' seconds') \
                        UNION ALL \
                        SELECT strftime('%Y-%m-%dT%H:%M:%f', datetime('now')) AS [Timestamp], \
                               ifnull((SELECT SUM([FFWorkTime]) \
                                         FROM [BurnerLogs] AS BL \
                                        WHERE BL.[TimeStamp] BETWEEN datetime('now', '-' || strftime('%M', 'now') || ' minutes', '-' || strftime('%S', 'now') || ' seconds', '-24 hours') AND datetime('now', '-' || strftime('%M', 'now') || ' minutes', '-' || strftime('%S', 'now') || ' seconds')), \
                                      0) as [FFWorkTime] \
                        ORDER BY [Timestamp]")

        result = []
        rows = cursor.fetchall()
        for row in rows:
            d = dict(zip(row.keys(), row))
            result.append(d)

        self.write(json.dumps(result))
        self.set_header("Content-Type", "application/json")
        cursor.connection.close()


if __name__ == '__main__':
    tornado.options.parse_command_line()
    currDir = os.path.dirname( os.path.abspath(__file__))
    app = tornado.web.Application(
        handlers=[
            (r"/", IndexHandler),
            # (r"/", MainHandler),
            # (r"/login", LoginHandler),
            (r"/api/getInfo", GetInfoHandler),
            (r"/api/getStats", GetStatsHandler),
            (r"/api/getConsumptionStats", GetConsumptionStatsHandler),
            (r"/api/getConsumptionByMonth", GetConsumptionByMonthHandler),
            (r"/api/setBoilerTemperature", SetBoilerTemperatureHandler),
            (r"/api/setModeAndPriority", SetModeAndPriorityHandler),
            # (r"/content/(.*)", web.StaticFileHandler, {'path': currDir + '/content'}),
        ] #, cookie_secret="StrongPassKey"
    )
    httpServer = tornado.httpserver.HTTPServer(app)
    httpServer.listen(options.port)
    print ("Listening on port:", options.port)

    mainLoop = tornado.ioloop.IOLoop.instance()
    mainLoop.start()

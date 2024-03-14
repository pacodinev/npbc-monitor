CREATE TABLE [MonthConsumption] (
    [MonthYear] DATETIME NOT NULL PRIMARY KEY,
    [FFWorkTime] BIGINT NOT NULL DEFAULT 0);

CREATE TABLE [BurnerLogs] (
    [Timestamp] DATETIME NOT NULL PRIMARY KEY,
    [SwVer] NVARCHAR NOT NULL,
    [Date] DATETIME NOT NULL,
    [Mode] INTEGER NOT NULL,
    [State] INTEGER NOT NULL,
    [Status] INTEGER NOT NULL,
    [IgnitionFail] TINYINT NOT NULL,
    [PelletJam] TINYINT NOT NULL,
    [Tset] INTEGER NOT NULL,
    [Tboiler] INTEGER NOT NULL,
    [Flame] INTEGER NOT NULL,
    [Heater] TINYINT NOT NULL,
    [DhwPump] TINYINT NOT NULL,
    [DHW] TINYINT NOT NULL,
    [CHPump] TINYINT NOT NULL,
    [BF] TINYINT NOT NULL,
    [FF] TINYINT NOT NULL,
    [Fan] INTEGER NOT NULL,
    [Power] INTEGER NOT NULL,
    [ThermostatStop] TINYINT NOT NULL,
    [FFWorkTime] INTEGER NOT NULL);
CREATE UNIQUE INDEX idx_BurnerLogs_timestamp ON BurnerLogs(Timestamp ASC);
CREATE INDEX idx_BurnerLogs_date ON BurnerLogs(Date DESC);
CREATE INDEX idx_BurnerLogs_date_asc ON BurnerLogs(Date ASC);
CREATE TRIGGER update_month_consumption_insert INSERT ON [BurnerLogs]
  BEGIN
    INSERT INTO [MonthConsumption] VALUES(strftime('%Y-%m', NEW.Date), NEW.FFWorkTime)
      ON CONFLICT DO UPDATE
        SET FFWorkTime = FFWorkTime+excluded.FFWorkTime;
  END;
CREATE TRIGGER update_month_consumption_update UPDATE ON [BurnerLogs]
  BEGIN
    UPDATE OR ABORT [MonthConsumption]
        SET FFWorkTime = FFWorkTime-OLD.FFWorkTime WHERE MonthYear = strftime('%Y-%m', OLD.Date);
    INSERT INTO [MonthConsumption] VALUES(strftime('%Y-%m', NEW.Date), NEW.FFWorkTime)
      ON CONFLICT DO UPDATE
        SET FFWorkTime = FFWorkTime+excluded.FFWorkTime;
  END;
CREATE TRIGGER update_month_consumption_delete DELETE ON [BurnerLogs]
  BEGIN
    UPDATE OR ABORT [MonthConsumption]
        SET FFWorkTime = FFWorkTime-OLD.FFWorkTime WHERE MonthYear = strftime('%Y-%m', OLD.Date);
  END;

-- Table: ais

-- DROP TABLE ais;

CREATE TABLE ais
(
  seqid serial NOT NULL,
  datetime timestamp without time zone NOT NULL,
  mmsi character(9) NOT NULL,
  latitude double precision NOT NULL,
  longitude double precision NOT NULL,
  true_heading double precision,
  sog double precision,
  cog double precision,
  location geometry NOT NULL,
  src character varying (128)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE ais
  OWNER TO postgres;

-- Index: ais_mmsi_datetime

-- DROP INDEX ais_mmsi_datetime;

CREATE UNIQUE INDEX ais_mmsi_datetime
  ON ais
  USING btree
  (mmsi, datetime);

-- Index: ais_seqid

-- DROP INDEX ais_seqid;

CREATE UNIQUE INDEX ais_seqid
  ON ais
  USING btree
  (seqid);
ALTER TABLE ais CLUSTER ON ais_seqid;



-- Function: ais_insert()

-- DROP FUNCTION ais_insert();

CREATE OR REPLACE FUNCTION ais_insert()
  RETURNS trigger AS
$BODY$
    DECLARE
        loc      geometry;
    BEGIN
	loc := st_setsrid(st_makepointm(NEW.longitude, NEW.latitude, extract(epoch from new.datetime)), (4326));

	IF EXISTS ( SELECT 1 FROM ais WHERE ais.mmsi = NEW.mmsi AND ais.datetime = NEW.datetime) THEN
		-- this record already exists.  Need to turn this into an update
		-- and return null to cancel the insert
		UPDATE ais SET
			location = loc,
			true_heading = NEW.true_heading,
			sog = NEW.sog,
			cog = NEW.cog,
			latitude = NEW.latitude,
			longitude = NEW.longitude
		WHERE ais.mmsi = NEW.mmsi AND ais.datetime = NEW.datetime;
		return NULL;
	ELSE
		NEW.location := loc;
		return NEW;
	END IF;
    END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION ais_insert()
  OWNER TO postgres;

-- Trigger: ais_insert on ais

-- DROP TRIGGER ais_insert ON ais;

CREATE TRIGGER ais_insert
  BEFORE INSERT
  ON ais
  FOR EACH ROW
  EXECUTE PROCEDURE ais_insert();






-- Table: vessel

-- DROP TABLE vessel;

CREATE TABLE vessel
(
  id serial NOT NULL,
  mmsi character(9) NOT NULL,
  name character varying(100),
  type character varying(50) NOT NULL,
  length integer,
  url character varying(1024)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE vessel
  OWNER TO postgres;


create view ais_path as
  SELECT
    a.mmsi,
    st_makeline(a.location) AS line,
    min(a.datetime) AS timemin,
    max(a.datetime) AS timemax
  FROM
    (SELECT
       ais.seqid,
       ais.datetime,
       ais.mmsi,
       ais.latitude,
       ais.longitude,
       ais.true_heading,
       ais.sog,
       ais.cog,
       ais.location
     FROM ais
     ORDER BY
       ais.mmsi,
       ais.datetime) a
  GROUP BY a.mmsi
  HAVING count(a.location) > 1;

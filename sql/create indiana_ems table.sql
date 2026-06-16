CREATE EXTERNAL TABLE IF NOT EXISTS ems_db.indiana_ems (
    id INT,
    INCIDENT_DT STRING,
    INCIDENT_COUNTY STRING
)
STORED AS PARQUET
LOCATION 's3://ems-incidents/indiana/2025/'
TBLPROPERTIES ("parquet.compression"="SNAPPY");

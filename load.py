# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Extract module ~~~~~
import boto3
import logging

logger = logging.getLogger(__name__)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ LoadEmsDataset ~~~
#   Base class for loading EMS datasets into datastores
#


class LoadEmsData:
    def __init__(self, args: str):
        self.source_file = args.source
        self.df = None

        # TODO move these parameters to a config file
        self.import_size = 5000
        self.s3_bucket = 'ems-incidents'
        self.s3_folder = 'indiana/2025'
        self.file_name = 'test'


    def set_df(self, df):
        self.df = df

    def load_df_into_s3(self):
        try:
            # 1. select fields
            filtered_df = self.df[["_id", "INCIDENT_DT", "INCIDENT_COUNTY"]].copy()

            # 2. Construct the S3 destination URI
            s3_path = f"s3://{self.s3_bucket}/{self.s3_folder.strip('/')}/{self.file_name}.parquet"

            # 3. Export directly to S3 using the pyarrow engine
            try:
                filtered_df.to_parquet(
                    path=s3_path,
                    engine='pyarrow',
                    compression='snappy',   # Standard efficient compression for Parquet
                    index=False             # Excludes the pandas row index from saving
                )
                logger.info(f"Successfully saved recordset to {s3_path}")
            except Exception as e:
                logger.error(f"An error occurred in write data to S3:\n{e}")
        except Exception as ex:
            logger.error(f'An error occurred in loading ems df:\n{ex}')


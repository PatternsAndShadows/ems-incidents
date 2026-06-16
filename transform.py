# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Extract module ~~~~~
import logging

logger = logging.getLogger(__name__)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ EmergencyMedicalServiceRunsTransformer ~~~
#   Base class for transforming EMS datasets
#
class EmergencyMedicalServiceRunsTransformer:
    def __init__(self, args: str):
        self.source_file = args.source
        self.df = None

        #TODO move these parameters to a config file
        self.import_size = 25000

    def set_df(self, df):
        self.df = df

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ transform_ems_incident_data ~~~
    #   Transform the datasets that originate with the Department of Homeland Security,
    #       emergency medical service runs
    def transform_ems_incident_data(self):
        pass

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ validate_dataframe ~~~
    #   This method calls the validation methods that are relevant to the Indiana dataset
    def validate_dataframe(self):
        # identify bad data
        #   tag it or move it to a DLQ (dead letter queue)
        pass

    def replace_nulls(self, column_name, replacement=''):
        for column, missing_num in self.df.isna().sum().items():
            print(column, missing_num)

    def get_transformed_df(self):
        return self.df


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ IndianaEmsTransform ~~~
#   derived class for ems datasets originating from Indiana
class IndianaEmsTransform(EmergencyMedicalServiceRunsTransformer):
    def transform_ems_incident_data(self):
        try:
            self.validate_dataframe()
            self.replace_nulls(column_name='INCIDENT_COUNTY')
        except Exception as ex:
            print(ex)

    def replace_nulls(self, column_name, replacement='N/A'):
        self.df[column_name] = self.df[column_name].fillna(replacement)



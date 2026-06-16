import argparse

import extract as e
import transform as t
import load as l
import logging

#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_logging():
    """Configures the root logger settings."""
    # Define a clean format including the module name (%(name)s)
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=logging.DEBUG,  # Capture DEBUG level and above
        format=log_format,
        handlers=[
            logging.StreamHandler(),  # Print to console/terminal
            logging.FileHandler("C:\\appLogs\\ems-incidents\\app.log")  # Save to an app.log file
        ]
    )

def main(args):
    setup_logging()
    logging.info("Starting the ems-incidents application")

    extract = e.IdhsDataExtractor(args)
    transform = t.IndianaEmsTransform(args)
    loader = l.LoadEmsData(args)

    source_dataset = '42c5f7f2-bc83-4c97-a5bf-787fdfc8e667'         # TODO add to property file
    transform.set_df(extract.extract_sourcedata(source_dataset))
    transform.transform_ems_incident_data()                        #TODO create a factory class?
    loader.set_df(transform.get_transformed_df())
    loader.load_df_into_s3()
    logger.info("ems-incident run complete")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", type=str, default="input.json", help="input file for source data")
    args = parser.parse_args()
    main(args)



# TODO: add logging to kafka for real time monitoring
# TODO: Create a property file, move configuration to it
# TODO: Create github deployment pipeline
# TODO: parallize the ETL process
#       extract first chunk of records
#           transform that chunk
#           load that chunk
#       while the first chunks are being transformed and loaded, start extracting the second chunk, etc


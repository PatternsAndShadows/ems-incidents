import argparse

import extract as e
import transform as t
import load as l



def main(args):
    extract = e.IdhsDataExtractor(args)
    transform = t.IndianaEmsTransform(args)
    loader = l.LoadEmsData(args)

    source_dataset = '42c5f7f2-bc83-4c97-a5bf-787fdfc8e667'
    transform.set_df(extract.extract_sourcedata(source_dataset))
    transform.transform_ems_incident_data()                        #TODO create a factory class?
    loader.set_df(transform.get_transformed_df())
    loader.load_df_into_s3()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", type=str, default="input.json", help="input file for source data")
    args = parser.parse_args()
    main(args)



# TODO: add logging
#   1. to rotating files
#   2. to kafka for real time monitoring

# TODO: Create a property file, move configuration to it

# TODO: Create github deployment pipeline


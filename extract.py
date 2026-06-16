# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Extract module ~~~~~
import os
import ijson
import logging
import json
import pandas as pd
import urllib.request as ur
import urllib.parse as up
import urllib.error as ue

logger = logging.getLogger(__name__)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ JsonDataExtractor ~~~
#   Base class for transforming EMS datasets
#
class JsonDataExtractor:
    def __init__(self, args: str):
        self.source_file = args.source
        self.df = None

        #TODO move these parameters to a config file
        self.import_size = 5000
        self.run_state = 'sample'   # options: ['sample' | 'test' | 'live' ]
                                    # sample = only extract one 'import_size' worth of data
                                    # test = reserved, not currently used
                                    # live = extract the entire dataset

        logger.debug(f"import size set to {self.import_size}")

    # extract dataset from the website directly, no need to download the json file first.
    # This is a virtual function, it needs to be implemented in any derived classes
    def extract_sourcedata(self, source_dataset):
        logging.debug("you've reached the base class, virtual method extract_sourcedata. this method should be overwritten in a derived class")
        pass

    # this method does a lazy load of a locally stored json file, where the schema and records are in seperate arrays
    def load_json_file(self):
        if not os.path.exists(self.source_file):
            raise FileNotFoundError(f'Could not find file {self.source_file}')

        # 1. Parse the schema
        columns = self.get_source_header()

        # 2. Stream 'records' array item-by-item
        chunk_list = []
        for raw_chunk in self.get_source_records():
            df_chunk = pd.DataFrame(raw_chunk, columns=columns)
            chunk_list.append(df_chunk)

        if chunk_list:
            final_df = pd.concat(chunk_list, ignore_index=True)
            return final_df
        else:
            return pd.DataFrame()  # Return empty DataFrame if file was empty

    # get the header from the json source file
    def get_source_header(self):
        with open(self.source_file, "rb") as f:
            fields_itr = ijson.items(f, "fields.item")
            # TODO if the header is missing, throw exception
            return [field["id"] for field in fields_itr]

    #  get source records from the json file
    def get_source_records(self):
        results = []
        with open(self.source_file, 'rb') as f:
            rows = ijson.items(f, 'records.item')
            for row in rows:
                results.append(row)
                if len(results) == self.import_size:
                    yield results
                    results = []

            if results:
                yield results

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ IdhsDataExtractor ~~~
#   Derived class for extracting Emergency Medical Service (EMS) run data available through
#       department of homelanc security
#
class IdhsDataExtractor(JsonDataExtractor):
    def extract_sourcedata(self, source_dataset):
        full_url = f'https://hub.mph.in.gov/api/3/action/datastore_search?resource_id={source_dataset}&limit={self.import_size}'   # TODO move the base url to properties file
        while True:
            next_url = self.get_emsr_incidents_dataset(source_url = full_url)
            if next_url is None:
                break
            else:
                full_url = next_url

    def get_emsr_incidents_dataset(self, source_url):
        df = None
        full_next_url = None

        try:
            # 1. Execute the HTTP GET Request
            with ur.urlopen(source_url) as response:
                payload = json.loads(response.read().decode("utf-8"))

            # 2. Check the success element
            if not payload.get("success"):
                raise ValueError("API Request failed according to 'success' status flag.")
            print("✅ API Request validation successful.")

            # Safely extract the inner result dictionary
            result = payload.get("result", {})

            # 3. Check the next _links element
            links = result.get("_links", {})
            next_link = links.get("next")
            if next_link:
                # Reconstruct full URL if API returns relative pathing
                full_next_url = up.urljoin(source_url, next_link)
                print(f"🔗 Next page URL available: {full_next_url}")
            else:
                print("⚠️ No subsequent page links found.")

            # 4. Create a list from the fields array
            # CKAN fields typically arrive as objects, extract the unique text id/name
            fields_array = result.get("fields", [])
            field_headers = [field["id"] for field in fields_array if "id" in field]
            print(f"📋 Extracted Field Headers ({len(field_headers)}): {field_headers}")

            # 5. Create a Pandas DataFrame using records and strict headers
            records_array = result.get("records", [])
            print(f"📋 Extracted {self.import_size} records")

            # Passing explicit columns ensures structural consistency and order
            df = pd.DataFrame(records_array, columns=field_headers)
            self.df = pd.concat([self.df, df])

            print("\n📊 Generated Pandas Dataframe:")
            print(df.head())
        except ue.URLError as net_err:
            print(f"❌ Network connection or URL error encountered: {net_err}")
        except KeyError as key_err:
            print(f"❌ Structural parsing error: Key {key_err} missing from payload.")
        except Exception as err:
            print(f"❌ An unexpected runtime issue occurred: {err}")
        finally:
            return full_next_url

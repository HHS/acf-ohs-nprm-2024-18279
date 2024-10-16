import os
import logging
from datetime import datetime
from time import time
import pandas as pd
from dataclean_utils import *

cur_directory = os.path.dirname(os.path.abspath(__file__))
relative_log_path = 'logs/'
relative_output_path = 'outputs/intermediate/'
relative_input_path = 'inputs/'

log_path = os.path.join(cur_directory, relative_log_path)
output_path = os.path.join(cur_directory, relative_output_path)
input_path = os.path.join(cur_directory, relative_input_path)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

TIMESTAMP=datetime.now().strftime("%Y-%m-%d_%I-%M-%S-%p")

# Assign a file-handler to that instance
fh = logging.FileHandler(log_path + "log_dataprocess_{}.txt".format(TIMESTAMP))
fh.setLevel(logging.INFO) 

# Add the handler to your logging instance
logger.addHandler(fh)

ts = time()
# Read in the pickle file
df = pd.read_pickle(input_path + "2023_scrape.pkl")
# Check to see if the OHS_dontrun_response file exists, if yes, read it in
if os.path.isfile(os.path.join(input_path, "OHS_dontrun_response.xlsx")):
    ohs_resp = pd.read_excel(input_path + "OHS_dontrun_response.xlsx")
    #df = df.merge(ohs_resp[])

ts_pickle = time() - ts
print("Read pickle file in {} seconds".format(ts_pickle))
logger.info('Read pickle file in %s', ts_pickle)

ts = time()
df_chunk, df_dont_run = chunk_dataframe(df, 800)
ts_chunk = time() - ts
print("Chunked dataframe in {} seconds".format(ts_chunk))
logger.info('Chunked dataframe in %s', ts_chunk)

#df_chunk.to_csv(csv_path + "df_chunk.csv")
df_chunk.to_excel(output_path + "df_chunk.xlsx")
df_chunk.to_pickle(output_path + "df_chunk.pkl")
df_dont_run.to_excel(output_path + "df_dont_run.xlsx")
df_dont_run.to_pickle(output_path + "df_dont_run.pkl")
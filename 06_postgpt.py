import os
import logging
from datetime import datetime
from time import time
import pandas as pd
from postgpt__utils import *
import numpy as np
import pathlib

cur_directory = os.path.dirname(os.path.abspath(__file__))
relative_log_path = 'logs/'
relative_output_path = 'outputs/intermediate/'
relative_input_path = 'inputs/'
relative_finaloutput_directory = 'outputs/final/'

log_path = os.path.join(cur_directory, relative_log_path)
output_path = os.path.join(cur_directory, relative_output_path)
input_path = os.path.join(cur_directory, relative_input_path)
final_output_path = os.path.join(cur_directory, relative_finaloutput_directory)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

TIMESTAMP=datetime.now().strftime("%Y-%m-%d_%I-%M-%S-%p")

# Assign a file-handler to that instance
fh = logging.FileHandler(log_path + "log_postgpt_dataprocess_{}.txt".format(TIMESTAMP))
fh.setLevel(logging.INFO) 

# Add the handler to your logging instance
logger.addHandler(fh)
# Read in long file with missing sements
filename = "full_df_and_missing_segments5.xlsx"
print("reading in ", filename)

#load initial files
df = pd.read_excel(filename) 
df['topic_origin']="ChatGPT Topic Match"

df_bill_numbers = pd.read_excel(input_path + "2023_bill_number_tagging_vF.xlsx",dtype='str',header=0)
df['topic'] = df['topic'].astype('str')
df['topic'] = df['topic'].apply(lambda x: x.title())
df_bill_numbers['topic'] = df_bill_numbers['topic'].apply(lambda x: x.title())
df_bill_numbers = df_bill_numbers[['topic','bill_number']]

bill_number="130[0-9].[0-9]+"

# Create a topic crosswalk output for OHS
results, results_two = output_topic_crosswalk(df,df_bill_numbers)
with pd.ExcelWriter(final_output_path + '/topic_eval_for_OHS.xlsx') as writer:
    # Write each DataFrame to a different Excel sheet
    results.to_excel(writer, sheet_name='topic_count', index=False,)
    results_two.to_excel(writer, sheet_name='topic_correlation', index=False)

# Add exact matches: must be in Title case
term_dict = {"Disabilities, IDEA, 504 Plan and Individualized Education Plan":["504"], 
             "Data Privacy And FERPA": ["FERPA"]}

#exact terms
df = add_exact_terms(df, term_dict)

#clean bill numbers
df = manage_add_bill_numbers(df, df_bill_numbers,bill_number)

#clean output
df = clean_output(df, df_bill_numbers)

#roll up topics
df = roll_up(df)
df.sort_values(by=['text_chunk_id','segment_number','topic'],axis=0,na_position='last', inplace=True)

#extra cleaning
original_topics = df_bill_numbers.topic.to_list()
df['is_other_topic']=~df['topic'].isin(original_topics)
df['original_topic']=df['topic'].isin(original_topics)
df['uncategorized'] = np.where(df['topic']=="Uncategorized",True,False)
df['uncategorized'] = np.where(df['topic'].isna(),True,df['uncategorized'])
df.loc[df['uncategorized']==True,'is_other_topic']=False
df['segment_length'] = df['segment'].apply(lambda x: len(x.split(" ")))
df['segment_lessthan_30words'] = np.where(df['segment_length']<30,1,0)
df['segment_lessthan_15words'] = np.where(df['segment_length']<15,1,0)

#add metadata from pkl
df_pkl = pd.read_pickle(path+"/2023_scrape (1).pkl")
helpful_columns = ['Document','Received','Status','Name',  'Organization', 'Government Agency Type', 
                   'Government Agency', 'Email', 'Address', 'Phone', 'has_attachments', 
                   'attachment_count','head_start_commenter', 'congress_commenter']
df = add_meta_data(df,df_pkl,helpful_columns)

#save
cols_to_export = ['Document', 'text_chunk_id', 'text', 'segment_number', 'rolled_up', 'segment', 
                  'topic', 'intent', 'all_topics_in_segment', 'all_topics_in_chunk', 'topic_origin', 
                  'is_other_topic', 'original_topic', 'uncategorized', 'bill_numbers' , 
                  'segment_lessthan_30words', 'segment_lessthan_15words', 'has_attachments', 
                  'attachment_count', 'Comment_counts', 'attachment_text_counts', 'to_translate', 
                  'head_start_commenter', 'congress_commenter', 'Name', 'Organization', 
                  'Government Agency Type', 'Government Agency', 'Email', 'Address', 'Phone', 
                  'Received', 'Status']
df[cols_to_export].to_excel(final_output_path + "topic_results_{}.xlsx".format(TIMESTAMP))

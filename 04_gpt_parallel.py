import logging
import os
#from utils import *
from model_utils import *
from dataclean_utils import *
import pandas as pd
from queue import Queue
from threading import Thread
from datetime import datetime
from time import time, sleep
import json
import sys
import shutil


cur_directory = os.path.dirname(os.path.abspath(__file__))
relative_json_directory = 'json_outputs/'
relative_log_directory = 'logs/'
relative_input_directory = 'outputs/intermediate/'
relative_finaloutput_directory = 'outputs/final/'

json_path = os.path.join(cur_directory, relative_json_directory)
log_path = os.path.join(cur_directory, relative_log_directory)
input_path = os.path.join(cur_directory, relative_input_directory)
final_output_path = os.path.join(cur_directory, relative_finaloutput_directory)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

TIMESTAMP=datetime.now().strftime("%Y-%m-%d_%I-%M-%S-%p")

# Assign a file-handler to that instance
fh = logging.FileHandler(log_path + "log_model_{}.txt".format(TIMESTAMP))
fh.setLevel(logging.INFO) 

# Add the handler to your logging instance
logger.addHandler(fh)

class DownloadWorker(Thread):

    def __init__(self, queue, endpoints, output_path):
        Thread.__init__(self)
        self.queue = queue
        self.endpoints = endpoints
        self.output_path = output_path

    def run(self):
        prompt_23 = '''
        You are reading a comment that a member of the public has written in response to a proposed rule change coming from the Office of Head Start.  
        - Read the comment delineated by triple back-ticks
        - Break the comment into paragraph segments (segments must be at least 45 words long), and do the following tasks for each segment:
        - For each segment, determine if any of the below topics within this list of topics are being discussed within the segment and return the topic. The topic is listed between double quotes, and key words related to those topics are shown in parenthesis after the topic in double quotes. If the topic being discussed in the segment isn't within this list, return a new topic. If there are multiple topics discussed in the segment, return a list of the topics that are discussed.
        ["Standards of Conduct",
        "Duration for Early Head Start",
        "Duration for Head Start Preschool",
        "Lead in Water",
        "Lead in Paint",
        "Governing body and parent committees",
        "Health, nutrition and mental health",
        "Data Privacy and FERPA",
        "Program Structure: class size, hours of operation, length of school year",
        "Center or home based program structure",
        "Disabilities, IDEA, 504 Plan and Individualized Education Plan",
        "Delegate Agencies",
        "Funding suspension and refunding appeals",
        "<...>"]
    - For each segment return the "intent" of that segment (either "suggestion", "concern", "agreement" or a combination of those. If it's a combination,  return all choices in a list of strings)
    - All segments of the comment should be returned with associated topics, and intents.
    - If consecutive segements contain overlapping topics, then the segments should be combined into one.
    - Format your response as a single json following this format:
        {"segment_1": "<first segment of the comment>",
        "topic_1": "<list of topics found in the segment>",
        "intent_1": ",intent associated with this segment>",
        "segment_2": "second segment of comment (if applicable)>",
        "topic_2": "<list of topics found in the second segment (if applicable)>",
        "intent_2": "<intent associated with the second segment (if applicable)>" ,
        etc}
    - Before returning your response, ensure that your response is a valid json format.
        '''
        
        while True:
            # Get the work from the queue and expand the tuple
            comment_id, comment = self.queue.get()
            if os.path.isfile(os.path.join(self.output_path, "{}.json".format(comment_id))):
                    self.queue.task_done()
                    continue
            model = self.endpoints.get()

            try:
                full_prompt = prompt_23 + " ```{}```".format(comment)
                print("trying comment", comment_id)
                response = call_azure_openai(comment_id=comment_id,
                                            full_prompt=full_prompt,
                                             model=model)
                # Log comments with GPT errors
                if isinstance(response, dict) and 'error' in response.keys():
                    logger.info("OpenAI error for {}".format(comment_id))
                    logger.exception(response['error'])

                with open(os.path.join(self.output_path, "{}.json".format(comment_id)), 'w') as tmpfile:
                    tmpfile.write(response)
                with open(os.path.join(self.output_path, "{}.json".format(comment_id)), 'r') as file:
                    try:
                        json_data = json.load(file, strict=False)
                    except:
                        print("json issue and rerun")
                        response = call_azure_openai(comment_id=comment_id,
                                                        full_prompt=full_prompt,
                                                        model=model)
                        # Log comments with GPT errors
                        if isinstance(response, dict) and 'error' in response.keys():
                            logger.exception(comment_id + " " + response['error'])
                        # Writing to [chunk_text_id].json
                        with open(os.path.join(self.output_path, "{}.json".format(comment_id)), "w") as outfile:
                            outfile.write(response)
                    
                sleep(1)
            finally:
                self.endpoints.put(model)
                self.queue.task_done()

def main(output_path, comments, validation):
    ts = time()

    # Create a queue to communicate with the worker threads
    queue = Queue()
    endpoints = Queue()

    model1 = modelType('prod_gpt4')
    model2 = modelType('prod_gpt4_1')
    model3 = modelType('prod_gpt4_2')
    model4 = modelType('prod_gpt4_3')
    model5 = modelType('prod_gpt4_4')
    model6 = modelType('prod_gpt4_5')
    model7 = modelType('prod_gpt4_6')
    model8 = modelType('prod_gpt4_7')
    model9 = modelType('prod_gpt4_8')

    models = [model1, model2, model3, model4, model5, model6, model7, model8, model9]

    #models = [modelType("dev4")] # Using for local testing purposes

    worker_lst = []
    # Create enough worker threads for num of endpoints
    for _ in range(len(models)):
        worker = DownloadWorker(queue, endpoints, output_path)
        worker_lst.append(worker)
        # Setting daemon to True will let the main thread exit even though the workers are blocking
        worker.daemon = True
        worker.start()

    for model in models:
        logger.info('Queueing endpoint {}'.format(model.model_name))
        endpoints.put(model)
    
    df = comments.dataframe
    
    # If in validation stage, only send validation chunks to chatGPT
    if validation:
        df = df[df['validation'] == '1']
    

    print("sending {} comment chunks to chatGPT".format(len(df)))

    # Put the tasks into the queues as a tuple
    for i, doc_id in enumerate(df[comments.id_col]):
        if i%100 == 0:
            logger.info('Queued {} comments'.format(i))
        comment = df[df[comments.id_col]==doc_id][comments.comment_col].iloc[0]
        queue.put((doc_id, comment))
    
    # Causes the main thread to wait for the queue to finish processing all the tasks
    queue.join()
    logger.info('Took %s to run comments', time() - ts)
    return worker_lst

###################### Read in Data ################################
tstart = time()

# Determine if we are running the validation set or the full chunk set
if len(sys.argv) > 1:
    validation = True
    logger.info('Running validation set')
else:
    validation = False

df_chunk = pd.read_pickle(input_path + "df_chunk.pkl")
print("Read in data")

comments = commentDataframe(df_chunk, 'text', 'text_chunk_id')

# # Initiate queues, send data to chatGPT, and save responses in json files
workers = main(json_path, comments, validation)
print("completed GPT calls")

# Iterate through each json file in outputs folder and load contents
# into result_dict where keys are the chunk text ids
result_dict = {}
#failed_files_df = pd.DataFrame(columns=['failed_json_file'])
failedjsonlist = []

for filename in os.listdir(json_path):
    if filename.endswith('.json'):
        # Extract the chunk text id (file name without the .json suffix)
        key = os.path.splitext(filename)[0]
        # Read the contents of the JSON file
        file_path = os.path.join(json_path, filename)
        with open(file_path, 'r') as file:
            # Load the JSON data into a dictionary
            try:
                json_data = json.load(file, strict=False)
                result_dict[key] = json_data
            except:
                print("json issue with chunk {}", key)
                logger.info("json issue with chunk {}".format(key))
                #failed_files_df = pd.concat([failed_files_df, pd.DataFrame(['failed_json_file', filename])], ignore_index=True)
                failedjsonlist.append(filename)
                source_path = os.path.join(json_path, filename)
                destination_path = os.path.join(json_path+'/failed_json/', filename)
                shutil.copy(source_path, destination_path)                
            
failed_files_df = pd.DataFrame({'failed_json_file': failedjsonlist})
failed_files_df.to_csv(final_output_path + "failed_json_files_{}.csv".format(TIMESTAMP))

gpt_df = create_gpt_dataframe(result_dict)
gpt_df = gpt_df.merge(df_chunk[['text_chunk_id','Document','text','to_translate','validation','dont_run','Comment_counts','attachment_text_counts']], 
                      how='left', 
                      left_on="comment number", 
                      right_on="text_chunk_id")

print("outputting wide format xlsx")
if validation:
    gpt_df.to_excel(final_output_path + "gpt_responses_wide_val_{}.xlsx".format(TIMESTAMP))
else:
    gpt_df.to_excel(final_output_path + "gpt_responses_wide_{}.xlsx".format(TIMESTAMP))

gpt_df_long = melt_wide_cols(gpt_df)
gpt_df_long = gpt_df_long.explode('topic')

print("outputting long format to xlsx")
if validation:
    gpt_df_long.to_excel(final_output_path + "gpt_responses_long_val_{}.xlsx".format(TIMESTAMP))
else:
    gpt_df_long.to_excel(final_output_path + "gpt_responses_long_{}.xlsx".format(TIMESTAMP))
logger.info('Took %s to run full parallel script', time() - tstart)


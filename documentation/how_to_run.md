## How to run:
1. First, install packages within requirements.txt
2. Receive and unzip FDMS bulk download folder. Run "01_move_files_to_subfolder.ipynb" to sort files into different folders.
3. Run "02_clean_raw_data.ipynb" and convert all PDF files to docx files to create "2023_scrape.pkl". Save this file in the "inputs" folder.
6. Then run "03_data_processing.py" to read in the scraped data pickle and create the chunked dataframe. This chunk_df will be saved as its own pickle file in "outputs/intermediate/". This script also creates the "do not run" dataframe. This file was shared with OHS so they could decide which files to run to ChatGPT and which to omit.
8. Then we should run "python 04_gpt_parallel.py validation" via the command to send a random selection of 10 comments to chatGPT in parallel (the parameter "validation" indicates to gpt_parallel that there should only be a subset of comments run to ChatGPT). JSONs from chatGPT will be saved in the json_outputs folder. This code will output three csvs:
    - gpt_responses_wide_val_TIME.csv : The per chunk version of our final dataframe
    - gpt_responses_long_val_TIME.csv : The per chunk per segment version of our final dataframe
    - failed_json_files_TIME.csv : A csv that indicates which json files the program had trouble loading
9. Team reviews the gpt_responses_long_val.csv and runs the sniff test on this validation set to decide if we want to rerun these validation and future comments with a new prompt. If we want to rerun the validation set we should archive the jsons already outputted, and leave the "jsons_output" folder empty except for the jsons.txt file.
10. Steps 4 and 5 should be repeated until we are happy with the sniff test results and do not want to change the prompt. 
11. Then we should run "python 04_gpt_parallel.py" which will run all chunks of text in parallel through chatGPT and create three files:
    - gpt_responses_wide_TIME.csv
    - gpt_responses_long_TIME.csv
    - failed_json_files_TIME.csv
12. Troubleshoot failed json files and any other GPT errors
13. Manually check that all chunk_ids appear in the "long" dataframe. Manually add in any missing chunk text to the "long" file. 
15. Run "05_segment_return.ipynb" to add segments into the long file that were not returned by ChatGPT
16. Run "06_postgpt.py" on the long file (that includes missing segments from step 15) to reformat the long dataframe and add bill tagging/exact term matching and roll up consecutive segments with the same topics.
17. Run "07_create_summaries.py" using the desired summary list to send either the full segment list or a randomly sampled segment list to ChatGPT for summarization.

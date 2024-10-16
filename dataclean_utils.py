import pandas as pd
import numpy as np
from langdetect import detect
from fuzzywuzzy import fuzz 
from model_utils import *
import re

def add_translation_column(dataframe, text_column='Comment', new_column='to_translate'):
    # Function to detect language and return 1 if not English, 0 otherwise
    def detect_non_english(text):
        try:
            lang = detect(text)
            return 1 if lang != 'en' else 0
        except:
            # Handle exceptions (e.g., short or empty strings)
            return 1

    # Apply the language detection function to the specified column
    dataframe[new_column] = dataframe[text_column].apply(detect_non_english)

    return dataframe



def chunk_dataframe(df, word_count):

    run_attachment_list = ['ACF-2023-0011-0377-A1.docx', 'ACF-2023-0011-0377-A2.docx', 'ACF-2023-0011-0377-A3.docx', 
                           'ACF-2023-0011-0380-A1.docx', 'ACF-2023-0011-0380-A2.docx', 'ACF-2023-0011-0380-A3.docx', 
                           'ACF-2023-0011-0640-A1.docx', 'ACF-2023-0011-0667-A1.docx', 'ACF-2023-0011-0667-A2.docx', 
                           'ACF-2023-0011-0761-A1.docx', 'ACF-2023-0011-0761-A2.docx', 'ACF-2023-0011-0764-A1.png', 
                           'ACF-2023-0011-DRAFT-1064-A1.docx', 'ACF-2023-0011-DRAFT-1075-A1.docx', 'ACF-2023-0011-DRAFT-1075-A2.docx',
                           'ACF-2023-0011-DRAFT-1078-A1.docx', 'ACF-2023-0011-DRAFT-1079-A1.docx', 'ACF-2023-0011-DRAFT-1296-A1.docx']
    
    #replace duplicate long files
    dup_dict = {"ACF-2023-0011-DRAFT-0974-A1":"ACF-2023-0011-DRAFT-0971-A1",
                "ACF-2023-0011-DRAFT-1176-A1":"ACF-2023-0011-DRAFT-0954-A1",
                "ACF-2023-0011-0859-A1":"ACF-2023-0011-0731-A1",
                "ACF-2023-0011-0377-A3":"ACF-2023-0011-DRAFT-1105-A1"}
    
    for rem, keep in dup_dict.items():
        keep_text = df[df['Document'] == keep]['attachment_text_clean'].iloc[0]
        df.loc[df['Document'] == rem, 'attachment_text_clean'] = keep_text
        
    #remove missing comment language
    MIN_AVG_WORD_PER_PARAGRAPH = 15 # less than X words per paragraph on average
    MIN_AVG_WORD_PER_PARAGRAPH_ALLOWABLE_COUNT = 4 # AND more than X paragraphs
    
    MIN_CHAR_PER_PARAGRAPH = 120 # less than one line in a doc
    MIN_CHAR_PER_PARAGRAPH_PERCENT= 0.8 # X% of the paragraphs must be under X characters
    MIN_CHAR_PER_PARAGRAPH_ALLOWABLE_COUNT=5 # AND more than X paragraphs must be under X characters
    
    MIN_CHAR_PER_TITLE = 25 #less than one title
    MIN_CHAR_PER_TITLE_PERCENT= 0.55 # X% of paragraphs must be under X characters
    MIN_CHAR_PER_TITLE_ALLOWABLE_COUNT=5 # AND more than X paragraphs must by under X characters
    
    MAX_CHAR_PER_TITLE_ALLOWABLE_COUNT=50 # OR more than X paragraphs are under X characters
    
    df["paragraphs"]=df.attachment_text_clean.str.split(pat="\n",expand=False)
    df["paragraph_count"]=df["paragraphs"].apply(lambda x: len(x))
    
    #probably document parsing issue
    df["words_per_paragraph"] = df.attachment_text_clean.apply(lambda x: (x.count(" ")+1)/(x.count("\n")+1))
    df["flag_low_avg_words"] = ((df["words_per_paragraph"]<MIN_AVG_WORD_PER_PARAGRAPH) & (df["paragraph_count"]>MIN_AVG_WORD_PER_PARAGRAPH_ALLOWABLE_COUNT))
    
    #probably document parsing issue
    df["num_short_paragraphs"]=df["paragraphs"].apply(lambda x: sum([len(para)<MIN_CHAR_PER_PARAGRAPH for para in x]))
    df["percent_short_paragraphs"]=df["paragraphs"].apply(lambda x: sum([len(para)<MIN_CHAR_PER_PARAGRAPH for para in x])/len(x))
    
    df["flag_short_paragraphs"] = ((df["percent_short_paragraphs"]>MIN_CHAR_PER_PARAGRAPH_PERCENT) & (df["num_short_paragraphs"]>MIN_CHAR_PER_PARAGRAPH_ALLOWABLE_COUNT))
    
    #probably includes a lot of signatures
    df["num_short_titles"]=df["paragraphs"].apply(lambda x: sum([len(para)<MIN_CHAR_PER_TITLE for para in x]))
    df["percent_short_titles"]=df["paragraphs"].apply(lambda x: sum([len(para)<MIN_CHAR_PER_TITLE for para in x])/len(x))
    
    df["flag_short_titles"] = ((df["percent_short_titles"]>MIN_CHAR_PER_TITLE_PERCENT) & (df["num_short_titles"]>MIN_CHAR_PER_TITLE_ALLOWABLE_COUNT))
    df["flag_short_titles_v2"] = ((df["num_short_titles"]>MAX_CHAR_PER_TITLE_ALLOWABLE_COUNT))
    df["flag_mult_attachments"] = ((df["attachment_count"]>1))

    df["dont_run"] =  df["has_attachments"] & (df["flag_low_avg_words"] | 
                                           df["flag_short_paragraphs"] | 
                                           df["flag_short_titles"] | 
                                           df["flag_short_titles_v2"] | 
                                           df["flag_mult_attachments"])

    #olivia added, but didnt check if worked
    df["run_attachment"] = False
    df["run_attachment"] = df["attachment_name"].apply(lambda x: str(x) in run_attachment_list)

    df["dont_run"] = np.where(df["run_attachment"],False,df["dont_run"]) #will break code if df["override_dont_run"] is missing

    #plots to identify the numbers
    #plt.hist(df["percent_short_paragraphs"])
    #plt.hist(df["percent_short_titles"])
    #plt.hist(df["num_short_titles"],bins=20)
    #plt.hist(df[df["num_short_titles"]<100]["num_short_titles"],bins=20)
    #plt.hist(df["words_per_paragraph"])
    
    #other exploration code
    #df["flag_short_paragraphs"].value_counts()
    #df["flag_short_titles"].value_counts()
    #df["flag_short_titles_v2"].value_counts()
    #df["dont_run"].value_counts()
    #print(df.loc[((df["words_per_paragraph"]>15) & (df["words_per_paragraph"]<20))].attachment_text_clean.to_list()[6])
    #df[["has_attachments","flag_low_avg_words","flag_short_paragraphs","flag_short_titles","flag_short_titles_v2"]].value_counts()
    
    #save the not to run here
    #df[df["dont_run"]].to_pickle("comments_not_run_through_model.pkl")
    
    cols_do_not_run = ['Document', 'Name', 'Government Agency Type', 'Government Agency', 'Organization', 'attachment_name', 'attachment_count', 'attachment_has_tables', 'attachment_error', 'Comment_clean', 'attachment_text', 'attachment_text_clean'] #'run_attachment'
    df_dont_run = df[df["dont_run"]][cols_do_not_run]
    df_dont_run['run_attachment']=False
    
    print("dont run count!", df['dont_run'].sum())
    new_vars_to_drop=["paragraphs","paragraph_count","words_per_paragraph","flag_low_avg_words","num_short_paragraphs","percent_short_paragraphs","flag_short_paragraphs","num_short_titles","percent_short_titles","flag_short_titles","flag_short_titles_v2"]
    df.drop(labels=new_vars_to_drop,axis=1,inplace=True)
    ##### END FLAGGING CODE #######

    df.loc[df['Comment_clean']=="See attached file(s)",'Comment_clean']=""

    #clean text before running count of similarity 
    pattern = re.compile('[\W_]+')
    df['Comment_clean_strip'] = df['Comment_clean'].apply(lambda x: pattern.sub('', x).lower())
    df['attachment_text_clean_strip'] = df['attachment_text_clean'].apply(lambda x: pattern.sub('', x).lower())

    #count of comment occurance
    df['Comment_counts'] = df.Comment_clean_strip.groupby(df.Comment_clean_strip).transform('count')
    df['attachment_text_counts'] = df.attachment_text_clean_strip.groupby(df.attachment_text_clean_strip).transform('count')
    
    #cumlative count to remove duplicates
    df['Comment_cum_counts'] = df.Comment_clean_strip.groupby(df.Comment_clean_strip).cumcount()
    df['attachment_text_cum_counts'] = df.attachment_text_clean_strip.groupby(df.attachment_text_clean_strip).cumcount()

    #fix comment counts if duplicated by attachments
    df.loc[df['attachment_count']>1,'Comment_counts'] = (df.loc[df['attachment_count']>1]['Comment_counts'] - df.loc[df['attachment_count']>1]['attachment_count'] + 1)
    
    #reset comment counts if comment was blank
    df.loc[df['Comment_clean']=="",'Comment_counts']=0
    df.loc[df['attachment_text_clean']=="",'attachment_text_counts']=0

    #remove comment text if attachment and comment are within 90% similarity threshold -> HERE
    df['similarity_comment_attachment'] = df.apply(lambda x: fuzz.ratio(x.Comment_clean_strip, x.attachment_text_clean_strip), axis=1)
    df.loc[df['similarity_comment_attachment']>90,"Comment_clean"]=""
    
    #remove duplicate comment / attachment text
    df.loc[df['Comment_cum_counts']>0,'Comment_clean']=""
    df.loc[df['attachment_text_cum_counts']>0,'attachment_text_clean']=""

    #get rid of stripped text
    df.drop(labels=['Comment_clean_strip','attachment_text_clean_strip'],inplace=True,axis=1) #new

    #remove dont run
    df.loc[df['dont_run'],'attachment_text_clean']="<OHS redacted attachment>"    
    
    #remove rows with no comment or attachment
    df['no_comment_or_attachment_flag']=((df['Comment_clean']=="") & (df['attachment_text_clean']==""))
    df_errors = df.loc[df['no_comment_or_attachment_flag']]
    df_dedup = df[~df['no_comment_or_attachment_flag']]
    
    #save out error comments for review
    df_errors.to_excel('comments_removed.xlsx')
    df_errors #this needs to be saved and reviewed to make sure no comments are accidentally removed
    
    #combine comment and attachment text
    df_dedup['all_text']=np.where(df_dedup['Comment_clean']=="",df_dedup['attachment_text_clean'],df_dedup['Comment_clean']+'\n '+df_dedup['attachment_text_clean'])
    df_dedup.drop(labels=['Comment','attachment_text','attachment_name','Comment_clean','attachment_text_clean','Comment_cum_counts','attachment_text_cum_counts','no_comment_or_attachment_flag'],axis=1,inplace=True)
    df_dedup.drop(labels=['As of','Posted','Comments Due', 'Submission Type','Comment On'],axis=1,inplace=True)
    
    df_dedup = add_translation_column(df_dedup, 'all_text', 'to_translate')
    for doc_id in df_dedup['Document']:
        if df_dedup.loc[df_dedup['Document']== doc_id, 'to_translate'].iloc[0] == 1:
            non_eng_comment = df_dedup.loc[df_dedup['Document']== doc_id, 'all_text'].iloc[0]
            translation = translate_comment(doc_id, non_eng_comment)
            df_dedup.loc[df_dedup['Document']== doc_id, 'all_text'] = translation
    
    # Add column indicating validation
    df_dedup['validation'] = 0
    validation_indices = np.random.choice(df_dedup[~df_dedup['dont_run']].index, size=100, replace=False)
    df_dedup.loc[validation_indices, 'validation'] = 1

    #pg0 stacks all attachments per document id
    col_names=['Document', 'to_translate','all_text','validation','dont_run','Comment_counts','attachment_text_counts'] #could add more here if we want to retain meta data
    pg0 = df_dedup.groupby(by=col_names, as_index = False).agg({'all_text': '\n '.join})
    
    #pg1 splits each document by paragraph, with a row per pararaph
    pg1 = pd.concat([pg0,pg0.all_text.str.split(pat="\n",expand=True)],axis=1)
    pg1 = pd.melt(pg1,id_vars=["Document", "all_text", 'to_translate','validation','dont_run','Comment_counts','attachment_text_counts'],value_vars=pg1.columns[2:],var_name="paragraph_id",value_name="text")
    
    pg1 = pg1.replace(to_replace='None', value=np.nan).dropna()
    pg1["text"]=pg1["text"].apply(lambda x: x.strip())
    
    #pg2 removes empty paragraphs, and counts cumulative words per paragraph
    pg2 = pg1[pg1["text"]!=""].copy().sort_values(by=["Document","paragraph_id"],axis=0)
    pg2.astype('str')
    pg2["word_count"]=pg2["text"].str.count(" ")+1
    
    pg2["chunk"]=""
    
    #new chunking
    last_document_id='' #try none
    chunk = 0
    words = 0
    
    for index, row in pg2.iterrows():
        current_document_id = row['Document']
        if current_document_id!=last_document_id:
            chunk = 0
            words = 0
        
        words+=row['word_count']
        if words>word_count:
            chunk+=1
            words=row['word_count']
    
        pg2.loc[index,"chunk"]=chunk
        last_document_id = current_document_id
    
    #pg3 groups the paragraphs into chunks or text below the word count
    pg3 = pg2.groupby(["Document","chunk","to_translate","all_text","validation","dont_run","Comment_counts","attachment_text_counts"], as_index = False).agg({'text': '\n '.join})
    pg3=pg3.astype('str')
    pg3["text_chunk_id"]=pg3["Document"]+"-"+pg3["chunk"]
    return (pg3, df_dont_run)


def clean_json_vals(gpt_dict):
    '''
    Turns gpt_dict into a dictionary of dictionaries rather than a dictionary of
    strings. 
    Inputs: 
        gpt_dict: (dict) dictionary of json strings
    Returns:
        gpt_dict_clean: (dict) dictionary of dictionaries
    '''
    gpt_dict_clean = {}
    for comment_id, json_val in gpt_dict.items():
        print(comment_id)
        print(json_val)
        val_dict = json.loads(json_val)
        gpt_dict_clean[comment_id] = gpt_dict_clean.get(comment_id, val_dict)

    return gpt_dict_clean


def create_gpt_dataframe(gpt_dict):
    '''
    Iterates through dictionaries to find the max number of columns needed for our
    dataframe. Then iterates through that max number to add rows of data from the 
    gpt dictionaries to a dataframe. 
    Inputs:
        gpt_dict: (dict) dictionary of dictionaries. 
    Returns:
        gpt_df: (dataframe) 
    '''
    max_col_count = 0
    for _, v in gpt_dict.items():
        if len(v.keys()) > max_col_count:
            max_col_count = len(v.keys())

    print("max column count is ", max_col_count)

    gpt_lst = []
    for comment_id, comment_dict in gpt_dict.items():
        row_data = {"comment number": comment_id,
                    "topic_1": comment_dict.get('topic_1'),
                    "segment_1": comment_dict.get('segment_1'),
                    "intent_1": comment_dict.get('intent_1')}
        for i in range(2,max_col_count):
            row_data["topic_{}".format(i)] = comment_dict.get("topic_{}".format(i),"")
            row_data["segment_{}".format(i)] = comment_dict.get("segment_{}".format(i),"")
            row_data["intent_{}".format(i)] = comment_dict.get("intent_{}".format(i),"")
        gpt_lst.append(row_data)

    # Create DataFrame
    gpt_df = pd.DataFrame(gpt_lst)

    return gpt_df


def melt_wide_cols(gpt_df):
    '''
    Turns wide dataframe with one row per comment into a long dataframe 
    with one row per comment per topic assigned by chatgpt. 
    Inputs:
        gpt_df: (dataframe) wide dataframe with one row per comment
    Returns:
        gpt2: (dataframe) long dataframe with one row per comment per segment of comment returned.
    '''
    mask_segment=["segment" in x for x in gpt_df.columns]
    mask_topic=["topic" in x for x in gpt_df.columns]
    mask_intent=["intent" in x for x in gpt_df.columns]
    
    #id_vars=["comment number","Comment_clean","Document"]
    id_vars=['comment number','text_chunk_id', 'Document', 'text', 'to_translate', 'validation','dont_run','Comment_counts','attachment_text_counts']
    
    gpt_segment = pd.melt(gpt_df,id_vars=id_vars, value_vars=gpt_df.columns[mask_segment], var_name="segment_number",value_name="segment")
    gpt_topic = pd.melt(gpt_df,id_vars=id_vars, value_vars=gpt_df.columns[mask_topic], var_name="topic_number",value_name="topic")
    gpt_intent = pd.melt(gpt_df,id_vars=id_vars, value_vars=gpt_df.columns[mask_intent], var_name="intent_number",value_name="intent")
    
    gpt2 = pd.concat([gpt_topic, gpt_segment.drop(labels=id_vars,axis=1), gpt_intent.drop(labels=id_vars,axis=1)],axis=1)
    
    gpt2.dropna(subset="topic",inplace=True)
    gpt2.sort_values(by=["comment number","topic_number"],inplace=True)
    gpt2 = gpt2.replace(to_replace='', value=np.nan).dropna()
    return gpt2

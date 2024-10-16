import pandas as pd
import numpy as np
import ast #add to req file
from ast import literal_eval

def output_topic_crosswalk(df,df_bill_numbers):
  '''takes in df for validation set, and returns topics crosswalk excel tabs'''
  #flag original topics
  original_topics = df_bill_numbers.topic.to_list() #new
  df['is_other_topic']=~df['topic'].isin(original_topics) #new

  #all topics
  results_zero = df[['topic','is_other_topic']].value_counts() #new

  #split topics by size of topic group
  topic_groups = df.groupby(["text_chunk_id","segment_number"])['topic'].apply(list).reset_index(name='topic_list')
  topic_groups["count"] = topic_groups["topic_list"].apply(lambda x: len(x))
  
  #appears alone
  one = topic_groups[topic_groups["count"]==1]
  one['topic_list'] = one['topic_list'].apply(lambda x: x[0])
  results_one = one.topic_list.value_counts()
  
  #topics in sets
  df_filter = df[~df['is_other_topic']] #new
  topic_groups_filter = df_filter.groupby(["text_chunk_id","segment_number"])['topic'].apply(list).reset_index(name='topic_list') #new
  topic_groups_filter["count"] = topic_groups_filter["topic_list"].apply(lambda x: len(x)) #new
  
  two = topic_groups_filter
  two['first_topic'] = two.topic_list.apply(lambda x: x[0])
  two['second_topic'] = two['first_topic']
  two.loc[two["count"]>1,'second_topic'] = two.loc[two["count"]>1,'topic_list'].apply(lambda x: x[1])
  
  two_three = topic_groups_filter[topic_groups_filter["count"]==3]
  
  two_three['first_topic'] = two_three.topic_list.apply(lambda x: x[0])
  two_three['second_topic'] = two_three.topic_list.apply(lambda x: x[1])
  two_three['third_topic'] = two_three.topic_list.apply(lambda x: x[2])
  
  #duplicate so order doesnt matter
  two_dup=pd.DataFrame({"first_topic":two['first_topic'].to_list() + 
                        two['second_topic'].to_list() + 
                        two_three['first_topic'].to_list() + 
                        two_three['second_topic'].to_list() + 
                        two_three['third_topic'].to_list() + 
                        two_three['third_topic'].to_list(),
                        "second_topic":two['second_topic'].to_list() + 
                        two['first_topic'].to_list() + 
                        two_three['third_topic'].to_list() + 
                        two_three['third_topic'].to_list() + 
                        two_three['first_topic'].to_list() + 
                        two_three['second_topic'].to_list() })

  results_two = pd.crosstab(index=two_dup['first_topic'],columns=two_dup['second_topic'],normalize="columns").round(1)
  
  #topics that appear in sets of three or more
  three_plus = topic_groups[topic_groups["count"]>2]
  results_three = three_plus.explode("topic_list").topic_list.value_counts() #this flags comments that appear with others frequently
  
  #combine results
  results_two.reset_index(inplace=True)
  results_zero = pd.DataFrame(results_zero)
  results_zero.reset_index(level='is_other_topic',inplace=True)
  results_zero.columns = ['Is_other_topic', 'Count_total'] #new
  results_one = pd.DataFrame(results_one)
  results_three =pd.DataFrame(results_three)
  results=results_zero.join(results_one)
  results.rename(columns={"topic_list":"Count_alone"},inplace=True)
  results=results.join(results_three)
  results.rename(columns={"topic_list":"Count_in_set_of_three_or_more"},inplace=True)
  results.reset_index(inplace=True)
  results.fillna(0,inplace=True)


  return (results, results_two) 
  

def roll_up(df):
  '''combine consecutive topic segments'''

  #create segment number
  df['segment_number_int'] = df['segment_index.1']
  df["prior_segment_number_int"] = df["segment_number_int"]-1

  #fix topic list
  df_topic_groups = df.groupby(['text_chunk_id','segment_number_int']).agg({'topic':lambda x: list(x)}).reset_index()
  df_topic_groups.columns = ['text_chunk_id','segment_number_int','all_topics_in_segment']
  df = pd.merge(df,df_topic_groups,on=['text_chunk_id', 'segment_number_int'],suffixes=("","_drop"),how='left')

  #merge topic list on prior
  df_topic_groups.columns = ['text_chunk_id','prior_segment_number_int','prior_all_topics_in_segment']
  df = pd.merge(df,df_topic_groups,on=['text_chunk_id', 'prior_segment_number_int'],suffixes=("","_drop"),how='left')

  #make itterable. Cant be empty list because not hashable
  df['prior_all_topics_in_segment'].fillna(value='',inplace=True)

  #check topic in prior
  df['topic_in_prior']=df.apply(lambda x: x["topic"] in x['prior_all_topics_in_segment'],axis=1)
  df['indexing_rollup']=np.where(df['topic_in_prior'],0,1)

  #put consecutive topics in same topic group
  df.sort_values(by=['text_chunk_id','segment_number_int','topic'],axis=0,na_position='last', inplace=True)
  df['topic_groups']= df.groupby(['text_chunk_id','topic'])['indexing_rollup'].cumsum()

  #fix segments
  appropriate_endings = [".","?","!",",",":","…"]
  double_endings = ['”','"',"'","’","n"]
  df["correct_ending"] = df["segment"].apply(lambda x: x[-1]).isin(appropriate_endings) | (df["segment"].apply(lambda x: x[-1]).isin(double_endings) & df["segment"].apply(lambda x: x[-2]).isin(appropriate_endings))
  df.loc[~df["correct_ending"],"segment"] = df.loc[~df["correct_ending"],"segment"]+"."
  df=df.drop(labels=["correct_ending"],axis=1)

  #identify columns to keep
  cols_keep = ['text_chunk_id', 'Document', 'text', 'to_translate',
        'validation', 'topic', 'is_other_topic', 'topic_groups', 'dont_run', 'Comment_counts',
       'attachment_text_counts'] # must include ['text_chunk_id','topic','topic_groups']

  def lists_to_set(lists):
    '''combines list of lists into a set'''
    result = set()
    for list in lists:
      for e in list:
        result.add(e)
    return result

  #roll up
  df_rolled = df.groupby(cols_keep).agg({'segment_number_int': [min, max],
                                        'segment': ' '.join,
                                        'intent': lambda x: list(lists_to_set(x)),
                                        'bill_numbers': lambda x: list(lists_to_set(x)),
                                        'all_topics_in_segment':lambda x: list(lists_to_set(x)),
                                        'topic_origin': lambda x: list(set(x))})

  df_rolled.columns = df_rolled.columns.droplevel(1)
  df_rolled.columns = ['segment_number', 'segment_number_end', 'segment', 'intent', 'bill_numbers',
                        'all_topics_in_segment','topic_origin']
  df_rolled.reset_index(inplace=True)

  df_rolled['rolled_up'] =  df_rolled['segment_number']!=df_rolled['segment_number_end']

  #full topic list for chunk
  df_topic_groups = df_rolled.groupby(['text_chunk_id']).agg({'topic':lambda x: list(x)}).reset_index()
  df_topic_groups.columns = ['text_chunk_id','all_topics_in_chunk']
  df_rolled = pd.merge(df_rolled,df_topic_groups,on=['text_chunk_id'],suffixes=("","_drop"),how='left')

  return df_rolled

def col_to_list(row):
    if pd.isnull(row):
        return []
    else:
        return literal_eval(row)

def add_bill_numbers(df,df_bill_numbers,bill_number):
  '''Takes long df and adds topic for each bill number'''

  df["bill_numbers"]=df["segment"].str.findall(pat=bill_number)
  df_bill = df[~df["bill_numbers"].isin([[]])]

  cols = ["intent","intent_number","topic",'topic_number']
  for col in cols:
    df_bill[col]="uncategorized"
  df_bill['topic_origin']="Bill Number Match"

  df_bill_long = df_bill.explode("bill_numbers")
  df_bill_long.drop_duplicates(subset=['text_chunk_id', 'Document', 'topic', 'segment', 'bill_numbers'], 
                               inplace=True)

  df_bill_match = pd.merge(df_bill_long, df_bill_numbers, left_on='bill_numbers', right_on='bill_number',
                           suffixes=("_drop",""))
  df_bill_match["topic_number"]="topic_bill_number"

  df_return = pd.concat([df,df_bill_match[df.columns]])
  df_return["bill_numbers"]=df_return["segment"].str.findall(pat=bill_number)
  #df_return.drop(labels=["bill_numbers"],inplace=True,axis=1)

  df_return.reset_index(inplace=True)
  df_return.drop(labels=["index"],inplace=True,axis=1)
  df_return.drop_duplicates(subset=["text_chunk_id","topic","segment"],keep='first',inplace=True)

  return df_return

def manage_add_bill_numbers(df,df_bill_numbers,bill_number):
  ''' runs bill number code separately for duplicated and unduplicated bill numbers'''
  df_bill_numbers['count'] = df_bill_numbers.groupby('bill_number')['bill_number'].transform('count')

  #filter df and df_bill_number
  original_topics = df_bill_numbers.topic.to_list()
  df['is_other_topic']=~df['topic'].isin(original_topics)

  df_categorized = add_bill_numbers(df[df['topic'].isin(original_topics)],
                                    df_bill_numbers[df_bill_numbers['count']==1],bill_number)
  df_uncategorized = add_bill_numbers(df[~df['topic'].isin(original_topics)],df_bill_numbers,bill_number)

  df_bills = pd.concat([df_categorized,df_uncategorized])
  df_bills.drop_duplicates(subset=["text_chunk_id","topic","segment"],keep='first',inplace=True)
  df_bills['is_other_topic']=~df_bills['topic'].isin(original_topics)

  return df_bills


def make_lower_list(entry):
  '''built for fixing the intent list'''
  if entry is None:
    return []
  elif type(entry)==str:
    if (entry[0]=="[") and (entry[-1]=="]"):
      l = ast. literal_eval(entry)
      return [x.lower() for x in l]
    else:
        return [entry.lower()]
  elif type(entry)==list:
    return [x.lower() for x in entry]

def clean_output(df,df_bill_numbers):
  '''clean formatting for OHS output'''

  #is other
  original_topics = df_bill_numbers.topic.to_list()
  df['is_other_topic']=~df['topic'].isin(original_topics)

  if 'comment number' in df.columns:
    df.drop(labels=['comment number'],inplace=True,axis=1)

  #clean intent
  df.intent = df.intent.apply(make_lower_list)

  #remove other topics for segments with original topics
  def intersection_size(lst1, lst2):
      return len(list(set(lst1) & set(lst2)))>0

  #segment full topic list
  df_topic_groups = df.groupby(['text_chunk_id','segment']).agg({'topic':lambda x: list(x)}).reset_index()
  df_topic_groups.columns = ['text_chunk_id','segment','all_topics_in_segment']
  df = pd.merge(df,df_topic_groups,on=['text_chunk_id', 'segment'],suffixes=("","_drop"),how='left') 


  df['topics_contain_original'] = df['all_topics_in_segment'].apply(lambda x: 
                                                                    intersection_size(x,original_topics))
  df['other_drop'] = (df['is_other_topic'] & df['topics_contain_original'])
  df = df[~df['other_drop']]
  df.drop(labels=['other_drop','topics_contain_original'],axis=1,inplace=True)

  return df
  
def add_meta_data(df,df_pkl,helpful_columns):
  '''match in meta data from pkl file'''
  df_pkl = df_pkl[helpful_columns]
  df_pkl.drop_duplicates(subset=['Document'],keep='first',inplace=True)
  
  df_meta = pd.merge(df,df_pkl,on="Document",suffixes=("","_drop"),how='left')
  df_meta["head_start_commenter"] = df_meta.Organization.str.contains(pat=r"Head Start.*?Association",case=False)
  df_meta['head_start_commenter']=df_meta['head_start_commenter'].fillna(False)
  return df_meta

def add_exact_terms(df,term_dict):
  '''add exact term matches into topics'''
  # create a new dataframe thats a row per chunk_id per segment
  dfd = df.drop_duplicates(["segment", "text_chunk_id"])
  # adjust the columns
  dfd['topic'] = None
  dfd['topic_number'] = "uncategorized"
  dfd['intent_number'] = "uncategorized"
  dfd['intent'] = "uncategorized"
  dfd['topic_origin'] = "Exact Match"

  for i in dfd.index:
      row = dfd.loc[i]
      chunk_id = row['text_chunk_id']
      segment = row['segment']
      # create mini dataframe of just the duplicates of this segment for this chunk_id
      # to see which topics it was already categorized to
      segments_df = df[(df['segment']==segment) & (df['text_chunk_id']==chunk_id)]
      topic_lst = []
      for topic, terms in term_dict.items():
          for term in terms:
              if term.lower() in segment.lower() and topic not in segments_df.topic.unique():
                  topic_lst.append(topic)
                  break
      dfd.loc[i, 'topic'] = str(topic_lst)
      dfd.loc[i, 'topic_number'] = "Exact Term Match"

  dfd = dfd[dfd['topic']!= "[]"]
  dfd['topic'] = dfd['topic'].apply(col_to_list)
  dfd = dfd.explode("topic")

  final = pd.concat([df, dfd])
  return final

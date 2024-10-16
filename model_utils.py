import openai
from langdetect import detect
from dotenv import load_dotenv
import os
load_dotenv()

class commentDataframe():
    '''
    Class to represent a dataframe to be sent to chatGPT for comment
    analysis
    Attributes:
        dataframe: (dataframe) holds dataframe containing comments and ids and other
            columns
        comment_col: (str) string representing column that holds text to be sent to
            chatGPT
        id_col: (str) string representing column that holds unique identifier for each 
            text chunk
    '''
    
    def __init__(self, dataframe, comment_col, id_col):
        '''
        Parameters:
            dataframe: (dataframe) holds dataframe containing comments and ids and other
                columns
            comment_col: (str) string representing column that holds text to be sent to
                chatGPT
            id_col: (str) string representing column that holds unique identifier for each 
                text chunk
        '''
        self.dataframe = dataframe
        self.comment_col = comment_col
        self.id_col = id_col
    


class modelType():
    '''
    Class to represent a model and the information needed to send a request to azure.
    Attributes:
        model_name: (str) indicates which azure information should be stored.
        endpoint: (str) the base_url needed to access the azure endpoint
        key: (str) the key needed to access the azure endpoint
        deployment_name: (str) the deployment name of the model we want to query
    Methods:
        get_azure_info(): returns the azure endpoint and deployment information for
            a specific model_name
    '''
    def __init__(self, model_name):
        '''
        Parameters:
            model_name: (str) indicates which azure information should be stored.
            endpoint: (str) the base_url needed to access the azure endpoint
            key: (str) the key needed to access the azure endpoint
            deployment_name: (str) the deployment name of the model we want to query
        '''
        self.model_name = model_name
        self.endpoint, self.key, self.deployment_name = self.get_azure_info()
    
    def get_azure_info(self):
        '''
        Returns the azure endpoint and deployment information for a specific model_name
        '''
        if self.model_name == "dev35":
            return(os.environ.get('dev_endpoint'),
                   os.environ.get('dev_key'),
                   'ohsp2_gpt_35_turbo16k')
        elif self.model_name == "dev4":
            return(os.environ.get('dev_endpoint'),
                   os.environ.get('dev_key'),
                   'ohsp2_gpt4_preview')
        elif self.model_name == "lang35":
            return(os.environ.get('lang_endpoint'),
                   os.environ.get('lang_key'),
                   'General-Comment-Ingest')
        elif self.model_name == "lang4":
             return(os.environ.get('lang_endpoint'),
                   os.environ.get('lang_key'),
                   'Language-Ingest')
        elif self.model_name == "prod_gpt4":
             return(os.environ.get('prod_gpt4_endpoint'),
                   os.environ.get('prod_gpt4_key'),
                   'ohs-gpt4-1106-preview')
        elif self.model_name == "prod_gpt4_1":
             return(os.environ.get('prod_gpt4_endpoint'),
                   os.environ.get('prod_gpt4_key'),
                   'ohs-gpt4-1106-1')
        elif self.model_name == "prod_gpt4_2":
             return(os.environ.get('prod_gpt4_endpoint'),
                   os.environ.get('prod_gpt4_key'),
                   'ohs-gpt4-1106-2')
        elif self.model_name == "prod_gpt4_3":
             return(os.environ.get('prod_gpt4_endpoint'),
                   os.environ.get('prod_gpt4_key'),
                   'ohs-gpt4-1106-3')
        elif self.model_name == "prod_gpt4_4":
             return(os.environ.get('prod_gpt4_endpoint'),
                   os.environ.get('prod_gpt4_key'),
                   'ohs-gpt4-1106-4')        
        elif self.model_name == "prod_gpt4_5":
             return(os.environ.get('prod_gpt4_endpoint1'),
                   os.environ.get('prod_gpt4_key1'),
                   'ohs-gpt4-1106-preview')
        elif self.model_name == "prod_gpt4_6":
             return(os.environ.get('prod_gpt4_endpoint1'),
                   os.environ.get('prod_gpt4_key1'),
                   'ohs-gpt4-1106-preview-1')
        elif self.model_name == "prod_gpt4_7":
             return(os.environ.get('prod_gpt4_endpoint1'),
                   os.environ.get('prod_gpt4_key1'),
                   'ohs-gpt4-1106-preview-2')
        elif self.model_name == "prod_gpt4_8":
             return(os.environ.get('prod_gpt4_endpoint1'),
                   os.environ.get('prod_gpt4_key1'),
                   'ohs-gpt4-1106-preview-3')
        
def get_gpt_response(prompt, 
                     comments, 
                     comment_count, 
                     model):
    '''
    Call chatGPT for each comment in the comments dataframe and store the response in a dictionary. 
    Returns a dictionary with the key = the comment id and the value is a json
    response from chatgpt.
    Inputs:
        prompt: (str) question to be sent to chatGPT along with comment
        comments: (commentDataframe instance) instantiation of commentDataframe class
        comment_count: (int) number of comments to run
        model: (modelType instance) instantiation of model type containing azure information
    Returns:
        gpt_dict: (dict) dictionary with the key = the comment id and the value is a json
        response from chatgpt 
    '''

    df = comments.dataframe
    gpt_dict = {}
    for i, com in enumerate(df[comments.comment_col][:comment_count]):
        prompt_com = prompt + " ```{}```".format(com)
        print("Running comment number ", comment_key)
        response = call_azure_openai(prompt_com, model)
        if response == 'error':
            continue
        comment_key = df[comments.id_col].iloc[i]
        gpt_dict[comment_key] = gpt_dict.get(comment_key, response)
        
    return gpt_dict


def call_azure_openai(comment_id,
                    full_prompt, 
                      model):
    '''
    Sends one comment to an azure openai resource
    Inputs:
        full_prompt: (str) string that contains both the analysis prompt and comment to be sent to chatGPT
        model: (modelType instance) instantiation of model type containing azure information
    Returns: 
        gpt_response: (json str) json response in string format from chatGPT
    '''
    deployment_name = model.deployment_name
    openai.api_type = "azure"
    openai.api_key = model.key
    openai.api_base = model.endpoint
    openai.api_version = "2023-05-15"

    try:
        # Create a completion for the provided prompt and parameters
        # To know more about the parameters, checkout this documentation: https://learn.microsoft.com/en-us/azure/cognitive-services/openai/reference
        completion = openai.ChatCompletion.create(
                        messages=[{"role": 'user',
                                "content":full_prompt}],
                        temperature=0,
                        engine=deployment_name)
        gpt_response = completion.choices[0].message['content']
        gpt_response = gpt_response.strip("```")
        gpt_response = gpt_response.strip("json")
        return gpt_response
            
    except openai.error.APIError as e:
        # Handle API error here, e.g. retry or log
        print(f"OpenAI API returned an API Error: {e} for comment {comment_id}")
        return({'error':e})

    except openai.error.AuthenticationError as e:
        # Handle Authentication error here, e.g. invalid API key
        print(f"OpenAI API returned an Authentication Error: {e} for comment {comment_id}")
        return({'error':e})

    except openai.error.APIConnectionError as e:
        # Handle connection error here
        print(f"Failed to connect to OpenAI API: {e} for comment {comment_id}")
        return({'error':e})

    except openai.error.InvalidRequestError as e:
        # Handle connection error here
        print(f"Invalid Request Error: {e} for comment {comment_id}")
        return({'error':e})

    except openai.error.RateLimitError as e:
        # Handle rate limit error
        print(f"OpenAI API request exceeded rate limit: {e} for comment {comment_id}")
        return({'error':e})

    except openai.error.ServiceUnavailableError as e:
        # Handle Service Unavailable error
        print(f"Service Unavailable: {e} for comment {comment_id}")
        return({'error':e})

    except openai.error.Timeout as e:
        # Handle request timeout
        print(f"Request timed out: {e} for comment {comment_id}")
        return({'error':e})

def translate_comment(comment_id, comment):
    translation_prompt = """Translate this comment delineated by triple back ticks into english and return the translation within
                        single quotes. """
    full_translation_prompt = translation_prompt + " ```{}```".format(comment)
    lang4 = modelType("lang4")
    translation = call_azure_openai(comment_id, full_translation_prompt, lang4)
    return translation

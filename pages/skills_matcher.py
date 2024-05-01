import dash
import json
import os 
import random
import pandas as pd 
import numpy as np
import requests
import yaml 
import sys
from dash import dcc, html, Input, Output, State, ALL, callback_context, dash_table, register_page, callback
# sys.path.append(os.pardir)
# sys.path.append(os.path.join( os.pardir))
import utils.plotting as plotting
from utils.utils_dash import load_job_dict, _load_target_job_options, create_adult, create_kid, list_ordinals
from utils.AzureStorageManager import AzureBlobStorageManager
from utils.load_creds import load_creds
from io import StringIO


PAGE_NAME = 'Skills Matcher'
PAGE_NUMBER = 5

register_page(__name__, path='/skills-matcher', name=PAGE_NAME)

TEST_FILE = os.path.join('example_data', 'DASH_exports_combined_New-Castle-County_30-adult_5-child_2-child_EDU+CODES.csv')
creds = load_creds()
azure_manager = AzureBlobStorageManager(connection_str=creds['azure']['conn-str'],
                                        container_name=creds['azure']['container-name-1'])
if not os.path.isfile(TEST_FILE): 
    downloaded_blob = azure_manager.container_client.download_blob(os.path.basename(TEST_FILE), encoding='utf-8')
    df = StringIO(downloaded_blob.readall(), low_memory=False)
else: 
    df = pd.read_csv(TEST_FILE)

RAND_TEST = True # print the random state to show
RAND_RIG = True # rig randomness to pre-approved state
approved_seeds = [580319, 151581, 869597, -181500, 940268, 11260, -211808, -355837]


save_request, save_response = False, False
example_sm_request = os.path.join('example_data', 'SubmitSkills_example_request.json')
example_sm_response = os.path.join('example_data', 'SubmitSkills_example_response.json')
if not os.path.isfile(example_sm_request): 
    save_request = True
if not os.path.isfile(example_sm_response): 
    save_response = True

## Load api credentials  
with open(os.path.join( 'creds', 'api_info.yaml'), 'r') as file: 
    CREDS = yaml.safe_load(file)

### Dynamically create HTML divs with questions from question-answer key:  
fp_skill_list = os.path.join('example_data','GetSkills_Response.json')
with open(fp_skill_list, 'r') as file: 
    skill_list = json.load(file)

levels = ["Beginner", "Basic", "Skilled", "Advanced", "Expert"]

# submit_state_storage =[] # for tracking question ids and values to pass into the submit callback function  
# Replaced with pattern matching callback

skills_matcher_divs = [html.H4("Compare job recommendations based on your answers below:")]
for n,d in enumerate(skill_list['Skills']):

    # Set up option labels and values 
    option_labels = [f"({level}): {description}" if description != "" else f"({level})"
                     for level, description in 
                     zip(levels, (d['AnchorFirst'], d['AnchorSecond'], d['AnchorThrid'], d['AnchorFourth'], d['AnchorLast']))]
    option_values = [d['DataPoint20'], d['DataPoint35'], d['DataPoint50'], d['DataPoint65'], d['DataPoint80']]

    # Create div for the question
    question_div = html.Div([
    html.Label(f"""{n+1}. {d['ElementName']}: {d['Question']}"""),
    dcc.RadioItems(
        id={'type':'question', 'index':n+1}, 
        options=[
            {'label':label, 
             'value':value} for label, value in zip(option_labels, option_values)
        ],
    )])

    # Add to main div 
    skills_matcher_divs.append(question_div)
    skills_matcher_divs.append(html.Br())

    # Add State objects for submit callback (replace with pattern matching callback)

layout = html.Div([
    html.H1("Skills Matcher"),
    html.Div(skills_matcher_divs, className='four columns'), 
    html.Div([

    # Plot/Tab 1 
    dcc.Graph(id='plot-1-output-2'),

    # Plot/Tab 2 (Multi-Tab)
    html.Div(id='plot-2-multi-tab-container-2'), # Empty div gets Tab elements added on submit   

    html.Label('Limit max number of suggested jobs to display'),
    dcc.Dropdown(options=[i for i in range(1,11)] + ["No Limit"],value='No Limit', 
                 id='max-jobs-display'),
    html.Button('Randomize Answers', id='random-button', n_clicks=0), 
    html.Button('Submit Skills', id='submit-button-skills', n_clicks=0),
    html.Div([html.Button('Maximize Answers', id='max-button', n_clicks=0)], hidden=True), 
    html.Div(id='recommended-jobs-table-div'), 
    ], className='six columns')


        
])


## --- CALLBACKS ----- ## 
@callback(
    Output({"type":"question", "index":ALL}, 'value'),
    [Input('random-button', 'n_clicks'), 
     Input('max-button', 'n_clicks')], 
    State({"type":"question", "index":ALL}, 'options'), 

)
def change_answers(n_clicks_rand, n_clicks_max, *values): 

    if n_clicks_rand > 0: 
        options = callback_context.states_list[0] # contains the options for each question 

        ## For debugging/viewing schemas
        # with open('demo_state.json', 'w') as file: 
        #     json.dump(options, file, indent=4)

        # with open('demo_output.json', 'w') as file: 
        #     json.dump(callback_context.outputs_list, file, indent=4)

        if RAND_TEST: 
            rand_seed = random.choice(approved_seeds) if RAND_RIG else random.randint(0,123415135)
            random.seed(a=rand_seed) 
            print("Random Seed: " + str(rand_seed))

        values = [random.choice(opt['value'])['value'] for opt in options]

        return values
    
    elif n_clicks_max > 0:
        options = callback_context.states_list[0] 
        values = [opt['value'][-1]['value'] for opt in options]
        return values

    else: 
        n_outputs = len(callback_context.outputs_list) # need to provide default values to avoid callback error 
        return [None for n in range(n_outputs)] 


### JSON API request but send to datatable 
@callback(
    Output('recommended-jobs-table-div', 'children'),
    [Input('submit-button-skills', 'n_clicks')],
    # submit_state_storage
    [State({'type':'question', 'index':ALL}, 'value'), 
     State('max-jobs-display', 'value')]
)
def send_get_request(n_clicks, *values):
    if n_clicks > 0:
        if all(values[0]): 
            # Request body needs ElementId (question id) and DataValue (answer id == chosen DataPoint == value in callback)
            answers = []
            for qa_dict, answer in zip(skill_list['Skills'], values[0]): 
                answers.append({"ElementId":qa_dict['ElementId'], "DataValue":answer})

            request_body = {'SKAValueList':answers} # request body to Skills Matcher

            if save_request:
               with open(example_sm_request, 'w') as file: 
                   json.dump(request_body, file, indent=4)
                   print('Saved request as example')

            # Make request 
            user_id = CREDS['career-onestop']['user-id']
            api_token = CREDS['career-onestop']['token-key']
            headers = CREDS['career-onestop']['headers']
            url = f"https://api.careeronestop.org/v1/skillsmatcher/{user_id}"           
            params = {
                'API Token':api_token, 
                'userId':user_id, 
                'body':request_body, 
                # sortColumn
                # sortOrder
                # eduFilterValue -- will use this in final app
                }
            
            response = requests.post(url=url,params=params,headers=headers, json=request_body) 
            if response.status_code == 200: 
                response_json = response.json()
                if save_response: 
                    with open(example_sm_response, 'w') as file: 
                        json.dump(response_json, file, indent=4)
                        print("Saved example response")

                recommended_job_dicts = response_json['SKARankList']

                df = pd.DataFrame(recommended_job_dicts,columns=['OnetCode','Rank', 'OccupationTitle', 'TypicalEducation', 'AnnualWages','Outlook'] )\
                        .rename({'OnetCode':'OCC_CODE', 
                        'OccupationTitle':'Occupation Title',
                        'Rank':'Match Rank','TypicalEducation':"Typical Education", "AnnualWages":"Annual Wages"}, axis=1)
                df.to_csv(os.path.join('example_data', 'skills-matcher-results-latest.csv'), index=False)

                fp = os.path.join('example_data', 'DASH_exports_combined_New-Castle-County_30-adult_5-child_2-child_EDU+CODES.csv')
                df_DE_baseline_jobs = pd.read_csv(fp)
                df_DE_baseline_jobs = df_DE_baseline_jobs['OCC_CODE'].unique()

                dff = df[df['OCC_CODE'].isin(df_DE_baseline_jobs)].reset_index(drop=True)
                print('Recommended Jobs with matches in DE example data: ')
                print(dff.shape)
                print('Warning: changing Rank vs Skills Matcher Original:')
                dff['Match Rank'] = dff.index + 1

                max_jobs = values[1] 
                if max_jobs != 'No Limit':
                    dff = dff[dff['Match Rank'] <= max_jobs
]
                data_table = dash_table.DataTable(
                                id='recommended-jobs-table',
                                data=dff.to_dict('records'), 
                                row_selectable='multi', 
                                hidden_columns=['OCC_CODE'], 
                                sort_action='native', 
                                sort_mode='multi', 
                                style_cell={'whiteSpace': 'normal','textOverflow': 'ellipsis', 'width':'20%'}, 
                                css=[{"selector": ".show-hide", "rule": "display: none"}]
                                # style_cell_conditional=[
                                #     {'if':{'column_id':'Occupation Title'}, 
                                #      'width':'10%'}]
                    )
                return data_table
            else: 
                return json.dumps(f"Non-200 status code: {response.status_code}")
        else: 
            return "Please answer all questions before hitting submit."


## Callback to obtain selected jobs from the data-table (up to three) as State, filter the global dataframe, and 
@callback(
    Output('plot-1-output-2', 'figure'), 
    [Input('recommended-jobs-table', 'derived_virtual_data'),
     Input('recommended-jobs-table', 'derived_virtual_selected_rows')]  
)
def retrieve_selected_row(rows, selected_rows): 
    if rows is not None and selected_rows != []: 
 
        colors = plotting.general_color_palette

        selected_careers = [rows[i]['OCC_CODE'] for i in selected_rows]
        # print(selected_careers)
        data_selected = df[df['OCC_CODE'].isin(selected_careers)]
        # print(data_selected)
        print(data_selected.shape)

        color_map = dict(zip(data_selected['CareerPath'].unique(), colors))

        # fig = plotting.plot_tab1(data_selected, color_map=color_map, title='Net Resources Over Time for Selected Jobs (New Castle County, Chosen Profile)')
        fig = plotting.plot_multi(df=data_selected, 
                                  x_var='Year', 
                                  y_var='NetResources',
                                  group_var='CareerPath', 
                                  color_map=color_map)
        return fig
    else:
        # Return an empty figure when the button is not clicked
        return {}
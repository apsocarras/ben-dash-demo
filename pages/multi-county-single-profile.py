import dash
from dash import dcc, html, Dash, html, Input, Output, callback, register_page, ALL, MATCH, callback_context
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import us 
import os
import json
import sys
import pandas as pd 
# sys.path.append(os.pardir)
# sys.path.append(os.path.join( os.pardir))
import utils.plotting as plotting
from utils.load_creds import load_creds
from utils.BeneficiaryProfile import Beneficiary
from utils.utils_dash import create_adult, create_kid, list_ordinals, extract_ben_dict
from utils.AzureStorageManager import AzureBlobStorageManager

from io import StringIO


PAGE_NAME = "Compare Counties"
PAGE_NUMBER = 3

TEST_MODE = True
use_azure = False
if TEST_MODE:  
    example_data_fp = os.path.join('example_data', 'all-counties_three-profile_example.csv')
    if os.path.isfile(example_data_fp) and not use_azure: 
        df_example = pd.read_csv(example_data_fp)
    else: 
        creds = load_creds()
        azure_manager = AzureBlobStorageManager(container_name=creds['azure']['container-name-2'], 
                                        connection_str=creds['azure']['conn-str'])  
        
        downloaded_blob = azure_manager.container_client.download_blob(os.path.basename(example_data_fp), encoding='utf-8')        
        df_example = pd.read_csv(StringIO(downloaded_blob.readall()), low_memory=False)
        print('Downloaded test csv from azure')

    TEST_MODE_DIV = f'TEST_MODE: Using example data file {example_data_fp}: '
    for profile in df_example['BeneficiaryProfile'].unique(): 
        TEST_MODE_DIV += f'\n({profile})'

else: 
    TEST_MODE_DIV = ''
    df_global = pd.DataFrame()

register_page(__name__, name = PAGE_NAME, path="/multi-county-single-profile")

## Write dashboard page to take in inputs for the yaml, generates a dict, then a Beneficiary Object, then creates the Net Resources vs Income plot  

### ---------------------------------------------------------------- ### 
# Starting Parameters  
# CREDS = load_creds() # load creds 

# State 
us_state_options = [{'label':s.name, 'value':s.abbr} for s in us.states.STATES]
us_state_options.insert(8, {'label':'District of Columbia', 'value':'DC'})

default_state_value = 'DE'

# County
with open('counties.json', 'r') as file: 
    counties_dict = json.load(file)
default_counties = ['New Castle County', 'Kent County', 'Sussex County']

# Family parameters  
default_n_adults = 1
default_age_adult = 30
default_n_kids = 1
# default_age_kid = 8 # included in create_kid 
    
# Benefit program selection 
default_program_selection = "All Programs"

default_fig = px.scatter({'a':[1,24,5,6,53], 'b':[1,3,52,56,67]},
    x="a",
    y="b",
    size_max=60,
    )
# default_fig = None


### ---------------------------------------------------------------- ### 
# Initialize app and set layout    

adult_state_storage = [] # TO-DO: replace with pattern-matching state in display_benefit_options() callback


# Define the layout of the app
layout = html.Div([
        
        html.Div([

            html.Div(TEST_MODE_DIV), 

            html.H2('Comparing US Counties:'),

            # State / County Select
            html.Div([
                html.Div([
                    html.Label(f"County #{n}"),
                    dcc.Dropdown(us_state_options, value=default_state_value, 
                        id={'type':'state-dropdown','index':n}),
                    dcc.Dropdown(options=[], value=default_counties[n-1],
                        id={'type':'county-dropdown', 'index':n}),
                    html.Br()
                    ]) for n in range(1,4)], 
                    id={'type':'state-county-select', 'index':PAGE_NUMBER}), 

            html.H3('Beneficiary Profile:'),

            ## Number of Adults (1 to 6)
            html.Label("Number of Adults (1 to 6)"),
            dcc.Dropdown(options=list(range(1,7)), value=default_n_adults, id=f'n-adults-dropdown-{PAGE_NUMBER}'),
            html.Div(id=f'n-adults-{PAGE_NUMBER}'),
            html.Br(),

            ## Number of Children (0 to 6)
            html.Label("Number of Children (0 to 6)"),
            dcc.Dropdown(options=list(range(0,7)), value=default_n_kids, id=f'n-kids-dropdown-{PAGE_NUMBER}'),
            html.Div(id=f'n-kids-{PAGE_NUMBER}'),
            html.Br(),

            ## Public Assistance Dropdown 
            html.Label("Public Assistance"),
            dcc.Dropdown(options=['All Programs', 'No Programs', 'Select Custom List'],
                        value=default_program_selection, id=f'public-assistance-dropdown-{PAGE_NUMBER}'),
            html.Br(),
            html.Div(id=f'public-assistance-{PAGE_NUMBER}'),

            ## Submit Form
            html.Div([
                html.Button(id={'type':'submit-button', 'index':PAGE_NUMBER}, n_clicks=0, children='Submit'), 
            ], style={"text-align":"center"}),
 
        ], id={'type':'select-bar', 'index':PAGE_NUMBER}, className='three columns'), 
        
        html.Div([
        # Multi-View Plot 
        dcc.Graph(id={'type':'plot-multi-view', 'index':PAGE_NUMBER}),
        # Single-View Tabs 
        html.Div(id={'type':'plot-single-view-div', 'index':PAGE_NUMBER}),
            ], id='reveal-div', hidden=True, className='seven columns')

    ])

 ## ---- CALLBACKS ---- ##

## County Dropdown
@callback(
    Output({'type':'county-dropdown', 'index':MATCH}, 'options'), 
    [Input({'type':'state-dropdown', 'index':MATCH}, 'value')]
)
def update_county_options(chosen_state_value): 
    
    global counties_dict

    if chosen_state_value is None: 
        return []
    
    counties_in_state = counties_dict[chosen_state_value]
    return [{'label':county, 'value':county} for county in counties_in_state]


## Adult Dropdown Content
@callback(
    Output(f'n-adults-{PAGE_NUMBER}', 'children'), 
    [Input(f'n-adults-dropdown-{PAGE_NUMBER}', 'value')]
)

def add_adults(n:int): 
           
    if n is None: 
        return []
    
    global adult_state_storage 

    adult_state_storage = [] # Don't want infinite store 

    adult_divs = [html.Br()]
    for i in range(1, n+1): 
        # adult_divs.append(html.Div(str(i)))       # Comments are to display on page for debugging
        adult_divs.append(create_adult(i, default_age=default_age_adult))
        if i < n: # separate adult divs before the last one 
            adult_divs.append(html.Br())

   
        adult_state_storage.extend([State({'type':'adult-div','index':n}, 'value'),
                                    State({'type':'disabilities-adult-checkbox', 'index':n}, 'value')])

        # adult_divs.append(str(adult_state_storage))
    # adult_divs.append(str(adult_state_storage))

    return adult_divs

## Child Dropdown Content
@callback(
    Output(f'n-kids-{PAGE_NUMBER}', 'children'),
    [Input(f'n-kids-dropdown-{PAGE_NUMBER}', 'value')]
)
def add_kids(n:int): 

    global n_kids 

    if n is None: 
        return []
    
    kid_divs = [html.Br()]
    for i in range(1, n+1): 
        kid_divs.append(create_kid(i)) 
        if i < n:
            kid_divs.append(html.Br())

    n_kids = n
    return kid_divs


## Benefits Programs Dropdown
@callback(
    Output(f'public-assistance-{PAGE_NUMBER}', 'children'), 
    [Input(f'public-assistance-dropdown-{PAGE_NUMBER}', 'value')], 
    adult_state_storage
)
def display_benefit_options(value, *values): 
    ## TO-DO: If you change the number of adults, this function should be refreshed and the div content in the benefits section changed
    if value is None: 
        return []
    
    if value == 'All Programs':

        div_content = [
            
            html.Label("Has anyone in the home ever received SSI?"),
            dcc.RadioItems(
                id={'type':'anyone-SSI', 'index':1}, 
                options=[{'label':'Yes', "value":"Yes"}, {'label':'No', "value":"No"}], 
                value="No"
            ), 
            html.Label("Amount spent ($) per month on specialized equipment or services that enable household member(s) with disabilities to work"),
            dcc.Input(id={'type':'disab-work-expenses', 'index':1}, value=0, type='number'), # Only one, but pattern matching ensures callback selects only when it exists
            html.Br(), html.Br()
            ]
        
        global adult_state_storage # should be passed in as values but unsure why that's not working        
        # for state in values: 
        for state in adult_state_storage: # TO-DO: check why *values not passed correctly
            if 'disabilities-adult' in state.component_id['type']:
                nth_adult = state.component_id['index'] 
                div_content.extend([
                    html.Label(f"Amount {list_ordinals()[nth_adult - 1]} adult receives ($) per month in SSDI payments: "), 
                    dcc.Input(id={'type':'ssdi-adult', 'index':nth_adult}, value=0, type='number'), 
                    html.Div('Do not include auxiliary benefits that are for children, spouses, or other family members.'),
                    html.Br()
                ])

    # elif value == 'No Programs':
    
    # elif value == 'Select Custom List':

    return div_content

@callback( 
    Output('county-comparison-beneficiary-store', 'data'), 
    # Output({'type':'plot-output-div', 'index':PAGE_NUMBER}, 'children'),
    # Output({"type":"plot-multi-view", 'index':PAGE_NUMBER}, 'figure'), 
    [Input({'type':'submit-button', 'index':PAGE_NUMBER}, 'n_clicks')], 

    [
     ## Family Parameters
     # Adults 
     State({'type':'age-input-adult', 'index':ALL}, 'value'), 
     State({'type':'married-adult-checkbox', 'index':ALL}, 'value'),  
     State({'type':'disabilities-adult-checkbox', 'index':ALL}, 'value'),  
     State({'type':'ssdi-adult', 'index':ALL}, 'value'), 
     # Children
     State({'type':'age-input-kid', 'index':ALL}, 'value'),
     State({'type':'disabilities-kid-checkbox', 'index':ALL}, 'value'),
     
     # (WIP) Program/Benefits selections
     State({'type':'anyone-SSI', 'index':ALL}, 'value'),
     State({'type':'disab-work-expenses', 'index':ALL}, 'value'), 
     
     State({'type':'state-dropdown', 'index':ALL}, 'value'), 
     State({'type':'county-dropdown', 'index':ALL}, 'value'),

     ]
)

def extract_beneficiary_information(n_clicks, *values): 
    """Store Beneficiary Profile State on submit click."""
    if n_clicks > 0: 
        ben_dict = extract_ben_dict(callback_context.states_list)   
        return ben_dict
    else: 
        return {} # TO-DO thinking about dataframe scope
        # current_profile = Beneficiary(project_name='user', **ben_dict)
        # current_profile.save_project(overwrite=True)
        # current_profile.run_applyBenefitsCalculator()
        # df = pd.read_csv(current_profile.output_path)


# @callback(        
# )
# TO-DO: def run_on_submit(): 
#     """Read input/beneficiary state from store, run calculations, and store data in temporary database table"""
    #   # dcc.Store() not large enough
    #   # might run for all counties and keep cached?   

@callback( 
    Output({'type':'plot-multi-view', 'index':PAGE_NUMBER}, 'figure'),
    [Input({'type':'submit-button', 'index':PAGE_NUMBER}, 'n_clicks'), 
     Input('county-comparison-beneficiary-store', 'data')] # Not working when store passed in through state parameter
     # Store only changes when button is clicked so this doesn't create more callbacks
)
def update_plot_multi_view(n_clicks, data):
    """Update Plot Multi View On Click"""
    if n_clicks > 0: 
        print(data)
        if TEST_MODE: 
            df = df_example.copy()  # In  production we will be reading from a pre-generated database table.
            # This block is awkward way to filter our example CSV by profile. 
            # Ordinarily there will be just one table for one profile.
            df = df[df['state_county'].isin(data['locations'])]
            ben_profile = Beneficiary(project_name='county-comparison', **data)
            chosen_profile = ben_profile.non_default().copy()
            chosen_profile.pop('locations')
            chosen_profile_str = json.dumps(chosen_profile)

            df = df[df['BeneficiaryProfile'] == chosen_profile_str]

        else: 
            return "Non-test-mode WIP"

        color_map = dict(zip(data['locations'], plotting.general_color_palette))

        multi_view_fig = plotting.plot_multi(df=df, 
                                    x_var='income', 
                                    y_var='NetResources',
                                    group_var='state_county', 
                                    color_map=color_map, 
                                    title=f'Net Resources vs. Income Bracket, County Comparison')
        return multi_view_fig 
    
    else:
        return {} 
    
@callback( 
    Output({'type':'plot-single-view-div', 'index':PAGE_NUMBER}, 'children'),
    [Input({'type':'submit-button', 'index':PAGE_NUMBER}, 'n_clicks'), 
    Input('county-comparison-beneficiary-store', 'data')],
    prevent_initial_call=True,
    )
def render_single_view_tabs(n_clicks, data):
    """Renders the single view tabs based on the selected locations"""
    if n_clicks > 0: 
         return [
            dcc.Tabs(id="plot-single-view-tabs", value=data['locations'][0], children=[
                dcc.Tab(label=data['locations'][0], value=data['locations'][0]),
                dcc.Tab(label=data['locations'][1], value=data['locations'][1]),
                dcc.Tab(label=data['locations'][2], value=data['locations'][2]),
            ]),
        html.Div(id={'type':"plot-single-view-chosen-tab", 'index':PAGE_NUMBER})
        ]


# Load the content of the tabs (based on selected tab)
@callback(
    Output({'type':'plot-single-view-chosen-tab', 'index':PAGE_NUMBER}, 'children'),
    [Input('plot-single-view-tabs', 'value')],
    [State({'type':'county-dropdown', 'index':ALL}, 'value'), 
     State({'type':'state-dropdown', 'index':ALL}, 'value'),
     State('county-comparison-beneficiary-store', 'data')] # wait why is passing store as state working here? 
)
def update_single_view_tabs(tab, *values):
    if TEST_MODE: 
        df = df_example.copy()
        ben_profile = Beneficiary(project_name='user', **values[-1]) 
        chosen_profile = ben_profile.non_default().copy()
        chosen_profile.pop('locations')
        chosen_profile_str = json.dumps(chosen_profile) 

        df = df[df['BeneficiaryProfile'] == chosen_profile_str]

        print(ben_profile.non_default())

    locations = [", ".join(tup) for tup in zip(values[0], values[1])]
    color_map = dict(zip(locations, plotting.general_color_palette))

    fig = plotting.plot_single_profile(
        df = df[df['state_county'] == tab], 
        x_var='income', 
        y_var='NetResources',
        curve_color=color_map[tab], 
        curve_name=f'Net Resources ({tab.split(",")[0]})', 
        title=''

    )

    return dcc.Graph(figure=fig) 
    

@callback( 
    Output('reveal-div', 'style'),
    [Input({'type':'plot-multi-view', 'index':PAGE_NUMBER}, 'figure')]
)
def reveal_output_div(figure):
    if figure is not None and 'data' in figure: 
        if figure['data']:
            return {"display":"block"}
    else: 
        return {'display':'none'}



## Save the yaml and run from there, or pass as command line args to R script? 
## When running the R script, do you save to csv file or can you read in directly to python?
    ## When hosted online this would likely be a temporary table in a database 
## Do you run for all locations and just store dataframe in the background? Only refresh if the beneficiary profile changes? 

# return json.dumps(current_profile.Profile)



## TO-DO: 
# Move plots to the right of the selection column 

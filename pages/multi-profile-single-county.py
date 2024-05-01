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
sys.path.append(os.pardir)
sys.path.append(os.path.join( os.pardir))
import utils.plotting as plotting
from utils.BeneficiaryProfile import Beneficiary
from utils.utils_dash import load_job_dict, _load_target_job_options, create_adult, create_kid, list_ordinals



PAGE_NAME = "View A Particular County"
PAGE_NUMBER = 4

page_path = "/view-county"
page_registry_name = 'pages' + '.' + page_path[1:]
dash.register_page(__name__, name=PAGE_NAME, path=page_path)
# print(list(dash.page_registry.keys()))
# PAGE_NUMBER = list(dash.page_registry.keys()).index(page_registry_name) 
TEST_MODE = True
if TEST_MODE:  
    example_data_fp = os.path.join('example_data', 'all-counties_three-profile_example.csv')
    df_example = pd.read_csv(example_data_fp)
    TEST_MODE_DIV = f'TEST_MODE: Using example data file {example_data_fp}: '
    for profile in df_example['BeneficiaryProfile'].unique(): 
        TEST_MODE_DIV += f'\n({profile})'
else: 
    TEST_MODE_DIV = ''
    df_global = pd.DataFrame()

register_page(__name__, name = PAGE_NAME, path="/multi-profile-single-county")

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
default_age_adult = None
default_n_kids = 0
# default_age_kid = 8 # included in create_kid 
    
# Benefit program selection 
default_program_selection = "All Programs"


### ---------------------------------------------------------------- ### 
# Initialize app and set layout    

# Define the layout of the app
layout = html.Div([

    dcc.Store(id={'type':'beneficiary-store', 'index':1}, data = {}),
    dcc.Store(id={'type':'beneficiary-store', 'index':2}, data = {}),
    dcc.Store(id={'type':'beneficiary-store', 'index':3}, data = {}),

    html.Div(TEST_MODE_DIV), 

    html.H2('Compare Beneficiary Profiles'),

    # Location & View Select
            html.Div(
                children=[
                    html.Div(
                        style={'display': 'flex'}, 
                        children=[
                                html.Div(
                                style={'margin-left': '10px', 'margin-right': '10px', 'flex-shrink': '0', 'vertical-align':'top'}, 
                                children=[  # plots
                                    html.Div([ 
                                        dcc.Graph(id={'type':'plot-multi-view', 'index':PAGE_NUMBER})
                                        ], id={'type':'plot-multi-view-div', 'index':PAGE_NUMBER}, hidden=False
                                        ), 
                                    html.Div(id={'type':'plot-single-view-div', 'index':PAGE_NUMBER}, hidden=True, 
                                             children=[
                                                 dcc.Tabs(id="plot-single-view-tabs", value="Beneficiary #1", 
                                                    children=[
                                                    dcc.Tab(label='Beneficiary #1', value='Beneficiary #1'),
                                                    dcc.Tab(label='Beneficiary #2', value='Beneficiary #2'),
                                                    dcc.Tab(label='Beneficiary #3', value='Beneficiary #3'),
                                                        ]), 
                                                html.Div(id={'type':"plot-single-view-chosen-tab", 'index':PAGE_NUMBER}, 
                                                    children=[
                                                        dcc.Graph({'type':'plot-single-view', 'index':PAGE_NUMBER})
                                            ])
                                        ]),
                                    ],
                            className='nine columns'),
                            html.Div(
                                style={'width': '20%'},  
                                children=[
                                    html.Label('Select a County:'), 
                                    dcc.Dropdown(
                                        options=us_state_options,
                                        id=f'state-dropdown-{PAGE_NUMBER}',
                                        value=default_state_value
                                    ),
                                    dcc.Dropdown(
                                        options=[],
                                        id=f'county-dropdown-{PAGE_NUMBER}',
                                        value=default_counties[0]
                                    ),
                                    html.Br(),
                                    dcc.Checklist(options=['Pre-load for all counties'],value=['Pre-load for all counties'], inline=True, id='county-preload-checklist'),
                                    html.Div('Required to see national averages.', style={'margin-left':'5px', 'font-style':'italic'}),
                                    html.Br(),
                                    html.Button(id={'type':'submit-button', 'index':PAGE_NUMBER}, 
                                                n_clicks=0,children='Submit'),
                                    html.Br(),
                                    html.Br(),
                                    html.Div(id='toggle-view-div', hidden=True, 
                                        children=[
                                            html.Label('Toggle View:'),
                                            dcc.RadioItems(
                                                options=[
                                                    {'label': 'All Profiles', 'value': 'All Profiles'},
                                                    {'label': 'Single Profile', 'value': 'Single Profile'},
                                                ],
                                                id="view-toggle",
                                                value='All Profiles',
                                                labelStyle={'display': 'block'}  # Display radio items vertically
                                        ),
                                    ]),
                                ]
                            ),
                        ]
                    )
                ]
            ),

    html.Br(), 

    ## Profile Fill Out
    # html.H3('Enter 3 Beneficiary Profiles:'),
    html.Div(id='beneficiary-profile-selection', 
            children=[
            html.Div(id='beneficiary-columns-div', 
                children=[
                html.Div(id={'type':'beneficiary-select-div', 'index':n}, style={'width': '30%', 'display': 'inline-block', 'vertical-align':'top'}, 
                    children=[
                    html.H4(f'Beneficiary #{n}'),
                    html.Label("Number of Adults (1 to 6)"),
                    dcc.Dropdown(options=list(range(1,7)), value=default_n_adults, id={'type':f'n-adults-dropdown-{PAGE_NUMBER}', 'index':n}),
                    html.Div(id={'type':f'n-adults-{PAGE_NUMBER}', 'index':n}),
                    html.Br(),
                    html.Label("Number of Children (0 to 6)"),
                    dcc.Dropdown(options=list(range(0,7)), value=default_n_kids, id={'type':f'n-kids-dropdown-{PAGE_NUMBER}', 'index':n}),
                    html.Div(id={'type':f'n-kids-{PAGE_NUMBER}', 'index':n}),
                    html.Br(),
                    html.Label("Benefits Programs"),
                    dcc.Dropdown(options=['All Programs', 'No Programs', 'Select Custom List'],
                    value=default_program_selection, id={'type':f'public-assistance-dropdown-{PAGE_NUMBER}', 'index':n}),
                    html.Br(),
                    html.Div(id={'type':f'public-assistance-{PAGE_NUMBER}', 'index':n}),
                            ]) 
                    for n in range(1,4)
            ]),
        ])
    ])

 ## ---- CALLBACKS ---- ##

## County Dropdown
@callback(
    Output(f'county-dropdown-{PAGE_NUMBER}', 'options'), 
    [Input(f'state-dropdown-{PAGE_NUMBER}', 'value')]
)
def update_county_options(chosen_state_value): 
    
    global counties_dict

    if chosen_state_value is None: 
        return []
    
    counties_in_state = counties_dict[chosen_state_value]
    return [{'label':county, 'value':county} for county in counties_in_state]


## Adult Dropdown Content
@callback(
    Output({'type':f'n-adults-{PAGE_NUMBER}', 'index':MATCH}, 'children'),
    [Input({'type':f'n-adults-dropdown-{PAGE_NUMBER}', 'index':MATCH}, 'value')],
)

def add_adults(n:int): 
           
    if n is None: 
        return [html.Br()]

    adult_divs = [html.Br()]
    for i in range(1, n+1): 
        # adult_divs.append(html.Div(str(i)))       # Comments are to display on page for debugging
        adult_divs.append(create_adult(i, default_age=default_age_adult))
        if i < n: # separate adult divs before the last one 
            adult_divs.append(html.Br())

    return adult_divs



## Child Dropdown Content
@callback(
    Output({'type':f'n-kids-{PAGE_NUMBER}', 'index':MATCH}, 'children'),
    [Input({'type':f'n-kids-dropdown-{PAGE_NUMBER}', 'index':MATCH}, 'value')],
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


## PLOTS 

# Reveal View Toggle 
@callback(
    Output('toggle-view-div', 'style'),
    [Input({'type':'submit-button', 'index':PAGE_NUMBER}, 'n_clicks')],
    
)
def reveal_view_toggle(n_clicks ): 
    if n_clicks > 0: 
        return {'display':'block'}
    else:
        return  {'display':'none'}

# Toggle View Options    
@callback(
    Output({'type':'plot-multi-view-div', 'index':PAGE_NUMBER}, 'style'),
    [Input("view-toggle", "value")] 
)
def toggle_multi_view(value): 
    """Change plot view from radio button."""

    if value == 'All Profiles':
        return {'display':'block'}
    else: 
        return {'display':'none'} 
    
@callback(
    Output({'type':'plot-single-view-div', 'index':PAGE_NUMBER}, 'style'),
    [Input("view-toggle", "value")] 
)
def toggle_single_view(value):
    """Change plot view from radio button."""

    if value == 'Single Profile':
        return {'display':'block'}
    else: 
        return {'display':'none'}

@callback(
    
    [Output({'type':'plot-multi-view', 'index':PAGE_NUMBER}, 'figure'),
     Output({'type':'plot-single-view', 'index':PAGE_NUMBER}, 'figure')],

    [Input({'type':'submit-button', 'index':PAGE_NUMBER}, 'n_clicks')],
    
    [   ### State and County States
        State('county-preload-checklist', 'value'),
        State(f'state-dropdown-{PAGE_NUMBER}', 'value'), 
        State(f'county-dropdown-{PAGE_NUMBER}', 'value'), 

        ### Past Beneficiary States     
        State({'type':'beneficiary-store', 'index':ALL}, 'data'), 

        ### Current Beneficiary States 
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

        ### Current Figures 
        ## We need to return these if the figures don't need to change 
        State({'type':'plot-multi-view', 'index':PAGE_NUMBER}, 'figure'),
        State({'type':'plot-single-view', 'index':PAGE_NUMBER}, 'figure')
  ], 
  prevent_initial_call=True 
)
def rerun_calc(n_clicks, *values):  
    """Check for changes in beneficiary profiles; re-run script for those which changed; update temporary db table."""
    
    if n_clicks > 0: 
        if TEST_MODE:
            

            multi_view_fig, single_view_fig = go.Figure(), go.Figure()

            global df_example 
            df = df_example.copy()
            df = df[(df['stateAbbrev'] == values[1]) & (df['countyortownName'] == values[2])]


            color_map = dict(zip((df['BeneficiaryProfile'].unique()), plotting.general_color_palette))

            multi_view_fig = plotting.plot_multi(
                df=df, 
                x_var='income', 
                y_var='NetResources', 
                group_var='BeneficiaryProfile', 
                title=f'Net Resources in ' + values[2] +  ", " + values[1],
                color_map=color_map, 
            )

            # # TO-DO: Read state of first beneficiary store object  
            chosen_prof = df['BeneficiaryProfile'].iloc[0]

            dff=df[df['BeneficiaryProfile'] == chosen_prof]

            single_view_fig = plotting.plot_single_profile( # Pre-loads figure of first beneficiary profile into the first tab  
                df=dff, 
                x_var='income', 
                y_var='NetResources',
                curve_color=plotting.general_color_palette[0], 
                curve_name='Net Resources', 
                title='', 
                ben_profile_text=None, 

            )

            return multi_view_fig, single_view_fig
        
        else: 

            # Check stores for prev config of each beneficiary 
            # Check current element states vs store to see which beneficiaries changed 
            # Rerun script and re-load table for each changed profile  

            return None, None
    
    return None, None 




## TO-DO:
# Add callback to render and populate tabs
# Pre-display tabs





# 
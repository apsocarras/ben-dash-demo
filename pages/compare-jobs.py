import dash
from dash import dcc, html, Dash, html, Input, Output, callback
from dash.dependencies import Input, Output, State
import plotly.express as px
import us 
import os
import json
import sys
import pandas as pd 
sys.path.append(os.pardir)
import utils.plotting as plotting
from utils.utils_dash import load_job_dict, _load_target_job_options, create_adult, create_kid, list_ordinals

PAGE_NAME = 'Compare Jobs'
PAGE_NUMBER = 2


page_path = "/compare-jobs"
page_registry_name = 'pages' + '.' + page_path[1:]

dash.register_page(__name__, name=PAGE_NAME, path=page_path)
# PAGE_NUMBER = list(dash.page_registry.keys()).index(page_registry_name) # ordered dict, should be consistent 
# I want page number to make certain element ids unique to a page.
# If the id is the same but index changes, then pattern matching callbacks should match across pages. 
# If I don't want that I can put the number in the id name itself. 


## Write dashboard page to take in inputs for the yaml, generates a dict, then a Beneficiary Object, then creates the plot  

TEST_MODE = True  # ONLY NEW CASTLE COUNTY, ONLY VALID FOR ONE BENEFICIARY PROFILE
TEST_FILE = os.path.join('example_data', 'DASH_exports_combined_New-Castle-County_30-adult_5-child_2-child_EDU+CODES.csv')
# These are the only job projections I have available right now
#
### ---------------------------------------------------------------- ### 
# Starting Parameters  
# CREDS = load_creds() # load creds 

if TEST_MODE: # run with only default options to match the example data 

    TEST_MODE_DIV = html.Div("TEST_MODE: Only uses projections exported from CLIFF Dashboard (30 y/o adult, 5 year-old child, 2 year-old child, all benefits programs)")

    # State 
    us_state_options = [{'label':"Delaware", 'value':"DE"}]
    # County 
    counties_dict = {"DE":["New Castle County"]}
    default_county = 'New Castle County'

    # Family parameters  
    default_n_adults = 1
    default_age_adult = 30
    default_n_kids = 0
    
    # Job selection 
    job_dict = load_job_dict(TEST_MODE)
    # Benefit program selection 
    program_selection = "All Programs"

    # data file 
    data = pd.read_csv(TEST_FILE)


else: 
    TEST_MODE_DIV = None 
    TEST_FILE = None

    # State 
    us_state_options = [{'label':s.name, 'value':s.abbr} for s in us.states.STATES]
    us_state_options.insert(8, {'label':'District of Columbia', 'value':'DC'})

    # County
    with open('counties.json', 'r') as file: 
        counties_dict = json.load(file)
    # WIP: get from Azure
    # response  = requests.get('https://benefitscliffs.blob.core.windows.net/dashboard/counties.json') # WIP -- why can I access this outside of the Dash app?
    #  if response == 200: 
    #     counties_dict  = response.json()
    # else: 
        # raise Exception('Can\'t retrieve counties')
    default_county = None

    # Family parameters  
    default_n_adults = None
    default_age_adult = 19
    default_n_kids = None
    # default_age_kid = None # parameter in create_kid
    
    # Job selection 
    job_dict = load_job_dict(TEST_MODE)

    # Benefit program selection 
    program_selection = "All Programs"

### Other Options for input
## ruleYear, Year -- leave at 2023 

### ---------------------------------------------------------------- ### 
# Initialize app and set layout    

adult_state_storage = [] # TO-DO: replace with pattern-matching state in display_benefit_options() callback

# Define the layout of the app
layout = html.Div([

    html.Div([
        TEST_MODE_DIV,
        # html.Br(),

        html.H2('Compare Jobs'),

        ## State of Residency 
        html.Label("State of Residency"),
        dcc.Dropdown(us_state_options, value=us_state_options[0]['value'], id='state-dropdown'),
        html.Div(id='missing-state'),
        html.Br(),

        ## County of Residency 
        html.Label("County of Residency"),
        dcc.Dropdown(options=[], value=default_county, id='county-dropdown'),
        html.Div(id='missing-county'),
        html.Br(),

        html.H4('Household Information:'),

        ## Number of Adults (1 to 6)
        html.Label("Number of Adults"),
        dcc.Dropdown(options=list(range(1,7)), value=default_n_adults, id='n-adults-dropdown'),
        html.Div(id='n-adults'),
        html.Br(),

        ## Number of Children (0 to 6)
        html.Label("Number of Children"),
        dcc.Dropdown(options=list(range(1,7)), value=default_n_kids, id='n-kids-dropdown'),
        html.Div(id='n-kids'),
        html.Br(),

        ## Public Assistance Dropdown 
        html.Label("Public Assistance"),
        dcc.Dropdown(options=['All Programs', 'No Programs', 'Select Custom List'],
                    value=program_selection, id='public-assistance-dropdown'),
        html.Br(),
        html.Div(id='public-assistance'),

        ## Job Selection Section: 
        html.Br(),
        html.H3("Target Occupations"),
        html.Div("Select Up to 3 Jobs by Occupation Group and Job Title"),
        html.Div([
        html.Label("Filter Jobs By Educational Requirement"),
        dcc.Dropdown(options=[
            "Less than high school diploma",
            "High school diploma or equivalent",
            "Some college, no degree",
            "Associate's degree",
            "Bachelor's degree",
            "Master's degree",
            "Doctoral or professional degree",
            ], value=[], id='education-requirement-dropdown', multi=True)], id='edu-filter-div', hidden=False),
            # Education levels taken from https://www.careeronestop.org/Developers/WebAPI/Occupation/get-occupation-details.aspx and should match our job database

        #Job 1:
        html.Br(),
        html.Label("Broad Occupation Group"),
        dcc.Dropdown(options=[{"label":k, "value":k} for k in job_dict.keys()],
                    value=None, id='broad-occupation-group1-dropdown'),
        html.Div(id='broad-occupation-group1'),
        html.Label("Target Occupation"),
        dcc.Dropdown(options=[],
                    value=None, id='target-occupation-group1-dropdown'),
        html.Div(id='target-occupation-group1'),

        # Job 2:
        html.Br(),
        html.Label("Broad Occupation Group"),
        dcc.Dropdown(options=[{"label":k, "value":k} for k in job_dict.keys()],
                    value=None, id='broad-occupation-group2-dropdown'),
        html.Div(id='broad-occupation-group2'),
        html.Label("Target Occupation"),
        dcc.Dropdown(options=[],
                    value=None, id='target-occupation-group2-dropdown'),
        html.Div(id='target-occupation-group2'),

        # Job 3:
        html.Br(),
        html.Label("Broad Occupation Group"),
        dcc.Dropdown(options=[{"label":k, "value":k} for k in job_dict.keys()],
                    value=None, id='broad-occupation-group3-dropdown'),
        html.Div(id='broad-occupation-group3'),
        html.Label("Target Occupation"),
        dcc.Dropdown(options=[],
                    value=None, id='target-occupation-group3-dropdown'),
        html.Div(id='target-occupation-group3'),
        html.Br(),
        
        ## Submit Form and Graph Output
        html.Div([
        html.Button(id='submit-button', n_clicks=0, children='Submit'),
        ], style={'text-align':'center'}),
        # # Plot/Tab 1 
        # dcc.Graph(id='plot-1-output'),

        # # Plot/Tab 2 (Multi-Tab)
        # html.Div(id='plot-2-multi-tab-container') # Empty div gets Tab elements added on submit 
        ], 
        id={'type':'select-bar', 'index':PAGE_NUMBER}, className='three columns'),
    
        html.Div([
            
            # # Plot/Tab 1 
            # dcc.Graph(id='plot-1-output'),

            # Multi-View Plot 
            dcc.Graph({'type':'plot-multi-view', 'index':PAGE_NUMBER}),

            # Plot/Tab 2 (Multi-Tab)
            html.Div(id='plot-2-multi-tab-container'),

            # Single-View Tabs 
            # html.Div(id=f'plot-single-view-container-{PAGE_NUMBER}') # TO-DO: Make name conventions consistent b/t pages
        
        ], id=f'reveal-div-{PAGE_NUMBER}', hidden=True, className='seven columns')
])


 ## ---- CALLBACKS ---- ##

## County Dropdown
@callback(
    Output('county-dropdown', 'options'), 
    [Input('state-dropdown', 'value')]
)
def update_county_options(chosen_state_value): 
    
    global counties_dict

    if chosen_state_value is None: 
        return []
    
    counties_in_state = counties_dict[chosen_state_value]
    return [{'label':county, 'value':county} for county in counties_in_state]


## Adult Dropdown Content
@callback(
    Output('n-adults', 'children'), 
    [Input('n-adults-dropdown', 'value')]
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
    Output('n-kids', 'children'),
    [Input('n-kids-dropdown', 'value')]
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
    Output('public-assistance', 'children'), 
    [Input('public-assistance-dropdown', 'value')], 
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
                options=[{'label':'Yes', "value":"Yes"}, {'label':'No', "value":"No"}]
            ), 
            html.Label("Amount spent ($) per month on specialized equipment or services that enable household member(s) with disabilities to work"),
            dcc.Input(id={'type':'disab-work-expenses', 'index':1}, value=0, type='number'), # Only one, but pattern matching ensures callback selects only when it exists
            html.Br(), html.Br()
            ]
        
        global adult_state_storage # should be passed in as values but unsure why that's not working        
        # for state in values: 
        for state in adult_state_storage: # TO-DO: check why *values not passed correctly
            state_id = state.component_id
            # print(state_id)
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


## Job Selection Dropdowns 
@callback( 
    Output('target-occupation-group1-dropdown', 'options'), 
    [Input('broad-occupation-group1-dropdown', 'value')]
)
def update_target_jobs_options1(chosen_occ_group): # isomorphic to update_county_options
    """Update the options in the target dropdown occupations drop down based on the broad occupation group selection"""
    result = [] if chosen_occ_group is None else  _load_target_job_options(job_dict, chosen_occ_group)
    return result

@callback( 
    Output('target-occupation-group2-dropdown', 'options'), 
    [Input('broad-occupation-group2-dropdown', 'value')]
)
def update_target_jobs_options2(chosen_occ_group):
    """Update the options in the target dropdown occupations drop down based on the broad occupation group selection"""
    result = [] if chosen_occ_group is None else  _load_target_job_options(job_dict, chosen_occ_group)
    return result
    
@callback( 
    Output('target-occupation-group3-dropdown', 'options'), 
    [Input('broad-occupation-group3-dropdown', 'value')]
)
def update_target_jobs_options3(chosen_occ_group): 
    """Update the options in the target dropdown occupations drop down based on the broad occupation group selection"""
    result = [] if chosen_occ_group is None else  _load_target_job_options(job_dict, chosen_occ_group)
    return result
    

### PLOTS

@callback(
    Output({'type':'plot-multi-view', 'index':PAGE_NUMBER}, 'figure'),
    [Input('submit-button', 'n_clicks')],

     [State('target-occupation-group1-dropdown', 'value'),
     State('target-occupation-group2-dropdown', 'value'),
     State('target-occupation-group3-dropdown', 'value')]

)
def update_plot_multi_view(n_clicks, *values):
    if n_clicks > 0:

        global data 

        colors = plotting.general_color_palette

        # selected_careers = ['Nurse Practitioners', 'Licensed Practical and Licensed Vocational Nurses', 'Health Technologists and Technicians, All Other']
        selected_careers = values
        data_selected = data[data['CareerPath'].isin(selected_careers)]

        color_map = dict(zip(selected_careers, colors))

        # Use input_text here to customize the plot if needed
        # fig = px.line(data, x='Year', y='NetResources', color='CareerPath', title='Sample Plot')
        # fig = plotting.plot_tab1(data_selected, color_map=color_map, title='Net Resources Over Time for Selected Jobs (New Castle County, Chosen Profile)')
        fig = plotting.plot_multi(data_selected,
                                x_var='Year', 
                                y_var='NetResources', 
                                group_var='CareerPath',
                                color_map=color_map, 
                                title='Net Resources Over Time for Selected Jobs (New Castle County, Chosen Profile)')

        return fig
    else:
        # Return an empty figure when the button is not clicked
        return {}
    

@callback(
    Output('plot-2-multi-tab-container', 'children'), 
    Input('submit-button', 'n_clicks'),
    [State('target-occupation-group1-dropdown', 'value'),
     State('target-occupation-group2-dropdown', 'value'),
     State('target-occupation-group3-dropdown', 'value')],
    prevent_initial_call=True 
)
def render_tabs(n_clicks, *values):
    if n_clicks > 0: 
        return [
            dcc.Tabs(id="plot-2-multi-tab", value='plot-2-tab-one-graph', children=[
                dcc.Tab(label=values[0], value='plot-2-tab-one-graph'),
                dcc.Tab(label=values[1], value='plot-2-tab-two-graph'),
                dcc.Tab(label=values[2], value='plot-2-tab-three-graph'),
            ]),
        html.Div(id="plot-2-output")
        ]

# Load the content of the tabs (based on selected tab)
@callback(
    Output('plot-2-output', 'children'),
    [Input('plot-2-multi-tab', 'value')],

     [State('target-occupation-group1-dropdown', 'value'),
     State('target-occupation-group2-dropdown', 'value'),
     State('target-occupation-group3-dropdown', 'value')]

)

def update_plot_tab2(tab, *values):

        global data 
        colors = plotting.general_color_palette

        n = ["plot-2-tab-one-graph", 'plot-2-tab-two-graph', 'plot-2-tab-three-graph'].index(tab)
            
        # fig = plotting.plot_tab2(df=data[data['CareerPath'] == values[n]], 
        #                         career_color=colors[n], 
        #                         career_name=values[n], 
        #                         title='', 
        #                         legend_text=None)

               
        fig = plotting.plot_single_profile(df=data[data['CareerPath'] == values[n]], 
                                curve_color=colors[n], 
                                curve_name=values[n], 
                                x_var='Year', 
                                y_var='NetResources',
                                title='')

        div_content = html.Div([
            # html.H3(values[0]),
            dcc.Graph(
                figure=fig
            ) 
        ])

        return div_content

@callback( 
    Output(f'reveal-div-{PAGE_NUMBER}', 'style'),
    [Input({'type':'plot-multi-view', 'index':PAGE_NUMBER}, 'figure')]
)
def reveal_output_div(figure):
    if figure is not None and 'data' in figure: 
        if figure['data']:
            return {"display":"block"}
    else: 
        return {'display':'none'}

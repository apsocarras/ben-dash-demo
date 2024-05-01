import dash 
import pandas as pd 
import os 
from dash import dcc, html, Input, Output, State
import yaml
from utils.BeneficiaryProfile import Beneficiary

def list_ordinals(lower=False):
    ordinals = ['First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth']
    if lower: 
        ordinals[:] = map(str.lower, ordinals)
    return ordinals

def create_adult(n:int, default_age=19, page_num=None) -> html.Div: 

    # TO-DO: page - can modify the ids used with a page number to make unique to a given page 
    # age_input_adult_id 
    # age_output_adult_id 
    # age_output_adult_id 


    ordinals = list_ordinals()
    div_content = [
        html.Label(f'Age of {ordinals[n-1]} Adult (19 to 64) '),
        dcc.Input(id={'type':'age-input-adult', 'index':n}, value=default_age, type='number'),
        html.Div(id={'type':'age-output-adult', 'index':n}), 
        dcc.Checklist(id={'type':'disabilities-adult-checkbox', 'index':n}, 
                      options=[{'label':'Has a Disability', 'value':'Disabled'}, {'label':'Legally Blind', 'value':'Legally Blind'}], 
                      value=[]),
        ] 
    if n == 1: 
       div_content.append(
            html.Div(dcc.Checklist(id={'type':'married-adult-checkbox','index':n}, # only one, but this is for pattern-matching callback to not hit if it doesn't exist 
            options=[{'label':'Married', 'value':'Married'}], 
            value=[]),
        hidden=False, # TO-DO: Callback to Reveal if n adults > 1, or validation to ensure n_adults > 2 on submit
        id='married-adult-checkbox-container'))

    # return html.Div(div_content, id=f'adult{n}')
    return html.Div(div_content, id={'type':'adult-div', 'index':n})


def create_kid(n:int, default_ages=[8,5,2]) -> html.Div: 


    if n in range(1,3): 
        default_age = default_ages[n-1]
    else: 
        default_age = 0


    ordinals = list_ordinals()
    div_content = [
        html.Label(f'Age of {ordinals[n-1]} Child (0 to 18) '),
        dcc.Input(id={'type':'age-input-kid', 'index':n}, value=default_age, type='number'),
        html.Div(id={'type':'age-output-kid', 'index':n}), 
        dcc.Checklist(id={'type':'disabilities-kid-checkbox', 'index':n}, options=[{'label':'Has a Disability', 'value':'Disabled'}], 
                      value=[]),
        ] 

    # return html.Div(div_content, id=f'child{n}')
    return html.Div(div_content, id={'type':'child-div', 'index':n})




def load_job_dict(test_mode:bool) -> dict: 
    """Load a dict of broad occupation groups and job titles available for the given county.
    
    Args: 

    test_mode (bool): whether to use the test file I created using my selenium pipeline on the dashboard

    Returns: 

    job_dict (dict): dict of jobs by broad occupation group (keys) and job titles (values)
    
    """
    ## TO-DO: Create a database of jobs for each county with projections available.
    # So far the only projections we have are for New Castle County.    

    if test_mode: 
        
        # Scraped this list from the CLIFF dashboard
        # this should be the complete list of all job options in the Dashboard by occupation group and title, regardless of county 
        # job_dict_fp = os.path.join('notebooks', 'CLIFF-scraping', 'JOB_LIST.yml')
        job_dict_fp = os.path.join( 'JOB_LIST.yaml')
        if not os.path.isfile(job_dict_fp): 
            job_dict_fp = 'JOB_LIST.yaml'
  
        with open(job_dict_fp, 'r') as file: 
            all_job_dict = yaml.full_load(file)

        # Filter to those which are available in the test file
        TEST_FILE = os.path.join('example_data', 'DASH_exports_combined_New-Castle-County_30-adult_5-child_2-child_EDU+CODES.csv')
        df_test = pd.read_csv(TEST_FILE, index_col=0)
        test_job_list = df_test['CareerPath'].drop_duplicates().to_list()

        job_dict = {}
        for occ_group, job_list in all_job_dict.items(): 
            jobs = [x for x in job_list if x in test_job_list] 
            job_dict[occ_group] = jobs

        return job_dict
                
    else: 
        
        return {} # Job projections only available from sample exports


# def create_job_div(): 
#     """Create div with job and target occupation group"""
## TO-DO: might use this if dynanimcally generated div elements 


def _load_target_job_options(job_dict, occ_group) -> list: 
    """Load list of option elements for the target jobs from the job_dict based on the occupation group.
    Function is used in each separate callback function to update job selection dropdowns.
    See how it's used in one of those for context (e.g. update_target_jobs_options1())
    """
    jobs_in_occ_group = job_dict[occ_group]

    return [{'label':job, 'value':job} for job in jobs_in_occ_group]


def extract_ben_dict(states_list):
    """Extract beneficiary information from related State objects.
    Used in callbacks to store current beneficiary profile options.
    
    Args: 

    values (list): callback_context.states_list: List of lists containing State dicts  
    with known id patterns (see known_ids):

        [[{'id': {'index': 1, 'type': 'age-input-adult'}, 
        'property': 'value', 'value': 30}], [{'id':...

    Returns: 

    ben_dict (dict): Dict of beneficiary information matching
    BeneficiaryProfile.Beneficiary.default_schema 
    
    """ 
    known_ids = ('age-input-adult',  
        'married-adult-checkbox', 
        'disabilities-adult-checkbox',  
        'ssdi-adult', 
        'age-input-kid'
        'disabilities-kid-checkbox'
        'anyone-SSI', 
        'disab-work-expenses', 
        'state-dropdown', 
        'county-dropdown')

    ben_dict = Beneficiary.default_schema.copy()


    us_states, counties = [], []
    for state_ls in states_list: 
        if state_ls != []: 
            for state_dict in state_ls: 
                
                # Age 
                if state_dict['id']['type'] in ('age-input-adult', 'age-input-kid'): 
                    offset = 0 if 'adult' in state_dict['id']['type'] else 6 
                    ben_dict['agePerson' + str(state_dict['id']['index'] + offset)] = [state_dict['value']]

                # Married
                elif state_dict['id']['type'] == 'married-adult-checkbox': 
                    if state_dict['value'] == ['Married']:
                        ben_dict['married'] = [1]

                elif 'disabilities' in state_dict['id']['type']: # condensing kid and adult checkbox checks
                    offset = 0 if 'adult' in state_dict['id']['type'] else 6 
                    if 'Disabled' in state_dict['value']: 
                        ben_dict['disability' + str(state_dict['id']['index'] + offset)] = [1]
                    elif 'Legally Blind' in state_dict['value']: 
                        if offset != 0:
                            continue ## TO-DO: Log some warning that kid blindness status isn't used in equations
                                        ## This should not occur due to me not including it in the form 
                        ben_dict['blind' + str(state_dict['id']['index'] + offset)] = [1]
                
                # SSDI 
                elif state_dict['id']['type'] == 'ssdi-adult': 
                    ben_dict['ssdiPIA' + str(state_dict['id']['index'])] = [state_dict['value']]

                # SSI 
                elif state_dict['id']['type'] == 'anyone-SSI':
                    if state_dict['value'] == 'Yes':
                        ben_dict['prev_ssi'] = [1] 

                # Disability Work Expenses 
                elif state_dict['id']['type'] == 'disab-work-expenses':
                    ben_dict['disab.work.exp'] = [0]

                # States and Counties
                elif state_dict['id']['type'] == 'state-dropdown': 
                    us_states.append(state_dict['value'])
                elif state_dict['id']['type'] == 'county-dropdown': 
                    counties.append(state_dict['value'])
                
    locations = [', '.join(tup) for tup in zip(counties, us_states)]
    locations = list(dict.fromkeys(locations)) # drop duplicates
    ben_dict['locations'] = locations

    return ben_dict
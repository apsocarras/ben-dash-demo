## Simple class for storing information related to a beneficiary profile, i.e. someone on benefits)
# (basically sets a long JSON schema with some accessor functions and a connector to a yaml file)
import os 
import yaml 
import subprocess

class Beneficiary:

    # TO-DO: Add class method to initialize from project yaml and "lock" file, i.e. cannot be overwritten

    default_schema = { 

        "ruleYear": [
            2023
        ],
        "Year": [
            2023
        ],
        
        'agePerson1': ['NA'], 'agePerson2': ['NA'], 'agePerson3': ['NA'], 
        'agePerson4': ['NA'], 'agePerson5': ['NA'], 'agePerson6': ['NA'],
        'agePerson7': ['NA'], 'agePerson8': ['NA'], 'agePerson9': ['NA'],
        'agePerson10': ['NA'],'agePerson11': ['NA'], 'agePerson12': ['NA'],

        'disability1': [0], 'disability2': [0], 'disability3': [0], 
        'disability4': [0], 'disability5': [0], 'disability6': [0],
        'disability7': [0], 'disability8': [0], 'disability9': [0],
        'disability10': [0],'disability11': [0], 'disability12': [0],

        'blind1': [0], 'blind2': [0], 'blind3': [0], 
        'blind4': [0], 'blind5': [0], 'blind6': [0],
        
        'ssdiPIA1': [0], 'ssdiPIA2': [0], 'ssdiPIA3': [0], 
        'ssdiPIA4': [0], 'ssdiPIA5': [0], 'ssdiPIA6': [0],
    
        "married": [0],

        "prev_ssi": [0],

        "locations": ["all"],

        "income_start": 20000,
        "income_end": 100000,
        "income_increase_by": 1000,
        "income.investment": [0],
        "income.gift": [0],
        "income.child_support": [0]
        ,

        "empl_healthcare": [0],
        "ownorrent": ["rent"],

        
        "assets.cash": [0],
        "assets.car1": [0],

        "disab.work.exp": [0],

        "k_ftorpt": "FT",
        "schoolagesummercare": "PT",
        "headstart_ftorpt": "PT",
        "preK_ftorpt": "PT",
        "contelig.headstart": False,
        "contelig.earlyheadstart": False,
        "contelig.ccdf": True,
        "budget.ALICE": "survivalforcliff", # same as Survival Line in CLFF Dashboard 


        "APPLY_CHILDCARE": True,
        "APPLY_HEADSTART": True,
        "APPLY_CCDF": True,
        "APPLY_PREK": True,
        "APPLY_LIHEAP": False,
        "APPLY_HEALTHCARE": True,
        "APPLY_MEDICAID_ADULT": True,
        "APPLY_MEDICAID_CHILD": True,
        "APPLY_ACA": True,
        "APPLY_SECTION8": True,
        "APPLY_RAP": False,
        "APPLY_FRSP": False,
        "APPLY_SNAP": True,
        "APPLY_SLP": True,
        "APPLY_WIC": True,
        "APPLY_EITC": True,
        "APPLY_TAXES": True,
        "APPLY_CTC": True,
        "APPLY_CDCTC": True,
        "APPLY_FATES": False,
        "APPLY_TANF": True,
        "APPLY_SSI": True,
        "APPLY_SSDI": True
    }

    # For identifying keys associated with the family members                
    _PERSON_TERMS = ('agePerson', 'disability', 'blind', 'ssdiPIA') # don't change the order of these from ('agePerson', 'disability', 'blind', 'ssdiPIA')

    @classmethod
    def validate_arguments(cls, **config):

        ## Check key names and value types
        for key in config.keys():
        
            # Check if recognized key 
            if key not in cls.default_schema.keys():
                raise ValueError(f"Invalid keyword argument '{key}'")
            
            # Check if the value is of correct type
            default_key_type = type(cls.default_schema[key])
            if not isinstance(config[key], default_key_type):
                raise TypeError(f"'{key}' must be {default_key_type}")
            elif default_key_type is list: 
                if not isinstance(config[key][0], type(cls.default_schema[key][0])):
                    if 'agePerson' in key: # here the value type can also be int 
                        if isinstance(config[key][0], int): 
                            continue
                        else: 
                            raise TypeError(f"'{key}' content must be {type(cls.default_schema[key][0])}")
                
        # Check family parameters: 
        for i in range(1,13):
            if f'agePerson{i}' not in config.keys(): 
                continue

            # If a family member at a given n doesn't exist, but one of the other parameters exists and isn't default
            elif config[f'agePerson{i}'] == ['NA']: 
                for term in Beneficiary._PERSON_TERMS[1:]: 
                    if term + str(i) in config.keys(): 
                        if config[term + str(i)] != [0]:
                            raise Exception(f"Invalid family member configuration ('{term}{i}' without matching 'agePerson{i}')")
            
            # If a family member at a given n is less than 18, but is listed as blind or SSDI 
            # blind children are obviously possible but just not counted in the calculator
            elif config[f'agePerson{i}'][0] < 18: 
                for term in Beneficiary._PERSON_TERMS[2:]: # blind, ssdi
                    if term + str(i) in config.keys():
                        if config[term + str(i)] != [0]:
                            raise Exception(f"Invalid family member configuration ('{term}{i}' given but 'agePerson{i}' is < 18)")

    @classmethod
    def from_yaml(cls, file_path):
        project_name = os.path.splitext(os.path.basename(file_path))[0]

        with open(file_path, 'r') as file:
            config_data = yaml.safe_load(file)

        return cls(project_name, **config_data)



    def __init__(self, project_name:str, **config): # pass valid key:values according to schema set in TEST.yaml 

        # Validate against default schema and set accessor (Can indicate what user changed)
        self.validate_arguments(**config)
        self.config = config 

        # Create Profile from Default Schema (Profile is set on init and should not be modified)
        self._Profile = {}
        for key in Beneficiary.default_schema.keys(): 
            if key in config.keys(): 
                self._Profile[key] = config[key]
            else: 
                self._Profile[key] = Beneficiary.default_schema[key]

        self.locations = self._Profile['locations']
        self.married = self._Profile['married']
        self.project_name = project_name
        
        self.output_path = os.path.join('output', 'results_' + self.project_name + '.csv')

        ## Methods
        # save/update yaml file 
        # check against yaml file 
        # return dict summary of beneficiary profile 
        # Print non-default params 
     
    def get_family(self) -> dict: 
        """List the family member information"""   

        family_data = {}
        adult_count = 0 
        child_count = 0
        for i in range(1, 13): 
            if self._Profile[f"agePerson{i}"] == ['NA']:
                continue 
            # Add member age 
            age_status = 'Adult' if int(self._Profile[f"agePerson{i}"][0]) >= 18 else 'Child'
            if age_status == 'Adult': 
                adult_count += 1
                age_status += str(adult_count)
            else: 
                child_count += 1 
                age_status += str(child_count)

            family_data[age_status] = {'Age':self._Profile[f"agePerson{i}"][0]}

            # Add if disabled 
            family_data[age_status]['Disability'] = bool(self._Profile[f'disability{i}'][0])

            # Add ssdi amount / blind 
            if 'Adult' in age_status: 
                family_data[age_status]['Blind'] = bool(self._Profile[f'blind{i}'][0])                
                family_data[age_status]['SSDI_Monthly'] = self._Profile[f'ssdiPIA{i}'][0]

        return family_data
    
    def get_benefits(self) -> list: 
        """Summarize the benefits programs applied""" 
        
        benefits_programs = [
            k.lstrip('APPLY_') for k,v in self._Profile.items()
            if 'APPLY' in k and v != False
        ] # TO-DO: Change benefits to explanations where needed (e.g. APPLY_TAXES)

        return benefits_programs
    
    def non_default(self): 
        """Get non-default parameters in the Profile"""
        non_default = {k:v for k,v in self._Profile.items() if v != Beneficiary.default_schema[k]}
        return non_default

    def save_project(self, outdir='projects', overwrite=False):
        if not os.path.exists(outdir): 
            raise Exception(f'Check that {outdir} is in current directory.')
        else: 
            fp = os.path.join(outdir, self.project_name + '.yaml')
            if os.path.isfile(fp) and not overwrite: 
                raise Exception(f'{fp} exists and overwrite is {overwrite}')
            else: 
                with open(fp, 'w') as file: 
                    yaml.dump(self.Profile, file)
        return     

    def run_applyBenefitsCalculator(self) -> None:
        """Run the calculator R script for the project's YAML"""

        command = ["Rscript", "applyBenefitsCalculator.R", self.project_name]
        subprocess.run(command)

    @property
    def Profile(self):
        return self._Profile










import plotly.express as px 
import plotly.graph_objects as go 
from utils.BeneficiaryProfile import Beneficiary
import utils.utils as utils 
import numpy as np 

## Parameters and utility functions for making plots 

general_color_palette =[
"#FFD700", # (Gold)
"#008080", # (Teal)
"#FF6347", # (Tomato)
"#00CED1", # (Dark Turquoise)
]

beneficiary_color_palette =[
"#1b9e77",
"#d95f02",
"#7570b3",
]

ben_display_map = {

  # column_name: display_name, display_color   
  ## Benefits Columns in output from applyBenefitsCalculator.R
 'value.snap': ('SNAP', '#2B3514'),
 'value.schoolmeals': ('School Meals', '#D32B1E'),
 'value.section8': ('Section 8', '#6F340D'),
 'value.liheap': ('LIHEAP', '#92AE31'),
 'value.medicaid.adult': ('Medicaid (Adult)', '#7E1510'),
 'value.medicaid.child': ('Medicaid (Child)', '#9a9a00'),
 'value.aca': ('ACA', '#91218C'),
 'value.employerhealthcare': ('Employer Healthcare', '#E1A11A'),
 'value.CCDF': ('CCDF', '#463397'),
 'value.HeadStart': ('Head Start', '#DF8461'),
 'value.PreK': ('Pre-K', '#4277B6'),
 'value.cdctc.fed': ('CDCTC (Federal)', '#D485B2'),
 'value.cdctc.state': ('CDCTC (State)', '#5FA641'),
 'value.ctc.fed': ('CTC (Federal)', '#7F7E80'),
 'value.ctc.state': ('CTC (State)', '#C0BD7F'),
 'value.eitc.fed': ('EITC (Federal)', '#BA1C30'),
 'value.eitc.state': ('EITC (State)', '#96CDE6'),
 'value.eitc': ('EITC', '#DB6917'),
 'value.ctc': ('CTC', '#702C8C'),
 'value.cdctc': ('CDCTC', '#EBCE2B'),
 'value.ssdi': ('SSDI', '#1D1D1D'),
 'value.ssi': ('SSI', '#DDDDDD'),
 
  ## Additional columns from the dashboard output 
  'value.earlyHeadStart': ('Head Start', '#E55D29'),   
  'value.wic' :  ('WIC', '#f9cab9'), 
  'value.FATES' : ('FATES', '#9ce019'), 
  'value.medicaid' :  ('Medicaid', '#30f593') 

 }
 

def create_custom_ticks_labels() -> tuple:     
    ## TO DO: let customize salary ranges from parameters  
    ## Create custom ticks for yearly and hourly wages 
    custom_ticks = list(range(30000, 100001, 10000)) 
    hourly_wages = [utils.get_hourly_wage(x) for x in custom_ticks]

    custom_labels = [f"${x[0]:,}\n{x[1]}" for x in zip(custom_ticks, hourly_wages)]
    return custom_ticks, custom_labels
    
### ------------------------------------------------------------------------------ ###
### --- PLOTLY TEMPLATES & HELPERS --- ###

## Generalized single curve plotting 
def plot_single_profile(df, x_var, y_var, curve_color, curve_name, fig=None,  title=None, ben_profile_text=None, plot_derivative=False): 
    """Plot single curve (either net resources per year for one job in tab1/tab2, or net resources vs income bracket in tab3) for one beneficiary profile.
    For multiple curves on one figure, this function is iterated over the same "fig" object and certain options are omitted. 
    """

    if title is None: 
        title = 'Net Resources for Chosen Beneficiary Profile'

    x,y = df[x_var], df[y_var]

    min_curve_name_len = 38 # hacky solution for legend box padding in plotly, can't find natively
    curve_name += " " * max(0, min_curve_name_len - len(curve_name))

    if fig is None: # Single Profile Plot
        fig = go.Figure()
        plot_benefits = True 

        # Add annotation box for beneficiary profile
        if ben_profile_text is not None: 
            fig.add_annotation(
                text=ben_profile_text,
                align='left',
                showarrow=False,
                xref='paper',
                yref='paper',
                x= 1.02,
                xanchor='left',
                y=.5,
                bordercolor='black',
                borderwidth=1, 
                bgcolor='white'    
            )
            
        # Add break even line 
        fig.add_shape(type="line",
            x0=df[x_var].min(),
            y0=0,
            x1=df[x_var].max(),
            y1=0,
            line=dict(color="red",width=4,dash="dash"),
            )
        
    else: # Multi Profile Plot
        plot_benefits = False 
        
    ## Main curve     
    derivative, derivative_rel_minima = utils.find_derivative(x,y)
    if plot_derivative: 
        derivative_scale = 10000
        fig.add_trace(go.Scatter(x=x, y=derivative * derivative_scale, 
                                 mode='markers+lines', line=dict(color="grey"), 
                                 name=f'1st Derivative (* {derivative_scale})'))

    ## Benefits
    df_benefits = utils.filter_benefits(df, include_eitc=False, include_ctc=False)
    cliffs = utils.find_benefits_cliffs(df_benefits, derivative_rel_minima, mode='peak')

    # Add annotations at cliff peaks 
    ben_cliff_peaks = np.empty(shape=df.shape[0], dtype=np.object_) # for storing where peaks are for hover text
    for ben_col, cliff_indices  in cliffs.items():
        for cliff_idx in cliff_indices: 
            x_label = x.iloc[cliff_idx]
            resource_level = y.iloc[cliff_idx]
            
            fig.add_annotation(
                x=x_label,
                y=resource_level,
                xref="x",
                yref="y",
                text='',
                showarrow=False,
                bordercolor="black",
                borderwidth=2,
                borderpad=4,
                bgcolor=curve_color,
                opacity=0.8
                )
            
            # Store name of the benefit lost at the given index
            if ben_cliff_peaks[cliff_idx] is None:
                ben_cliff_peaks[cliff_idx] = [ben_display_map[ben_col][0]]
            else: 
                ben_cliff_peaks[cliff_idx].append(ben_display_map[ben_col][0])

    # Create text array for hover text 
    # Need to combine income with the benefit that was lost, if any, to pass in as "text" parameter
        # Income is accessible in hovertemplate as 'x' if it's the x variable, but not if x == "Year"  
    text_list = []
    for income, ben_list in zip(df['income'], ben_cliff_peaks): 
        text = utils.format_int_dollars(income)
        if ben_list is not None: 
            text += f"<br>Lost Benefits: " + ', '.join(ben_list)
        text_list.append(text)
    hover_template = 'Net Resources: %{y:$,.0f}<br>Income: %{text}  <extra></extra>'
    if x_var == "Year": 
        hover_template = "Year: %{x}<br>" + hover_template
        

    ## Plots 
    # Base plot 
    fig.add_trace(go.Scatter(x=df[x_var], y=df[y_var],text=text_list,
                                mode='markers+lines', name=curve_name, 
                                line=dict(color=curve_color)))
    # fig.update_traces(hovertemplate='Year: %{x}<br>Net Resources: %{y:$,.0f}<br>Income: %{text}  <extra></extra>') 
    fig.update_traces(hovertemplate=hover_template) 

    # Benefits
    if plot_benefits: 
    
        ben_cols_ordered = list(cliffs.keys()) + [col for col in df_benefits.columns if col not in cliffs.keys()]
            # First plot cols w/ cliffs so legend label order is correct 

        for col in ben_cols_ordered: 
            visibility = True if col in cliffs.keys() else 'legendonly' 
            fig.add_trace(go.Scatter(x=df[x_var],y=df[col], 
                                    mode='markers+lines', 
                                    hovertemplate='%{y:$,.0f}',
                                    line=dict(color=ben_display_map[col][1]),
                                    name=ben_display_map[col][0], visible=visibility))
            
            
    # Adjust Sizing and main axis labels 
    fig.update_layout(
        autosize=True,
        minreducedwidth=20,
        title=title, 
        xaxis=dict(title=x_var.title()),
        yaxis=dict(title="$ (Net Resources OR Benefits)"),
        height=800,
        width=1300
        )
    
    # Adjust axis labels 
    # If x-axis is income, adjust labels to annual & hourly wage
    fig.update_xaxes(labelalias={f"{n}k":f"${n},000 <br>(${(n * 1000) / (52 * 40):.2f}/h)" for n in range(10, 110, 10)})
    # fig.update_yaxes(labelalias={f"{n}k":f"${n},000" for n in range(-15, 30, 5)}) # not working for negative dollars, I don't know why
        
    return fig 

## Generalized multi curve plot
def plot_multi(df, x_var, y_var, group_var, color_map=None, title=None): 
    """Plot net resources over (income or time) for multiple (jobs, counties, or beneficiary profiles)"""

    if color_map is None: 
        color_map = dict(zip(df[group_var].unique(), general_color_palette))

    known_group_cols = ("countyortownName","CareerPath","BeneficiaryProfile", "state_county")
    if group_var not in known_group_cols: # TO-DO: BeneficiaryProrfile is created column from combining dataframes
        raise Warning(f"{group_var} not in known grouping columns ({known_group_cols})")
    
    fig = go.Figure()

    for group in df[group_var].unique():
         
        dff = df[df[group_var] == group] 

        fig = plot_single_profile(dff, 
                                  x_var=x_var, 
                                  y_var=y_var,
                                  curve_color=color_map[group],
                                  curve_name=group, 
                                  fig=fig)

    ## -- Add baseline (break-even) -- ## 
    fig.add_shape(type="line",
                x0=df[x_var].min(),
                y0=0,
                x1=df[x_var].max(),
                y1=0,
                line=dict(color="red",width=4,dash="dash"),
                )

    ## --- Add title --- ## 
    fig.update_layout(title=title, legend=dict(x=.02, y=.98))

    return fig 

# Legend for Beneficiary Profile
def create_profile_legend_text(family_data:dict, color:str, ben_list=[]): 
    """Create the legend annotation for a beneficiary profile
    
    Args: 

    family_data (dict): dict of family parameters matching schema of BeneficiaryProfile.Beneficiary.get_family()

    ben_list (list): list of benefit program names

    (TO-DO: I might turn this function a method of that class but I wanted to keep all plot-related functions in the same file).
    """
    legend_text = f"<span style='color:{color};'><b>Net Resources for Family:</b></span><br><i>(Age, Disabled, Blind, Monthly SSDI)<br></i>"

    for fam_member, params in family_data.items():
        legend_text = legend_text + f"<b>{fam_member}</b>: " 
        if isinstance(params, dict): 
            for v in params.values(): 
                legend_text += f"{v}, "
        else: # flexibility for other dict schemas
            for v in params: 
                legend_text += f"{v}, "
        legend_text = legend_text.rstrip(', ') + "<br>"
        
    ## Add Benefits List
    legend_text += "<i>" 
    for i in range(len(ben_list)):
        if i % 3 == 0:
            legend_text += "<br>"
        legend_text += ben_list[i] + ", " 
    legend_text = legend_text.rstrip(",  ") + "</i>"

    return legend_text
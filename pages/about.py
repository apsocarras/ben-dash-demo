from dash import dcc, html, Input, Output, callback, register_page, page_registry
import plotly.express as px
import pandas as pd



register_page(__name__, name='About this tool', path="/")

layout = html.Div([
    html.Div([
    html.H3(['About this tool:']), 
    html.Div(['A demo dashboard expanding off the functionality of the Policy Rules Database (PRD) and CLIFF Dashboard produced by the Atlanta Federal reserve bank. On each page, you can enter information about an American household receiving benefits and view their estimated net resources (i.e. assets after income plus benefits minus expenses and taxes).']),
    html.H4(['Page Descriptions:']),
    html.Div(['Use the navigation bar in the header to move between the following pages.']),
    html.Br(),
    html.Ul([
            html.Li([
                html.A('Compare Jobs', href='/compare-jobs'),
                html.P("Select and compare three jobs for a chosen beneficiary profile.")
            ]),
            html.Li([
                html.A('Compare Counties', href='/multi-county-single-profile'),
                html.P("Compare net resources per income bracket for a chosen beneficiary profile.")
            ]),
            html.Li([
                html.A('Compare Beneficiary Profiles', href='/multi-profile-single-county'),
                html.P("View net resources per income bracket for three beneficiary profiles within a given county.")
            ]),
            html.Li([
                html.A('Skills Matcher', href='/skills-matcher'),
                html.P("Take a Skills Assessment from CareerOneStop to compare recommended career paths.")
                ])
            ])
            ], id='Table-of-contents-bar',className="five columns"),
    html.Div([
        html.Br(),
        html.Img(src="/assets/frba_line_logo.png", style={'width': '75%', 'height': '75%', 'text-align':'right'}),
        html.Br(),
        html.Br(),
        html.Img(src="/assets/Tech_Impact_Main_Logo_Color_Border.png", style={'width': '75%', 'height': '50%', 'text-align':'right'}),
    ], id='Logos-div', className='five columns'),
])
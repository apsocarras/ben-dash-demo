from dash import html, dcc
from dash.dependencies import Input, Output
import dash
import os

app = dash.Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
server = app.server
app.layout = html.Div(
    [
        dcc.Store(id="store", data={}),
        dcc.Store(id="county-comparison-beneficiary-store", data={}),
        dcc.Store(id="county-comparison-df-store", data={}), 
        html.H1("Benefits Cliffs Dashboard Demo"),
        html.Div( # The "Nav Bar" 
            [
                html.Div(
                    dcc.Link(f"{page['name']}", href=page["path"]),
                    style={'display':'inline', 'margin-right':'30px'}
                ) 
                for page in dash.page_registry.values()
            ]
        ),
        # html.Div(id='store-display'), 
        html.Hr(), # Page divider 
        dash.page_container, # Contains content of whatever page you're on. 
    ]
)

# @app.callback(
#     Output('store-display', 'children'),
#     [Input('county-comparison-beneficiary-store', 'data')]
# )
# def update_store_content(data):
#     if data: 
#         return str(data)

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
import base64
import os
from urllib.parse import quote as urlquote

from flask import Flask, send_from_directory
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, ALL
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import json

UPLOAD_DIRECTORY = "/project/app_uploaded_files"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)


# Normally, Dash creates its own Flask server internally. By creating our own,
# we can create a route for downloading files directly:
server = Flask(__name__)
app = dash.Dash(server=server)


@server.route("/download/<path:path>")
def download(path):
    """Serve a file from the upload directory."""
    return send_from_directory(UPLOAD_DIRECTORY, path, as_attachment=True)


app.layout = html.Div(
    [
        dcc.Store(id='updateFilesList'),
        html.H1("File Browser"),
        html.H2("Upload"),
        dcc.Upload(
            id="upload-data",
            children=html.Div(
                ["Drag and drop or click to select a file to upload."]
            ),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            multiple=True,
        ),
        html.H2("File List"),
        html.Ul(id="file-list"),
    ],
    style={"max-width": "800px"},
)


def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    with open(os.path.join(UPLOAD_DIRECTORY, name), "wb") as fp:
        fp.write(base64.decodebytes(data))
    
def delete_file(filename): 
    """Delete a file from the upload directory"""
    if os.path.exists(os.path.join(UPLOAD_DIRECTORY, filename)):
        os.remove(os.path.join(UPLOAD_DIRECTORY, filename))
        return True
    return False

def uploaded_files():
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(UPLOAD_DIRECTORY):
        path = os.path.join(UPLOAD_DIRECTORY, filename)
        if os.path.isfile(path):
            files.append(filename)
    return files


def file_download_link(filename):
    """Create a Plotly Dash 'A' element that downloads a file from the app."""
    location = "/download/{}".format(urlquote(filename))
    return html.A(filename, href=location)



@app.callback(
    Output("file-list", "children"),
    [
        Input("upload-data", "filename"), 
        Input("upload-data", "contents"), 
        Input('updateFilesList', 'data')
    ],
)
def update_output(uploaded_filenames, uploaded_file_contents, updateFilesList):
    """Save uploaded files and regenerate the file list."""

    if uploaded_filenames is not None and uploaded_file_contents is not None:
        for name, data in zip(uploaded_filenames, uploaded_file_contents):
            save_file(name, data)

    files = uploaded_files()
    if len(files) == 0:
        return [html.Li("No files yet!")]
    else:
        return [html.Li([
            file_download_link(filename), 
            dbc.Button(
                'Delete', 
                id={'id':'deleteBtn', 'filename': filename}, 
                color="danger", 
                outline=True, 
                className="mr-1", 
                style={'marginLeft': '20px'}, 
                n_clicks=0
            )
        ], style={'marginTop': '10px'}) for filename in files]

@app.callback(
    Output('updateFilesList', 'data'),
    Input({'id': 'deleteBtn', 'filename': ALL}, 'n_clicks')
)
def delete_files(deleteBtn): 
    context = dash.callback_context.triggered
    if len(context) > 1 or (len(context) == 1 and not context[0]['value']): 
        raise PreventUpdate
    
    prop_id = '.'.join(context[0]['prop_id'].split('.')[:-1])
    
    file_dict = json.loads(prop_id)
    if delete_file(file_dict['filename']): 
        return {'deleted': True}

    return {'deleted': False}


if __name__ == "__main__":
    app.run_server(debug=True, port=8888)
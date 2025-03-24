import dash
from dash import dcc, html, Input, Output, State
import dash_mantine_components as dmc
from dash_chat import ChatComponent
import requests

import os
from dotenv import load_dotenv
load_dotenv()

backend_url = os.getenv('BACKEND_URL', "http://localhost:8000/chat")

app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Define login layout
login_layout = dmc.Center([
    dmc.Paper([
        dmc.Title("Tourism Chat Login", mb=20),
        dmc.TextInput(id="username", label="Username", placeholder="Enter your username"),
        dmc.PasswordInput(id="password", label="Password", placeholder="Enter your password"),
        dmc.Button("Login", id="login-button", fullWidth=True, mt=10),
        dmc.Text(id="login-output", mt=10)
    ], p=30, withBorder=True, shadow="md", radius="md", style={"width": "400px"})
], style={"height": "100vh"})

# Wrap the entire app with MantineProvider
app.layout = dmc.MantineProvider([
    html.Div(id="page-content", children=[login_layout])
])


# Define chat layout
chat_layout = dmc.Center([
    dmc.Paper([
        dmc.Title("Tourism Chatbot", mb=20),
        ChatComponent(
            id="chat-component",
            messages=[],
            container_style={'height': '90%'}
        )
    ], p=30, withBorder=True, shadow="md", radius="md", style={"width": "80%", "height": "90%"})
], style={"height": "100vh"})

# Login callback
@app.callback(
    Output("page-content", "children"),
    Output("login-output", "children"),
    Input("login-button", "n_clicks"),
    State("username", "value"),
    State("password", "value"),
    prevent_initial_call=True
)
def login(n_clicks, username, password):
    if username == "user" and password == "pass":
        return chat_layout, ""
    return login_layout, "Invalid username or password."

# Chat callback
@app.callback(
    Output("chat-component", "messages"),
    Input("chat-component", "new_message"),
    State("chat-component", "messages"),
    prevent_initial_call=True
)
def handle_chat(new_message, messages):
    if not new_message:
        return messages

    updated_messages = messages + [new_message]

    if new_message["role"] == "user":
        response = requests.post(backend_url, json={"user_id": "1", "message": new_message["content"]})
        bot_response = response.json().get("response", "No response")

        bot_msg = {"role": "assistant", "content": bot_response}
        return updated_messages + [bot_msg]

    return updated_messages

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

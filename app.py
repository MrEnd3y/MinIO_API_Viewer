from flask import Flask, request, jsonify
import gradio as gr
import json
import threading
import signal
import sys
import pandas as pd
from config import FLASK_HOST, FLASK_PORT, GRADIO_HOST, GRADIO_PORT, GRADIO_ROOT_PATH, GRADIO_SHARE

# Create an instance of a Flask app
app = Flask(__name__)

# Variables for storing data
DATA_STORAGE = []
DATA_RAW_STR = ""
DATA_TEMP = []
DATA_COUNT = 0
DF = pd.DataFrame(columns=['UserName', 'Total'])

@app.route('/', methods=['POST'])
def main():
    global DATA_TEMP, DATA_COUNT
    payload = request.get_json()
    print("Received webhook data:", payload)
	    
    # Adding new data to temporary store
    DATA_TEMP.append(payload)
    DATA_COUNT += 1
    return jsonify({"message": "Data received", "current_count": DATA_COUNT})

def create_dynamic_table(df, data):
    """
    Updates the DataFrame by adding users and their API calls.

    Parameters:
    df (pd.DataFrame): The DataFrame containing information about users and their API calls.
    data (Union[Dict[str, Any], List[Dict[str, Any]]]): 
        A dictionary or a list of dictionaries containing data about users and their API calls.
        Each dictionary should contain the keys 'requestClaims' and 'api'.

    Returns:
    pd.DataFrame: The updated DataFrame with added users and their API calls.
    """
    if type(data) is not list: data = [data]

    # We process each element in the data
    for entry in data:
        # Extract parentUser, if not specified, use 'MinIO'
        parent_user = entry.get('requestClaims', {}).get('parent', entry.get('parentUser', 'MinIO'))
        api_name = entry.get('api', {}).get('name', 'None')
        
        # Adding a record to the DataFrame
        if parent_user not in df['UserName'].values:
            df.loc[len(df)] = {"UserName":parent_user}        
            df = df.fillna(0)
		
        # Increase the counter for this api_name
        index = df[df['UserName'] == parent_user].index[0]
        if api_name in df.columns:
            df = df.fillna(0)
            df.at[index, api_name] += 1
        else:
            df.at[index, api_name] = 1

    # Fill NaN values ​​with zeros
    df = df.fillna(0)
	
    # Calculate the total amount
    columns = [column for column in df.columns if column not in ['UserName', 'Total']]
    df['Total'] = df[columns].sum(axis=1)
	
    # Move to the very end
    df['Total'] = df.pop('Total')
    return df

def calc_edges(window, value):
    if window < 0:
        start = window-value
        end = -value if value != 0 else None
    else:
        start = value
        end = value+window
    return start, end

def udate_str_data(window, value):
    global DATA_RAW_STR
    start, end = calc_edges(window, value)
    DATA_RAW_STR = ""
    t = len(DATA_STORAGE) + start if len(DATA_STORAGE) > abs(start) else 0
    for index, item in enumerate(DATA_STORAGE[start:end], t if start < 0 else start):
        number_str = f"Item {index + 1}"
        centered_number = number_str.center(100, "=")
        DATA_RAW_STR += centered_number + "\n" + json.dumps(item, indent=4) + "\n" + "="*100 + "\n"
    return DATA_RAW_STR

def get_data(window, value):
    global DF, DATA_TEMP, DATA_STORAGE, DATA_RAW_STR
    if len(DATA_TEMP) != 0:
        temp_list = []
        for i in range(len(DATA_TEMP)):
            removed_element = DATA_TEMP.pop(0)
            temp_list.append(removed_element)
            DATA_STORAGE.append(removed_element)
        DF = create_dynamic_table(DF, temp_list)
        DATA_RAW_STR = udate_str_data(window, value)
    return DF, DATA_RAW_STR

def refresh_view_elements(window, value):
    global DATA_COUNT
    start, end = calc_edges(window, value)
    if end is None: end = ""
    return gr.update(value=f"Amount: {DATA_COUNT}\nDATA[{start}:{end}]")

def create_gradio_interface():
    with gr.Blocks() as app_ui:
        gr.Markdown("## MinIO API Viewer")
        
        # Create tabs
        with gr.Tab("DataFrame"):
            output_dataframe = gr.DataFrame(label="Result", interactive=False)

        with gr.Tab("Raw data"):
            with gr.Row():
                output_raw = gr.Textbox(label="Raw data", interactive=False, scale=10, lines=15, max_lines=15 , elem_id="output_raw")
                with gr.Column():
                    item_count = gr.Label(value=f"Amount: {DATA_COUNT}\nDATA[-10:]", container=False)  
                    window_number = gr.Number(label="Window size", value=-10, step=1) 
                    value_slider = gr.Slider(minimum=0, maximum=10, step=1, label="Range X", value=0)
				
        # Buttons for updating and resetting data
        refresh_button = gr.Button("Update Data")
        reset_button = gr.Button("Delete data")

        # Update data at the click of a button
        refresh_button.click(fn=get_data,inputs=[window_number, value_slider], outputs=[output_dataframe, output_raw])
		
        # Changing the slider and input window
        value_slider.change(fn=refresh_view_elements, inputs=[window_number, value_slider], outputs=item_count)
        window_number.change(fn=refresh_view_elements, inputs=[window_number, value_slider], outputs=item_count)

        # Data update every 1 second
        timer = gr.Timer(1)
        timer.tick(fn=get_data, inputs=[window_number, value_slider], outputs=[output_dataframe, output_raw])  # Обновляем оба вывода
        #timer.tick(fn=refresh_max_value_slider, outputs=value_slider)
        timer.tick(fn=lambda: gr.update(maximum=DATA_COUNT), outputs=value_slider)
        timer.tick(fn=udate_str_data, inputs=[window_number, value_slider], outputs=output_raw)
        timer.tick(fn=refresh_view_elements, inputs=[window_number, value_slider], outputs=item_count)
		
        # Function for resetting data
        def reset_data():
            global DATA_STORAGE, DATA_COUNT, DF, DATA_RAW_STR
            DATA_COUNT = 0
            DATA_STORAGE = []
            DATA_RAW_STR = ""
            DF = pd.DataFrame(columns=['UserName', 'Total'])
            return get_data(window_number, value_slider)

        reset_button.click(fn=reset_data, outputs=[output_dataframe, output_raw])
        
    return app_ui

def signal_handler(sig, frame):
    """Signal handler for completion"""
    print("Завершение работы...")
    if 'app_ui' in globals():
        app_ui.close()
    sys.exit(0)

def run_flask():
    """Launches the Flask-application."""
    app.run(host=FLASK_HOST,
            port=FLASK_PORT)

def run_gradio():
    global app_ui
    """Launches the Gradio interface."""
    app_ui = create_gradio_interface()
    app_ui.launch(share=GRADIO_SHARE,
                  root_path=GRADIO_ROOT_PATH,
                  server_name=GRADIO_HOST,
                  server_port=GRADIO_PORT)
    
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    # Run Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Launch Gradio
    run_gradio()

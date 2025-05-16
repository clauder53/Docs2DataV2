import streamlit as st
import sqlite3
import requests
from   PIL import Image


#t.image(image, caption='Sunrise by the mountains')

# Database setup for storing API key and deployment URL
def init_db():
    conn = sqlite3.connect("api_data.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT,
            deployment_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_credentials():
    conn = sqlite3.connect("api_data.db")
    c = conn.cursor()
    c.execute("SELECT api_key, deployment_url FROM credentials ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    return row

def save_credentials(api_key, deployment_url):
    conn = sqlite3.connect("api_data.db")
    c = conn.cursor()
    c.execute("INSERT INTO credentials (api_key, deployment_url) VALUES (?, ?)", (api_key, deployment_url))
    conn.commit()
    conn.close()

# IBM Cloud token retrieval function
def get_ibm_token(api_key):
    token_url = 'https://iam.cloud.ibm.com/identity/token'
    data = {
        "apikey": api_key,
        "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'
    }
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        #st.write("We have a token")
        return response.json()["access_token"]
    else:
        st.error("Failed to retrieve token")
        return None
# Function to perform a search query to the GenAI model
def perform_search(search_query, token, deployment_url):
    header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}

    # Example payload for search functionality
    messages = [{"role": "user", "content": search_query}]  # Search query is passed as the message

    # Payload for the search use case
    payloadx = {
        "input_data": [
            {
                "fields": ["Search", "access_token"],  # Adjust based on your API's expected fields
                "values": [messages, [token]]  # Pass messages as search query and token if needed
            }
        ]
    }
    payloady = {
        "input_data": [
            {
                "fields": ["Search"],  # Adjust based on your API's expected fields
                "values": [messages]  # Pass messages as search query and token if needed
            }
        ]
    }

    # Log the payload for debugging
    #st.write(f"Messages: {messages}")
    #st.write(f"Deployment_url: {deployment_url}")
    #st.write(f"Headers:{header}")
    #st.write(f"Payload being sent: {payload}")

    payload_scoring = {"messages":messages}

    response         = requests.post("https://us-south.ml.cloud.ibm.com/ml/v4/deployments/efc848c8-3f4a-471d-b68c-05bcd8138d58/ai_service?version=2021-05-01",
                                    json=payload_scoring,
                                    headers={'Authorization': 'Bearer ' + token})


    #response = requests.post(deployment_url, json=payload, headers=header)

    #print("ResponseX:", str(response.json()) )
    
    if response.status_code == 200:
        try:
            return response.json()  # Adjust parsing based on your API's response structure
        except IndexError as e:
            st.error(f"Error parsing response: {e}")
            st.error(response.json())  # Show raw response for further debugging
            return None
    else:
        st.error(f"Error fetching search results: {response.status_code} - {response.text}")
        return None

def display_results(results):
    # Display the generated response in markdown format
    key_list = list(results.keys())
    #print("Keys in Result dict:", key_list)

    choices = results
    #print("Keys in Choices dict:", results["choices"][0])

    #print("Choices:", choices["choices"][0])
    datac = choices["choices"][0]
    datam = datac["message"]
    datat = datam["content"]
    #print("Content:", datat)
    generated_response = datat
    st.write(f"**Generated Response:**\n\n{generated_response}")

def append_summary( search_response):
    choices = search_response
    datac = choices["choices"][0]
    datam = datac["message"]
    datat = datam["content"]
    generated_response = datat
    return generated_response

    
# Function to display search results in Streamlit chat style
def display_results_predictions(results):
    predictions = results['predictions'][0]

    # Extract the proximity search results and the generated response
    proximity_results = predictions['values'][0]
    generated_response = predictions['values'][1]

    # Display the generated response in markdown format
    st.write(f"**Generated Response:**\n\n{generated_response}")

    # Optionally display the proximity search results
    st.markdown("**Proximity Search Results:**")
    for result in proximity_results:
        metadata = result['metadata']
        score = result['score']
        st.write(f"Asset: {metadata['asset_name']} (Score: {score:.2f})")
        st.write(f"Range: {metadata['from']} - {metadata['to']}")
        #st.write(f"[View Document]({metadata['url']})")
        st.write("---")  # Line separator for better readability


def generate_summary( api_key, optionc, optionp, optionw, deployment_url):
   
    sentences = ""

    summary_1 = "What is the Loan Number?"
    summary_3 = "Who is the borrower?"
    summary_2 = "Give me the terms of the loan as amount, interest rate, repayment period"
    summary_4 = "what is the collateral"
    summary_5 = "what is the monthly payment?"
    summary = [];
    narrative = [];

    summary.append(summary_1)
    summary.append(summary_3)
    #summary.append(summary_5)
    summary.append(summary_2)
    al = len(summary)

    token = get_ibm_token(api_key)

    if token:
        sentences = "Summary for project " + optionc + " for period " + optionp + "\n\n" 
        for query in summary:
            search_response = perform_search(query, token, deployment_url)
            if search_response:
                response = "\n\n"
                response += append_summary(search_response)
                sentences += response + "\n"

        st.write(f"\n\n{sentences}")


####### TOP OF LOOP ##################

# Initialize the database -- we can optimize this with state 
init_db()
#...
# Fetch stored credentials or use defaults
credentials = get_credentials()
default_api_key = "FedF8mcrgdZotpwU31BtvOwnSE3gGOyGHF0_et47-WFL" # created a new one 
default_deployment_url = "https://us-south.ml.cloud.ibm.com/ml/v4/deployments/9739daac-1507-4e07-be46-f449a3735ccc/ai_service?version=2021-05-01"

#TEST_default_api_key = "FedF8mcrgdZotpwU31BtvOwnSE3gGOyGHF0_et47-WFL"  # Replaced -- with my default API key
#TEST_default_deployment_url = "https://us-south.ml.cloud.ibm.com/ml/v4/deployments/02f00442-5529-4f26-beaa-f7db8e3dfe40/predictions?version=2021-05-01"
#TEST_default_deployment_url = "https://us-south.ml.cloud.ibm.com/ml/v4/deployments/9c1260e4-6738-4660-bb6b-858c20574959/ai_service?version=2021-05-01"

qlist = ["Calculate the Monthly Payment", "Calculate the DSCR", "Who is(are) the borrower(s)"]
#...
    
image = Image.open('3.jpg')
st.image(image) 

#st.header("Docs2Data.AI (sm)")

# Streamlit UI
st.header("AskAL&nbsp;&nbsp;&nbsp;your Research Assistant")
#st.markdown('<p>AskAlyour Review Assistant</p>', unsafe_allow_html=True)

#The loop starts here so yu need to maintain a state
#print("Right at the top?")
if "qlist" not in st.session_state:
    qlist =  ["Ask a new question", "Calculate the Monthly Payment", "Calculate the DSCR", "Who is(are) the borrower(s)"]
    st.session_state["qlist"] = qlist
   
    option1 = 'Christmas Lane'
    option2 = "2024"
    option3 = ""
    st.session_state["option1"] = option1
    st.session_state["option2"] = option2
    st.session_state["option3"] = option3

    # init the db only once 
    init_db()

else:
    qlist = st.session_state["qlist"]
    option1 =  st.session_state["option1"]
    option2 =  st.session_state["option2"]
    option3 =  st.session_state["option3"]

col1, col2, col3 = st.columns([2,2,4], border=True)
#col4 = st.columns(1,border=False)
container4 = st.container(height=300, border=True, key="Response")
response5  = st.empty()

# we do not need to save as we rebuild on every
# so get the credentials  
credentials = get_credentials()

if credentials:
    default_api_key, default_deployment_url = credentials

api_key = default_api_key
deployment_url = default_deployment_url


#print ("Do we get back here?")
st.session_state['qlist'] = qlist

#Everything is looked at from left to right
#..with col4:
    
#..    image = Image.open('1.jpg')
#.   st.image(image, use_container_width=True) #, caption='Sunrise by the mountains') 
with col1:
    #print ("Or in Col1")
    #st.header("Project")
    option1 = st.selectbox(
        'Select a Project to Analyze?',
        (  'Christmas Lane', 'Antonin Jewelry', 'ABC Software'))
    st.session_state['option1'] = option1

with col2:
    #print("Or in COl2")
    #st.header("Period")
    option2 = st.selectbox(
        'For which Reporting Period?',
        ('2024', '2023', 'Boarding'))
    st.session_state['option2'] = option2
    
with col3:
    #print("Or in COl3")
    #st.header("Action")
    #print("waiting for Input " + str(qlist))
    #st.write(" we are in col3")
    option3 = st.selectbox( "What do you need to do", options=list(qlist), accept_new_options=True)
    st.session_state['option3'] = option3
    #st.write(" we have an action  in column 3")
    #print(" History: " + str(qlist))
    
    if option3 == "Ask a new question" or not option3:
        #clear the response area
        container4.empty()
        #print( "Option 3 " + str(option3))
        search_query = ""
        #.....search_query = st.chat_input("Please enter a search query or action ")
        #print("Search_QueryA " + str(search_query))
        #print("Test New " + str(search_query not in qlist))

        if search_query and (search_query not in qlist):
            #print("Inserting " + str(search_query))
            
            qlist.insert(1, search_query)
            #print("Inserted " + str(search_query) + " History:" + str(qlist))
            st.session_state['qlist'] = qlist
            print("Session state refreshed")

        if search_query:
            print("Searching ....")
            wstring = "SearchingA " + option1 + " For " + option2 + " With " + search_query
            #st.write( wstring )
            
            # Get IBM token
            token = get_ibm_token(api_key)

            if token:
            # Perform the search query using the provided deployment
                search_response = perform_search(search_query, token, deployment_url)

                if search_response:
                    if search_response["choices"] :
                        choices = search_response["choices"][0] 
                        print( str(choices) )

            # Display the response in a formatted way
            # we need to ship this to container4 logic 
            #.if search_response:
            #.    (search_response)
    
            search_query = ""
    else:
        search_query = option3
        print("Search_QueryB " + str(search_query))
        if search_query not in qlist:
            qlist.insert(1, search_query)
        if search_query:
            wstring = "SearchingB " + option1 + " For " + option2 + " With " + search_query
            #st.write( wstring )
            # Get IBM token
            token = get_ibm_token(api_key)

            if token:
            # Perform the search query using the provided deployment
                search_response = perform_search(search_query, token, deployment_url)

                if search_response:
                    if search_response["choices"] :
                        choices = search_response["choices"][0] 
                        messages = choices['message']
                        contents = messages['content']
                        #print( str(contents) )

            # Display the response in a formatted way
            # we need to ship this to container4 logic 
            #.if search_response:
            #.    (search_response)

            search_query = ""

if search_query:
    st.write( "SearchingC " + option1 + " For Period " + option2 + " With " + search_query)
    search_query = ""

with container4:
#with response5.container():
    try:
        if search_response:
            cstring = "Response and Metrics"
            container4.write(cstring)
            #container4.write(search_response)
            if search_response["choices"] :
                choices = search_response["choices"][0] 
                messages = choices['message']
                contents = messages['content']
                container4.write(contents)
 
    except:
        cstring = "No Response Available Yet"
        container4.write(cstring)

    #try:
    #    if wstring:
    #        st.write(wstring)
    #        #response5.markdown(wstring)
    #        cstring = "Response and Metrics"
    #        container4.write(cstring)
    #        #response5.markdown(cstring)
    #except:
    #    st.write("No Response ...")
    

print("out of the loop on cols")

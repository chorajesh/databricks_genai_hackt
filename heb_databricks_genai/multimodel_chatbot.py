"""Module for chat bot UI using streamlit"""
import os
# import openai
import streamlit as st
import mlflow.deployments
from streamlit_chat import message

# Read env files
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
import requests
from io import BytesIO
from transformers import ViltProcessor, ViltForQuestionAnswering
from heb_databricks_genai.productSearch import prodsearchAgent as psa



#Initiate env file
DIR_PATH = Path(os.path.dirname(os.path.realpath(__file__)))
load_dotenv(os.path.join(DIR_PATH, ".env"))
deployment_name= "hackathon-gpt4"

bot_logo = "heb_databricks_genai/img/bot_logo.png"
HEB_logo = "heb_databricks_genai/img/heb_logo.png"


def display_product_headings():
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2], gap="small")
        with col1:
            st.markdown("**Product**")
        with col2:
            st.markdown("**Price**")
        with col3:
            st.markdown("**Category**")
        with col4:
            st.markdown("**Visit Page**")
        st.markdown("---")  # Add a line to separate the header from the products


def display_product_details(product_info):
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2], gap="small")
        with col1:
            st.markdown(f"**{product_info['name']}**")
        with col2:
            st.markdown(f"{product_info['price']}")
        with col3:
            st.markdown(f"{product_info['catg']}")
        with col4:
            st.markdown(f"[View Product]({product_info['url']})", unsafe_allow_html=True)
        st.markdown("---")  # Add a line to separate products


# Setting page title and header
st.set_page_config(
    page_title="Smart Shopper", page_icon=HEB_logo, layout="wide"
)
st.image(HEB_logo, width=150)
st.header("Smart Event-Based Shopping List Generator ")

# Initialise session state variables
if "generated" not in st.session_state:
    st.session_state["generated"] = []
if "past" not in st.session_state:
    st.session_state["past"] = []
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]


# Sidebar Let's user -
# choose model
# show total cost of current conversation
# clear the current conversation
#st.sidebar.title("Sidebar")
#model_name = "GPT-4"
counter_placeholder = st.sidebar.empty()

clear_button = st.sidebar.button("Clear Conversation", key="clear")

# reset everything
if clear_button:
    st.session_state["generated"] = []
    st.session_state["past"] = []
    st.session_state["messages"] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
# generate a response
def get_answer(image, text): #for multimodal support
    try:
        # Load and process the image
        #img = Image.open(BytesIO(image)).convert("RGB")
        processor = ViltProcessor.from_pretrained("dandelin/vilt-b32-finetuned-vqa")
        model = ViltForQuestionAnswering.from_pretrained("dandelin/vilt-b32-finetuned-vqa")

       # prepare inputs
        encoding = processor(image, text, return_tensors="pt")

        # forward pass
        outputs = model(**encoding)
        logits = outputs.logits
        idx = logits.argmax(-1).item()
        answer = model.config.id2label[idx]

        return answer

    except Exception as e:
        return str(e)


def generate_response(prompt, engine=deployment_name):

    query2 = "I'm hosting a birthday party for 15 kids. We need finger foods, non-alcoholic drinks"
    output2 = { "Event": "Birthday Party", "Number of Guests": 15, "Dietary Considerations": 'NA', "Food Preferences": 'NA', "Budget": 150, "Suggested Items": { "Appetizers": [ { "Item": "Mini Pizzas", "Price": 12, "Quantity": 3 }, { "Item": "Chicken Nuggets", "Price": 10, "Quantity": 4 }, { "Item": "Veggie Sticks with Dip", "Price": 8, "Quantity": 2 } ], "Beverages": [ { "Item": "Juice Boxes", "Price": 6, "Quantity": 4 }, { "Item": "Soda", "Price": 8, "Quantity": 3 } ], "Main Course": [ { "Item": "Cupcakes", "Price": 10, "Quantity": 3 } ], "Sides": [ { "Item": "Fresh Fruit Salad", "Price": 10, "Quantity": 2 } ], "Desserts": [ { "Item": "Ice Cream Sundae Bar", "Price": 15, "Quantity": 1 } ],"Miscellaneous": [
            {"Item": "Paper Plates", "Price": 5, "Quantity": "20"},
            {"Item": "Napkins", "Price": 3, "Quantity": "30"},
            {"Item": "Disposable Cups", "Price": 5, "Quantity": "20"}
        ] } }

    prompt = f"""As a Shopping Assistant AI, you are tasked with generating shopping lists for users based on their queries. User query
     can include details about an event, personal preferences, the number of guests, and possibly a budget. Your role is to interpret these details to suggest appropriate products for purchase.

    Please adhere to the following instructions:
    - Carefully read each user's query to identify key details: Event Name, Number of Guests, Dietary Considerations, Food Preferences, and Budget.
    - If any of these details are missing in the user's query, use 'NA' for that specific information in the output.
    - Compile a list of relevant products that align with the event type, guest preferences, dietary needs, and budget constraints, including food items, beverages, and miscellaneous essentials like cutlery.
    - Determine and include the recommended price in dollars and quantities for each product.
    - Ensure high relevance and precision in your suggestions, avoiding any unnecessary or unrelated items.
    Deliver your Output as a list of JSON objects, with no deviation. To ensure clarity and consistency, refrain from including any leading indicators like "Output:".
    Maintain clarity and consistency in your output, and ensure each key in the JSON object corresponds to a category of information from the user's query (Event, Number of Guests, Dietary Considerations, Food Preferences, Budget, Suggested Items).

    For Example:
    Comments: {query2}
    Output: {output2}
    Comments: {prompt}
    Output: """
    
    st.session_state["messages"].append({"role": "user", "content": prompt})

    client = mlflow.deployments.get_deploy_client("databricks")
    completions_response = client.predict(
    endpoint="heb_openai",
     inputs = {"messages":[{"role": "user", "content": prompt}]}
    )
    response = completions_response.choices[0]['message']['content']


    st.session_state["messages"].append({"role": "assistant", "content": response})

    return response

# container for chat history
response_container = st.container()
# container for text box
container = st.container()

with container:
    with st.form(key="my_form", clear_on_submit=True):


        # Create columns for image upload and input fields
        col1, col2 = st.columns(2)

        # Image upload
        with col1:
            uploaded_file = st.file_uploader("Do you wish to upload image", type=["jpg", "jpeg", "png"])
            
        # Question input
        with col2:
            user_input = st.text_area("You:", key="input", height=100)

            submit_button = st.form_submit_button(label="Submit")
            #question = st.text_input("Question")

    print("hi")      
    if submit_button and user_input:
        answer = ""
        if (uploaded_file is not None):
                st.image(uploaded_file, use_column_width=True)
                image = Image.open(uploaded_file)                                
                answer = get_answer(image, "What is the dish in the image")
                print(answer)

        user_input= user_input +" " + answer
        # print(user_input) 
        output = generate_response(user_input)
        print(f"Control Agent output : {output}")
        shoppinglist = psa.getShoppingList(output)

        print(f"------------- \n {shoppinglist} \n ------------------")

        st.session_state["past"].append(user_input)
        st.session_state["generated"].append(shoppinglist)

if st.session_state["generated"]:
    with response_container:
        for i in range(len(st.session_state["generated"])):
            # User chat bubble
            message(
                st.session_state["past"][i],
                is_user=True,
                key=str(i) + "_user",
                avatar_style="bottts-neutral",  # change this for different user icon
                seed="Buster",
            )  # or the seed for different user icons
            # AI chat bubble
            # Check if the message is a product dictionary
            if isinstance(st.session_state["generated"][i], dict):
                display_product_headings()
                # If it is, iterate over the dictionary and display each product
                for product_id, product_info in st.session_state["generated"][i].items():
                    if product_id != 'Error':
                        display_product_details(product_info)
            else:
                # If the message is just text, display it in a chat bubble
                message(
                    st.session_state["generated"][i],
                    key=str(i),
                    avatar_style="bottts",  # change this for different user icon
                    seed="Dusty",
                ) 

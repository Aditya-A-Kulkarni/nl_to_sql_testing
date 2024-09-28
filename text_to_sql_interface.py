#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import getpass
import os
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import GoogleGenerativeAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate, MessagesPlaceholder
import streamlit as st
from google.cloud import storage
import json

#api_key = 'AIzaSyCogpzeS47BqAVEB_kzotgR6wTKDgsyfHU'
api_key = os.getenv('API_KEY')
google_llm = GoogleGenerativeAI(model = "gemini-1.5-pro-latest", google_api_key = api_key, temperature = 0.1)
google_chat = ChatGoogleGenerativeAI(model = "gemini-1.5-pro-latest", google_api_key = api_key, temperature = 0.1)

project = 'dx-api-project'
dataset = 'madkpi_text_to_sql'
#credential_path = r"gs://nl_to_sql_credentials/credentials_json.json"

url = f'bigquery://{project}/{dataset}'#?credentials_path={credential_path}'
db = SQLDatabase.from_uri(url)

def text_to_sql (db, question):

    api_key = 'AIzaSyCogpzeS47BqAVEB_kzotgR6wTKDgsyfHU'
    google_llm = GoogleGenerativeAI(model = "gemini-1.5-pro-latest", google_api_key = api_key, temperature = 0.1)

    prefix = '''You are a Bigquery SQL expert. Given an input question, first create a syntactically correct Bigquery SQL query to run, then look at the results of the query and return the answer to the input question.
You must query only the columns that are needed to answer the question. Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
Pay attention to use the formulae for the following derived metrics - CTR (click-through rate) = clicks/impressions, Conversion Rate = conversions/impressions, Revenue eCPC = Revenue (Adv Currency) / clicks, Revenue eCPM = [Revenue (Adv Currency) / Impressions] * 1000, Revenue eCPV = Revenue (Adv Currency) / views, Video Revenue eCPCV = Revenue (Adv Currency) / complete views, Revenue eCPA = Revenue (Adv Currency) / Total conversion. DO NOT use backslash (\) to escape characters. 

Below are a few examples questions along with their corresponding SQL queries: '''

    suffix = ''' Only use the following tables:
{table_info}

Question: {input} 
SQL Query: '''

    few_shot_examples = [

    {
        "input" : "What is the total number of impressions for creative id 591714124 and AnLiv - BetterHelp on 16th August, 2024?",
        "query" : "SELECT SUM(CAST(impressions AS FLOAT64)) FROM `dx-api-project.madkpi_text_to_sql.Creative_level_table_BetterHelp` WHERE creative_id = '591714124' AND date = '2024/08/16'"
    },
    {
        "input" : "What is the total number of conversions for creative id 594460225 and AnLiv - Blue Tag on 16th August, 2024?",
        "query" : "SELECT SUM(CAST(total_conversions AS FLOAT64)) FROM `dx-api-project.madkpi_text_to_sql.Creative_level_table_Blue_Tag` WHERE creative_id = '591714124' AND date = '2024/08/16'"
    }
]

    example_prompt = PromptTemplate.from_template("Question: {input}\nSQL query: {query}")

    prompt = FewShotPromptTemplate(
    examples = few_shot_examples,
    example_prompt = example_prompt,
    prefix = prefix,
    suffix = suffix,
    input_variables = ["input", "table_info"])

    _prompt_ = PromptTemplate.from_template(prompt.format(input = question, table_info = db.table_info))

    sql_chain = _prompt_ | google_llm

    sql = sql_chain.invoke({'input' : question}).replace('```sql', '').replace('```', '')
    sql = sql.split()
    sql = ' '.join(sql)

    return sql

st.set_page_config(page_title = 'Testing Interface for NL to SQL.\nA demo DV360 database is connected to this app. Please ask relevant questions to help with the app\'s testing.')
st.header('Testing Interface for NL to SQL.\nA demo DV360 database is connected to this app. Please ask relevant questions to help with the app\'s testing.\nThis application is powered by Gemini Pro')

question = st.text_input("Input: ", key = 'input')

submit = st.button("Ask a question")

if submit:

    response = text_to_sql (db, question)
    print(response)


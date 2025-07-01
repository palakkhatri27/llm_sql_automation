import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai

# Configure Gemini API Key
genai.configure(api_key="API_KEY")  # Replace with your actual API key

# Function to create a database and table from CSV
def create_database(csv_file, db_name="my_database.db", table_name="my_table"):
    try:
        df = pd.read_csv(csv_file)
        conn = sqlite3.connect(db_name)
        df.to_sql(table_name, conn, if_exists='replace', index=False)  # Replace table if exists
        conn.close()
        return True, None  # Success
    except Exception as e:
        return False, str(e)  # Return error message

# Function to execute SQL query and fetch results
def execute_query(db_name, query):
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results, None
    except Exception as e:
        return None, str(e)

# Function to use Gemini for natural language to SQL conversion
def natural_language_to_sql(natural_language_query, table_name="my_table"):
    prompt = f"""Convert the following natural language query into a SQL query that can be executed on a table named {table_name}.
    Only return the SQL query and nothing else.

    Natural Language Query: {natural_language_query}
    SQL Query:"""

    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)

    sql_query = response.text.strip()

    # Remove Markdown formatting if present
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

    return sql_query

# Function to convert SQL query results into a natural language response
def sql_results_to_natural_language(nl_query, sql_query, sql_results):
    prompt = f"""Given the following SQL query and its results, generate a natural language response that answers the user's original question.

    User's Natural Language Query: {nl_query}

    SQL Query: {sql_query}

    Query Results: {sql_results}

    Provide a concise, human-readable response as if you were answering the user's question in plain English.
    """

    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)

    return response.text.strip()  # Extract text response

# Streamlit App
st.title("Talk to your Stock Data")

uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file is not None:
    db_created, error_message = create_database(uploaded_file)

    if db_created:
        st.success("Database created successfully!")

        user_query = st.text_input("Enter your query (natural language):")

        if st.button("Submit"):
            if user_query:
                with st.spinner("Thinking..."):
                    sql_query = natural_language_to_sql(user_query)

                    st.write("Generated SQL Query:")
                    st.code(sql_query, language="sql")  # Display SQL query

                    results, query_error = execute_query("my_database.db", sql_query)

                    if results is not None:
                        st.write("Query Results:")
                        df_results = pd.DataFrame(results)  # Convert to DataFrame
                        st.dataframe(df_results)  # Display results

                        # Convert SQL results into a natural language summary
                        natural_language_response = sql_results_to_natural_language(user_query, sql_query, results)
                        
                        st.subheader("AI Response:")
                        st.write(natural_language_response)  # Show the natural language summary

                    elif query_error:
                        st.error(f"Error executing SQL query: {query_error}")

            else:
                st.warning("Please enter a query.")
    else:
        st.error(f"Error creating database: {error_message}")


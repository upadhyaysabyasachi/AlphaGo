import gspread
import pandas as pd
import gradio as gr
import re
import os
import google.generativeai as genai
import json
import config # Import the new configuration file
from datetime import datetime

# Note: The 'oauth2client' library is deprecated.
# This script now uses 'gspread' which handles authentication with the 'google-auth' library.
# Please ensure you have it installed: pip install gspread google-auth google-generativeai

# ------------------------------
# 1. Configuration & Setup
# ------------------------------
# --- Google Sheets Setup ---
try:
    client = gspread.service_account(filename="service_account.json")
    SHEET_NAME = "Galaxy Renters Information"
    sheet = client.open(SHEET_NAME).sheet1
    data = pd.DataFrame(sheet.get_all_records())

    required_cols = ["PROPERTY ADDRESS", "UNIT", "TENANT", "PROPERTY", "LEASE START", "LEASE END", "TENANT PHONE", "TENANT EMAIL"]
    if not all(col in data.columns for col in required_cols):
        raise ValueError("One or more required columns are missing from the Google Sheet.")

    # Ensure UNIT is treated as a string to avoid floating point issues (e.g., 8.0)
    data['UNIT'] = data['UNIT'].astype(str)
    data["LookupKey"] = data["PROPERTY ADDRESS"].astype(str) + " " + data["UNIT"]
    
    # --- New Date Processing Logic ---
    # Clean and convert LEASE END to datetime objects for comparison.
    # This handles various formats and text like "month".
    data['LEASE END'] = data['LEASE END'].astype(str).str.replace(' month', '', case=False)
    data['LEASE END_dt'] = pd.to_datetime(data['LEASE END'], errors='coerce')

    print("Successfully connected to Google Sheets and loaded data.")

except Exception as e:
    print(f"Error connecting to Google Sheets: {e}")
    data = pd.DataFrame()

# --- Gemini LLM Setup ---
try:
    # Get the API key from the config.py file
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "YOUR_API_KEY_HERE":
        raise ValueError("GEMINI_API_KEY not set in config.py. Please add your key.")
    genai.configure(api_key=config.GEMINI_API_KEY)
    llm = genai.GenerativeModel('gemini-1.5-flash-latest')
    print("Gemini LLM successfully configured.")
except Exception as e:
    print(f"Error configuring Gemini LLM: {e}")
    llm = None

# ------------------------------
# 2. LLM-Powered NLP Parser
# ------------------------------
def interpret_query_with_llm(query):
    """Uses the LLM to classify the query and parse it into a structured format."""
    if not llm:
        return {"error": "LLM not configured. Please check your API key in config.py."}

    current_date = datetime.now().strftime('%Y-%m-%d')

    prompt = f"""
    First, classify the user's query into one of two categories: 'internal_lookup' or 'general_question'.
    - 'internal_lookup' is for questions specifically about tenants, properties, leases, contact information, addresses, or units.
    - 'general_question' is for everything else, such as facts, definitions, or general knowledge questions.

    Today's date is {current_date}.

    If the query is an 'internal_lookup', analyze it to extract specific information. The available fields are:
    - "lease_expired" (for leases that have already ended before today's date)
    - "lease_end" (for lease expiration date)
    - "lease_start" (for move-in or lease beginning)
    - "tenant_name" (when asking 'who' lives somewhere)
    - "email", "phone"
    - "full_record" (for a general overview)

    Analyze this query: "{query}"

    Return your answer as a single JSON object.
    - If it is a 'general_question', the JSON must have one key: "query_type": "general_question".
    - If it is an 'internal_lookup', the JSON must have four keys: "query_type": "internal_lookup", "tenant": "...", "address": "...", and "field": "...".
    """
    try:
        response = llm.generate_content(prompt)
        clean_response = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_response)
    except Exception as e:
        print(f"LLM parsing failed: {e}")
        # Fallback to internal lookup if parsing fails
        return {"tenant": "", "address": "", "field": "full_record", "query_type": "internal_lookup"}

# ------------------------------
# 3. General Question Answering
# ------------------------------
def answer_general_question(query):
    """Answers a general knowledge question using the LLM."""
    if not llm:
        return "LLM not configured. Please check your API key in config.py."

    prompt = f"Please provide a concise and helpful answer to the following question: {query}"
    try:
        response = llm.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error answering general question: {e}")
        return "Sorry, I was unable to answer that question."

# ------------------------------
# 4. Smart Lookup Function
# ------------------------------
def smart_lookup(query):
    """
    Routes the query to either the internal database lookup or a general QA function.
    """
    if data.empty and not llm:
        error_msg = "Error: Could not load data from Google Sheets and LLM is not configured."
        return error_msg, gr.update(visible=False), ""

    parsed_query = interpret_query_with_llm(query)
    if "error" in parsed_query:
        return parsed_query["error"], gr.update(visible=False), ""

    # --- New Routing Logic ---
    query_type = parsed_query.get("query_type")
    if query_type == 'general_question':
        answer = answer_general_question(query)
        return answer, gr.update(visible=False, choices=[]), ""

    # --- Internal Lookup Logic ---
    if data.empty:
        return "Error: Could not load data from Google Sheets.", gr.update(visible=False), ""

    # Safely handle potential None values from the LLM
    tenant_value = parsed_query.get("tenant")
    tenant_query = tenant_value.strip().lower() if tenant_value else ""
    
    address_value = parsed_query.get("address")
    address_query = address_value.strip().lower() if address_value else ""

    field = parsed_query.get("field", "full_record")
    matches = data.copy()
    search_type = "LLM Search"

    if field == 'lease_expired':
        today = pd.to_datetime('today').normalize()
        matches = matches[matches['LEASE END_dt'] < today].dropna(subset=['LEASE END_dt'])
        search_type = "Expired Leases"

    if tenant_query:
        matches = matches[matches["TENANT"].str.lower().str.contains(tenant_query, na=False)]
    
    if address_query:
        # --- NEW FLEXIBLE SEARCH LOGIC ---
        # Pre-process the address query to remove common noise words like 'apt' or 'unit'
        processed_address_query = re.sub(r'\b(apt|unit|apartment)\b', '', address_query, flags=re.IGNORECASE)
        
        # Create a flexible regex pattern from the cleaned query
        address_pattern = re.sub(r'[\s,.-]+', r'\\s*', processed_address_query).strip()
        
        # Search using the flexible pattern
        matches = matches[matches["LookupKey"].str.lower().str.contains(address_pattern, na=False, regex=True)]
    
    # Fallback search if other filters yield no results
    if matches.empty and (tenant_query or address_query):
        matches = data[data.apply(lambda row: query.lower() in str(row).lower(), axis=1)]

    if matches.empty:
        return "No matching record found. Please try a different query.", gr.update(choices=[], visible=False), query

    # Limit results to avoid overwhelming the user
    if len(matches) > 10:
        matches = matches.head(10)
         
    results = [format_result(row, search_type, field) for _, row in matches.iterrows()]
    return "\n\n".join(results), gr.update(choices=[], visible=False), query

# ------------------------------
# 5. Helper: Format Results
# ------------------------------
def format_result(row, search_type, field):
    """Formats a single record into a readable string based on the requested field."""
    tenant_info = f"{row.get('TENANT', 'N/A')} ({row.get('PROPERTY ADDRESS', 'N/A')} {row.get('UNIT', 'N/A')})"
    if field == "lease_end" or field == "lease_expired":
        return f"📅 Lease End Date for {tenant_info}: {row.get('LEASE END', 'N/A')}"
    elif field == "lease_start":
        return f"📅 Lease Start Date for {tenant_info}: {row.get('LEASE START', 'N/A')}"
    elif field == "tenant_name":
        return f"👤 Tenant at {row.get('PROPERTY ADDRESS', 'N/A')} {row.get('UNIT', 'N/A')}: {row.get('TENANT', 'N/A')}"
    elif field == "email":
        return f"📧 Tenant Email for {tenant_info}: {row.get('TENANT EMAIL', 'N/A')}"
    elif field == "phone":
        return f"📱 Tenant Phone for {tenant_info}: {row.get('TENANT PHONE', 'N/A')}"
    else:
        return f"""
✅ Record Found (Search by {search_type}):
- Tenant: {row.get('TENANT', 'N/A')}
- Property: {row.get('PROPERTY', 'N/A')}
- Address: {row.get('PROPERTY ADDRESS', 'N/A')}
- Unit: {row.get('UNIT', 'N/A')}
- Lease: {row.get('LEASE START', 'N/A')} → {row.get('LEASE END', 'N/A')}
- Contact: {row.get('TENANT PHONE', 'N/A')}, {row.get('TENANT EMAIL', 'N/A')}
        """.strip()

# ------------------------------
# 6. Handle Dropdown Selection
# ------------------------------
def show_selected(selected_option, original_query):
    if not selected_option:
        return gr.update(), gr.update()

    parsed_query = interpret_query_with_llm(original_query)
    field = parsed_query.get("field", "full_record")

    try:
        tenant_name = selected_option.split(" (")[0]
        address_unit = selected_option.split(" (")[1][:-1]
    except IndexError:
        return "❌ Invalid selection format.", gr.update(visible=False)

    match = data[(data["TENANT"] == tenant_name) & (data["LookupKey"] == address_unit)]

    if match.empty:
        return "❌ Could not find the selected record.", gr.update(visible=False)

    row = match.iloc[0]
    result = format_result(row, "Dropdown Selection", field)
    return result, gr.update(visible=False)

# ------------------------------
# 7. UI Interaction Functions
# ------------------------------
def clear_all():
    """Clears all input and output components."""
    return "", "", gr.update(choices=[], visible=False), ""

# ------------------------------
# 8. Gradio UI
# ------------------------------
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🏠 Tenant Lookup & General Q&A Tool (Powered by Gemini)")
    gr.Markdown("Ask tenant questions like 'Who lives at 14 Barton Ct?', or general questions like 'What is the capital of France?'.")

    with gr.Row():
        query = gr.Textbox(label="Ask a question", scale=4, placeholder="Type your question here...")
        submit = gr.Button("Search", variant="primary", scale=1)
        clear = gr.Button("Clear")

    output = gr.Textbox(label="Result", lines=10, interactive=False)
    dropdown = gr.Dropdown(choices=[], visible=False, label="Multiple matches found. Please select one.")

    state_query = gr.State()

    submit.click(fn=smart_lookup, inputs=query, outputs=[output, dropdown, state_query])
    dropdown.change(fn=show_selected, inputs=[dropdown, state_query], outputs=[output, dropdown])
    clear.click(fn=clear_all, inputs=None, outputs=[query, output, dropdown, state_query])

demo.launch()


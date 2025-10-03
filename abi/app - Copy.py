import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import gradio as gr
import re

# ------------------------------
# 1. Connect to Google Sheets
# ------------------------------
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

SHEET_NAME = "Galaxy Renters Information"  # Change to your sheet name
sheet = client.open(SHEET_NAME).sheet1
data = pd.DataFrame(sheet.get_all_records())

# Create lookup key
data["LookupKey"] = data["PROPERTY ADDRESS"].astype(str) + " " + data["UNIT"].astype(str)

# ------------------------------
# 2. Fallback NLP Parser
# ------------------------------
def interpret_query(query):
    query = query.lower()

    if "lease end" in query or "end date" in query or "expire" in query:
        return "lease_end"
    elif "lease start" in query or "begin" in query or "move in" in query:
        return "lease_start"
    elif "who" in query or "tenant" in query or "name" in query:
        return "tenant_name"
    elif "email" in query:
        return "email"
    elif "phone" in query or "contact" in query or "number" in query:
        return "phone"
    else:
        return "full_record"

# ------------------------------
# 3. Smart Lookup Function with Clickable Summary
# ------------------------------
def smart_lookup(query):
    query_lower = query.strip().lower()

    # Detect search type
    if re.search(r"\d+", query_lower) or any(word in query_lower for word in ["st", "ct", "ln", "rd", "ave", "run", "dr"]):
        matches = data[data["LookupKey"].str.lower().str.contains(query_lower, na=False)]
        search_type = "Property + Unit"
    else:
        matches = data[data["TENANT"].str.lower().str.contains(query_lower, na=False)]
        search_type = "Tenant Name"

    if matches.empty:
        return "No matching record found. Try different wording or update the sheet.", gr.update(choices=[], visible=False) 

    field = interpret_query(query_lower)

    # If too many results, show dropdown to refine
    if len(matches) > 3:
        options = [f"{row['TENANT']} ({row['PROPERTY ADDRESS']} {row['UNIT']})" for _, row in matches.iterrows()]
        return f"{len(matches)} found {len(matches)} possible matches. Please select one:", gr.update(choices=options, visible=True)

    # Else, return full results immediately
    results = []
    for _, row in matches.iterrows():
        results.append(format_result(row, search_type, field))
    return "\n\n".join(results), gr.update(choices=[], visible=False)

# ------------------------------
# 4. Helper: Format Results
# ------------------------------
def format_result(row, search_type, field):
    if field == "lease_end":
        return f"📅 Lease End Date for {row['TENANT']} ({row['PROPERTY ADDRESS']} {row['UNIT']}): {row['LEASE END']}"
    elif field == "lease_start":
        return f"📅 Lease Start Date for {row['TENANT']} ({row['PROPERTY ADDRESS']} {row['UNIT']}): {row['LEASE START']}"
    elif field == "tenant_name":
        return f"👤 Tenant at {row['PROPERTY ADDRESS']} {row['UNIT']}: {row['TENANT']}"
    elif field == "email":
        return f"📧 Tenant Email for {row['TENANT']} ({row['PROPERTY ADDRESS']} {row['UNIT']}): {row['TENANT EMAIL']}"
    elif field == "phone":
        return f"📱 Tenant Phone for {row['TENANT']} ({row['PROPERTY ADDRESS']} {row['UNIT']}): {row['TENANT PHONE']}"
    else:
        return f"""
        ✅ Record Found (Search by {search_type}):
        - Tenant: {row['TENANT']}
        - Property: {row['PROPERTY']}
        - Address: {row['PROPERTY ADDRESS']}
        - Unit: {row['UNIT']}
        - Lease: {row['LEASE START']} → {row['LEASE END']}
        - Contact: {row['TENANT PHONE']}, {row['TENANT EMAIL']}
        """

# ------------------------------
# 5. Handle Dropdown Selection
# ------------------------------
def show_selected(selected_option, field):
    if not selected_option:
        return "❌ No selection made."

    # Extract tenant + address from dropdown
    tenant_name = selected_option.split(" (")[0]
    address_unit = selected_option.split(" (")[1][:-1]  # remove ")"

    match = data[(data["TENANT"] == tenant_name) & (data["LookupKey"] == address_unit)]
    if match.empty:
        return "❌ Could not find record after selection."

    row = match.iloc[0]
    return format_result(row, "Dropdown Selection", field)

# ------------------------------
# 6. Gradio UI
# ------------------------------
with gr.Blocks() as demo:
    gr.Markdown("## 🏠 Internal Tenant/Unit Lookup Tool (Clickable Summary Mode)")
    gr.Markdown("Ask: 'Who lives at 14 Barton Ct?', 'Show me all Smith tenants', 'What’s the lease end date for John Doe?'.")
    
    query = gr.Textbox(label="Ask a question")
    output = gr.Textbox(label="Result", lines=12)
    dropdown = gr.Dropdown(choices=[], visible=False, label="Select a match to view details")
    
    submit = gr.Button("Search")
    submit.click(fn=smart_lookup, inputs=query, outputs=[output, dropdown])
    
    dropdown.change(fn=lambda choice: show_selected(choice, interpret_query(query.value)), inputs=dropdown, outputs=output)

demo.launch()

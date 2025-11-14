# import streamlit as st
# import json
# import os
# import hashlib
# import re
# import pandas as pd
# import imaplib
# import email
# from email.header import decode_header
# import io
# import datetime
# from utils.pdf_parser import read_pdf_from_streamlit
# from utils.data_extractor import extract_invoice_data, is_invoice_text
# from utils.csv_helper import save_to_csv
# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.base import MIMEBase
# from email import encoders

# # ---------------- Fetch History Helpers ---------------- #
# FETCH_HISTORY_FILE = "data/fetch_history.json"

# def load_fetch_history():
#     if os.path.exists(FETCH_HISTORY_FILE):
#         with open(FETCH_HISTORY_FILE, "r") as f:
#             return json.load(f)
#     return {}

# def save_fetch_history(history):
#     with open(FETCH_HISTORY_FILE, "w") as f:
#         json.dump(history, f, indent=4)

# def get_fetch_key(email, start_date, end_date):
#     return f"{email}|{start_date}|{end_date}"


# # ---------------- Utility Functions ---------------- #
# USERS_FILE = "users.json"

# def load_users():
#     if os.path.exists(USERS_FILE):
#         with open(USERS_FILE, "r") as f:
#             return json.load(f)
#     return {}

# def save_users(users):
#     with open(USERS_FILE, "w") as f:
#         json.dump(users, f, indent=4)

# def make_hash(password):
#     return hashlib.sha256(password.encode()).hexdigest()

# def validate_password(password):
#     if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
#         return False
#     return True

# def validate_email(email):
#     pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
#     return re.match(pattern, email) is not None

# def add_user(name, email, password):
#     users = load_users()
#     if email in users:
#         return False
#     users[email] = {"name": name, "password": make_hash(password)}
#     save_users(users)
#     return True

# def check_user(identifier, password):
#     users = load_users()
#     hashed = make_hash(password)
#     # Check if identifier is an email/username in users
#     if identifier in users:
#         user_record = users[identifier]
#         if isinstance(user_record, dict):
#             if user_record.get("password") == hashed:
#                 return user_record
#             else:
#                 raise ValueError("Invalid password.")
#         else:
#             raise ValueError("Corrupted user record. Please contact support.")
#     # Check by username
#     for info in users.values():
#         if isinstance(info, dict) and info.get("name", "").lower() == identifier.lower():
#             if info.get("password") == hashed:
#                 return info
#             else:
#                 raise ValueError("Invalid password.")
#     # If not found
#     raise ValueError("User not found. Please sign up first.")

# # ---------------- Helper to fetch PDFs from Email ---------------- #
# def _decode_header_part(hdr):
#     try:
#         dh = decode_header(hdr)
#         parts = []
#         for part, enc in dh:
#             if isinstance(part, bytes):
#                 parts.append(part.decode(enc or "utf-8", errors="ignore"))
#             else:
#                 parts.append(part)
#         return "".join(parts)
#     except:
#         return hdr

# def fetch_pdfs_from_email(email_user, email_pass, imap_server="imap.gmail.com", folder="INBOX", start_date=None, end_date=None):
#     try:
#         mail = imaplib.IMAP4_SSL(imap_server, timeout=30)
#         mail.login(email_user, email_pass)
#         mail.select(folder)
#         search_criteria = "ALL"
#         if start_date and end_date:
#             start_str = start_date.strftime("%d-%b-%Y")
#             end_str = (end_date + datetime.timedelta(days=1)).strftime("%d-%b-%Y")
#             search_criteria = f'(SINCE {start_str} BEFORE {end_str})'

#         status, messages = mail.search(None, search_criteria)
#         if status != "OK":
#             mail.logout()
#             return {"error": f"IMAP search failed with status {status}"}

#         email_ids = messages[0].split()
#         if not email_ids:
#             mail.logout()
#             return {"files": []}

#         pdf_files = []
#         progress_bar = st.progress(0, text="Fetching emails...")
#         for idx, e_id in enumerate(email_ids, start=1):
#             status, data = mail.fetch(e_id, "(RFC822)")
#             if status != "OK" or not data or not data[0]:
#                 continue
#             raw_email = data[0][1]
#             msg = email.message_from_bytes(raw_email)
#             for part in msg.walk():
#                 if part.get_content_maintype() == "multipart":
#                     continue
#                 content_disposition = part.get("Content-Disposition", "")
#                 if not content_disposition:
#                     continue
#                 filename = part.get_filename()
#                 if filename:
#                     filename = _decode_header_part(filename)
#                 if filename and filename.lower().endswith(".pdf"):
#                     file_bytes = part.get_payload(decode=True)
#                     if file_bytes:
#                         pdf_files.append((filename, file_bytes))
#             progress_bar.progress(idx / len(email_ids), text=f"Fetching emails... {idx}/{len(email_ids)}")
#         mail.logout()
#         progress_bar.empty()
#         return {"files": pdf_files}
#     except imaplib.IMAP4.error as e:
#         return {"error": f"IMAP authentication/connection error: {str(e)}"}
#     except Exception as e:
#         return {"error": f"Unexpected error: {str(e)}"}

# # ---------------- Authentication Pages ---------------- #
# def login_page():
#     st.title("🔐 Login to Invoice Data Extractor")
#     with st.form("login_form"):
#         identifier = st.text_input("Email or Username")
#         password = st.text_input("Password", type="password")
#         login_btn = st.form_submit_button("Login")

#     if login_btn:
#         try:
#             user = check_user(identifier, password)
#             st.session_state["authenticated"] = True
#             st.session_state["user_name"] = user["name"]
#             st.session_state["current_page"] = "input_source"
#             st.success(f"Welcome {user['name']}! 🎉")
#             st.rerun()
#         except ValueError as ve:
#             st.error(str(ve))
#         except Exception as e:
#             st.error("An unexpected error occurred. Please contact support.")

#     if st.button("👉 Don't have an account? Sign Up"):
#         st.session_state["auth_page"] = "Sign Up"
#         st.rerun()

# def signup_page():
#     st.title("📝 Create a New Account")
#     with st.form("signup_form"):
#         name = st.text_input("Full Name / Username")
#         email_id = st.text_input("Email")
#         password = st.text_input("Password", type="password")
#         confirm_password = st.text_input("Confirm Password", type="password")
#         submit = st.form_submit_button("Sign Up")

#     if submit:
#         if not validate_email(email_id):
#             st.error("❌ Please enter a valid email address.")
#         elif password != confirm_password:
#             st.error("Passwords do not match.")
#         elif not validate_password(password):
#             st.error("Password must be at least 8 characters long and contain letters and numbers.")
#         elif add_user(name, email_id, password):
#             st.success("✅ Account created successfully! Please login.")
#             st.session_state["auth_page"] = "Login"
#             st.rerun()
#         else:
#             st.error("User already exists with this email.")

#     if st.button("🔑 Already have an account? Login"):
#         st.session_state["auth_page"] = "Login"
#         st.rerun()

# # ---------------- Input Source Page ---------------- #
# class FakeUpload(io.BytesIO):
#     def __init__(self, name, content_bytes):
#         super().__init__(content_bytes)
#         self.name = name


# def input_source_page():
#     st.title("📂 Select Input Source")
#     st.sidebar.success(f"Logged in as {st.session_state['user_name']}")

#     # --- Show fetch history in sidebar ---
#     fetch_history = load_fetch_history()
#     if fetch_history:
#         st.sidebar.markdown("### 📁 Previous Fetches")
#         # Group by email
#         from collections import defaultdict
#         email_to_ranges = defaultdict(list)
#         for key, meta in fetch_history.items():
#             email, start, end = key.split("|")
#             email_to_ranges[email].append((start, end, key, meta))

#         for email, ranges in email_to_ranges.items():
#             st.sidebar.markdown(f"<span style='font-size: 0.95em;'>{email}</span>", unsafe_allow_html=True)
#             btn_label = "View/Download 📥"
#             if st.sidebar.button(btn_label, key=f"view_{email}"):
#                 st.session_state['show_ranges_for_email'] = email
#                 st.rerun()
#             # If this email is selected, show its date ranges with delete option
#             if st.session_state.get('show_ranges_for_email') == email:
#                 for start, end, key, meta in sorted(ranges):
#                     cols = st.sidebar.columns([3,1])
#                     range_label = f"{start} to {end}"
#                     with cols[0]:
#                         if st.button(range_label, key=f"range_{key}"):
#                             st.session_state['saved_fetch'] = meta
#                             st.session_state['current_page'] = 'saved_data'
#                             st.session_state['show_ranges_for_email'] = None
#                             st.rerun()
#                     with cols[1]:
#                         if st.button("🗑️", key=f"delete_{key}", help="Delete this fetch"):
#                             # Remove from fetch_history and save
#                             fetch_history.pop(key, None)
#                             save_fetch_history(fetch_history)
#                             st.session_state['show_ranges_for_email'] = email
#                             st.rerun()

#     if st.sidebar.button("🚪 Logout"):
#         st.session_state["authenticated"] = False
#         st.session_state["auth_page"] = "Login"
#         st.rerun()

#     input_method = st.radio("Choose Input Method", ["Upload PDFs", "Fetch from Email"])
#     uploaded_files = []

#     if input_method == "Upload PDFs":
#         uploaded_files = st.file_uploader("Upload PDF invoices", type=["pdf"], accept_multiple_files=True)
#         if uploaded_files:
#             st.session_state["uploaded_files"] = uploaded_files

#     else:  # Fetch from Email
#         st.markdown("### 📧 Enter Email Credentials (use App Password for Gmail)")
#         email_user = st.text_input("Email Address")
#         email_pass = st.text_input("App Password", type="password")
#         imap_server = st.text_input("IMAP Server", value="imap.gmail.com")

#         today = datetime.date.today()
#         date_input = st.date_input(
#             "Select date range:",
#             value=(today, today),
#             min_value=today - datetime.timedelta(days=30),
#             max_value=today
#         )
#         start_date, end_date = date_input if isinstance(date_input, tuple) and len(date_input) == 2 else (None, None)

#         fetch_btn = st.button("📥 Fetch Emails")
#         if fetch_btn:
#             if not email_user or not email_pass:
#                 st.error("Please enter both email address and app password.")
#             elif not start_date or not end_date:
#                 st.error("Please select a valid date range first.")
#             else:
#                 # --- New logic: Only fetch dates not already fetched ---
#                 from datetime import timedelta
#                 def daterange(start, end):
#                     for n in range((end - start).days + 1):
#                         yield start + timedelta(n)

#                 # Collect all already fetched dates for this email
#                 fetched_dates = set()
#                 for k in fetch_history:
#                     em, s, e = k.split("|")
#                     if em == email_user:
#                         s_dt = datetime.datetime.strptime(s, "%Y-%m-%d").date()
#                         e_dt = datetime.datetime.strptime(e, "%Y-%m-%d").date()
#                         for d in daterange(s_dt, e_dt):
#                             fetched_dates.add(d)

#                 req_start = start_date
#                 req_end = end_date
#                 to_fetch = [d for d in daterange(req_start, req_end) if d not in fetched_dates]
#                 already_fetched = [d for d in daterange(req_start, req_end) if d in fetched_dates]

#                 if not to_fetch:
#                     # All dates already fetched
#                     st.info("All data for this date range already fetched.")
#                     # Find the fetch key(s) covering these dates
#                     for k, meta in fetch_history.items():
#                         em, s, e = k.split("|")
#                         if em == email_user:
#                             s_dt = datetime.datetime.strptime(s, "%Y-%m-%d").date()
#                             e_dt = datetime.datetime.strptime(e, "%Y-%m-%d").date()
#                             if s_dt <= req_start and e_dt >= req_end:
#                                 st.markdown(f"[View/Download previously fetched data for {s} to {e}](#)")
#                                 if st.button(f"Go to {s} to {e}", key=f"goto_{k}"):
#                                     st.session_state['saved_fetch'] = meta
#                                     st.session_state['current_page'] = 'saved_data'
#                                     st.rerun()
#                     return

#                 # If some dates are already fetched, notify user
#                 if already_fetched:
#                     st.info(f"Data for these dates already fetched: {', '.join(str(d) for d in already_fetched)}")
#                     # Optionally, provide a link to the relevant fetch
#                     for k, meta in fetch_history.items():
#                         em, s, e = k.split("|")
#                         if em == email_user:
#                             s_dt = datetime.datetime.strptime(s, "%Y-%m-%d").date()
#                             e_dt = datetime.datetime.strptime(e, "%Y-%m-%d").date()
#                             overlap = [d for d in already_fetched if s_dt <= d <= e_dt]
#                             if overlap:
#                                 st.markdown(f"[View/Download data for {s} to {e}](#)")
#                                 if st.button(f"Go to {s} to {e}", key=f"goto_{k}"):
#                                     st.session_state['saved_fetch'] = meta
#                                     st.session_state['current_page'] = 'saved_data'
#                                     st.rerun()

#                 # Only fetch the new dates
#                 fetch_start = min(to_fetch)
#                 fetch_end = max(to_fetch)
#                 with st.spinner(f"⏳ Fetching emails for {fetch_start} to {fetch_end}..."):
#                     resp = fetch_pdfs_from_email(email_user, email_pass, imap_server, "INBOX", fetch_start, fetch_end)
#                     if "error" in resp:
#                         st.error(f"❌ Failed to fetch: {resp['error']}")
#                     else:
#                         files = resp.get("files", [])
#                         if not files:
#                             st.warning("No PDF attachments were found.")
#                         else:
#                             st.success(f"✅ Found {len(files)} PDF attachments")
#                             st.session_state["uploaded_files"] = [FakeUpload(fname, content) for fname, content in files]
#                             st.session_state["fetch_meta"] = {
#                                 "email": email_user,
#                                 "start_date": str(fetch_start),
#                                 "end_date": str(fetch_end)
#                             }

#         # Show Next: Extract Data button only after fetch
#         if st.session_state.get("uploaded_files"):
#             if st.button("➡️ Next: Extract Data"):
#                 st.session_state["current_page"] = "output_options"
#                 st.rerun()

# def send_email_with_attachments(sender_email, sender_pass, recipient_email, subject, body, attachments):
#     try:
#         msg = MIMEMultipart()
#         msg['From'] = sender_email
#         msg['To'] = recipient_email
#         msg['Subject'] = subject

#         # Attach the email body
#         msg.attach(MIMEBase('text', 'plain'))
#         msg.attachments = []

#         # Attach files
#         for file_path in attachments:
#             part = MIMEBase('application', 'octet-stream')
#             with open(file_path, 'rb') as f:
#                 part.set_payload(f.read())
#             encoders.encode_base64(part)
#             part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
#             msg.attach(part)

#         # Connect and send
#         server = smtplib.SMTP('smtp.gmail.com', 587)
#         server.starttls()
#         server.login(sender_email, sender_pass)
#         server.send_message(msg)
#         server.quit()
#         return True, "Email sent successfully!"
#     except Exception as e:
#         return False, str(e)

# def output_options_page():
#     st.title("📑 Invoice Data Extractor - Output Options")
#     uploaded_files = st.session_state.get("uploaded_files", [])
#     extracted_data_list = []

#     valid_invoices = []
#     flattened_rows = []

#     for idx, uploaded_file in enumerate(uploaded_files, start=1):
#         st.subheader(f"📄 {uploaded_file.name}")
#         try:
#             pdf_text = read_pdf_from_streamlit(uploaded_file)
#         except Exception as e:
#             st.error(f"Failed to read PDF {uploaded_file.name}: {e}")
#             continue

#         invoice_data = extract_invoice_data(pdf_text) if is_invoice_text(pdf_text) else None
#         if isinstance(invoice_data, str):
#             cleaned = re.sub(r"```json|```", "", invoice_data, flags=re.IGNORECASE).strip()
#             json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
#             if json_match:
#                 cleaned = json_match.group(0)
#             try:
#                 invoice_data = json.loads(cleaned)
#             except:
#                 invoice_data = None

#         if not invoice_data or not invoice_data.get("Invoice Number"):
#             st.warning("⚠️ Skipped: Not a valid invoice or missing Invoice Number.")
#             continue

#         valid_invoices.append(invoice_data)
#         st.write(f"**Invoice Number:** {invoice_data.get('Invoice Number')}")
#         st.write(f"**User Name:** {invoice_data.get('User Name', 'N/A')}")

#         # Flatten this invoice and add to flattened_rows
#         invoice_number = invoice_data.get("Invoice Number", "")
#         user_name = invoice_data.get("User Name", "")
#         due_date = invoice_data.get("Due Date", "")
#         total_amount = invoice_data.get("Total Amount", "")
#         product_details = invoice_data.get("Product Details", [])
#         if isinstance(product_details, list):
#             for product in product_details:
#                 flattened_rows.append({
#                     "Invoice Number": invoice_number,
#                     "User Name": user_name,
#                     "Due Date": due_date,
#                     "Item Name": product.get("name", ""),
#                     "Quantity": product.get("quantity", ""),
#                     "Price": product.get("price", ""),
#                     "Total": product.get("total", ""),
#                     "Invoice Total Amount": total_amount
#                 })
#         else:
#             flattened_rows.append({
#                 "Invoice Number": invoice_number,
#                 "User Name": user_name,
#                 "Due Date": due_date,
#                 "Item Name": "",
#                 "Quantity": "",
#                 "Price": "",
#                 "Total": "",
#                 "Invoice Total Amount": total_amount
#             })

#     if not valid_invoices:
#         st.info("No valid invoices to download or process.")
#         return

#     # ---------------- Download Options ---------------- #
#     st.markdown("### ⬇️ Download Options")
#     col1, col2 = st.columns(2)
#     import io
#     import pandas as pd
#     df_flat = pd.DataFrame(flattened_rows)
#     # Save CSV/XLSX to disk for fetch history and email attachments
#     combined_csv_path = "data/exports/all_invoices.csv"
#     combined_xlsx_path = "data/exports/all_invoices.xlsx"
#     df_flat.to_csv(combined_csv_path, index=False)
#     df_flat.to_excel(combined_xlsx_path, index=False)
#     # For instant download
#     csv_buffer = io.StringIO()
#     df_flat.to_csv(csv_buffer, index=False)
#     st.download_button("📥 Download All (CSV)", data=csv_buffer.getvalue(), file_name="all_invoices.csv", mime="text/csv")
#     xlsx_buffer = io.BytesIO()
#     df_flat.to_excel(xlsx_buffer, index=False)
#     st.download_button("📥 Download All (Excel)", data=xlsx_buffer.getvalue(), file_name="all_invoices.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

#     with col2:
#         if len(valid_invoices) > 1:
#             for idx, invoice in enumerate(valid_invoices, start=1):
#                 inv_num = invoice.get("Invoice Number", f"Invoice_{idx}")
#                 safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', str(inv_num))
#                 # Flatten the invoice to row-per-item format
#                 rows = []
#                 invoice_number = invoice.get("Invoice Number", "")
#                 user_name = invoice.get("User Name", "")
#                 due_date = invoice.get("Due Date", "")
#                 total_amount = invoice.get("Total Amount", "")
#                 product_details = invoice.get("Product Details", [])
#                 if isinstance(product_details, list):
#                     for product in product_details:
#                         rows.append({
#                             "Invoice Number": invoice_number,
#                             "User Name": user_name,
#                             "Due Date": due_date,
#                             "Item Name": product.get("name", ""),
#                             "Quantity": product.get("quantity", ""),
#                             "Price": product.get("price", ""),
#                             "Total": product.get("total", ""),
#                             "Invoice Total Amount": total_amount
#                         })
#                 else:
#                     rows.append({
#                         "Invoice Number": invoice_number,
#                         "User Name": user_name,
#                         "Due Date": due_date,
#                         "Item Name": "",
#                         "Quantity": "",
#                         "Price": "",
#                         "Total": "",
#                         "Invoice Total Amount": total_amount
#                     })
#                 import io
#                 import pandas as pd
#                 df_flat = pd.DataFrame(rows)
#                 csv_buffer = io.StringIO()
#                 df_flat.to_csv(csv_buffer, index=False)
#                 st.download_button(
#                     f"📥 {safe_name}.csv",
#                     data=csv_buffer.getvalue(),
#                     file_name=f"{safe_name}.csv",
#                     mime="text/csv",
#                     key=f"invoice_{idx}_download"
#                 )

#     # Save fetch history if coming from email fetch
#     if "fetch_meta" in st.session_state:
#         fetch_meta = st.session_state.pop("fetch_meta")
#         fetch_key = get_fetch_key(fetch_meta["email"], fetch_meta["start_date"], fetch_meta["end_date"])
#         fetch_history = load_fetch_history()
#         fetch_history[fetch_key] = {
#             "files": [f.name for f in uploaded_files],
#             "invoices": valid_invoices,
#             "csv": combined_csv_path,
#             "xlsx": combined_xlsx_path
#         }
#         save_fetch_history(fetch_history)

#     # ---------------- Back Button ---------------- #
#     if st.button("⬅️ Back to Input Selection"):
#         st.session_state["current_page"] = "input_source"
#         st.rerun()

#     # ---------------- Email Sending ---------------- #
#     st.markdown("### 📧 Send Valid Invoices via Email")
#     with st.form("email_form"):
#         sender_email = st.text_input("Your Email (Gmail recommended)")
#         sender_pass = st.text_input("App Password", type="password")
#         recipient_email = st.text_input("Recipient Email")
#         email_subject = st.text_input("Subject", "Invoice Data")
#         email_body = st.text_area("Email Body", "Hello,\n\nPlease find the attached invoice data.\n\nRegards")
#         send_btn = st.form_submit_button("Send Email")

#     if send_btn:
#         attachments = [combined_csv_path, combined_xlsx_path]
#         if not sender_email or not sender_pass or not recipient_email:
#             st.error("Please fill all email fields.")
#         else:
#             with st.spinner("📤 Sending email..."):
#                 success, msg = send_email_with_attachments(sender_email, sender_pass, recipient_email, email_subject, email_body, attachments)
#                 if success:
#                     st.success("✅ " + msg)
#                 else:
#                     st.error("❌ " + msg)

# # ---------------- Saved Data Page ---------------- #
# def saved_data_page():
#     meta = st.session_state.get('saved_fetch')
#     if not meta:
#         st.warning("No saved data selected.")
#         return
#     st.title("📁 Previously Fetched Invoice Data")
#     st.write("**Invoices:**")
#     invoices = meta.get("invoices", [])
#     import io
#     import pandas as pd
#     import re
#     # Show fetch date range at the top
#     fetch_key = None
#     fetch_history = load_fetch_history()
#     for k, v in fetch_history.items():
#         if v == meta:
#             fetch_key = k
#             break
#     fetch_range = ""
#     if fetch_key:
#         email, start, end = fetch_key.split("|")
#         fetch_range = f"**Fetched for:** {email}  **Date Range:** {start} to {end}"
#         st.markdown(fetch_range)
#     st.markdown("### Invoice Details")
#     for idx, inv in enumerate(invoices, start=1):
#         col1, col2 = st.columns([3, 1])
#         with col1:
#             st.write(f"**Invoice Number:** {inv.get('Invoice Number')}")
#             st.write(f"**User Name:** {inv.get('User Name', 'N/A')}")
#         with col2:
#             safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', str(inv.get("Invoice Number", f"Invoice_{idx}")))
#             # Flatten the invoice to row-per-item format
#             rows = []
#             invoice_number = inv.get("Invoice Number", "")
#             user_name = inv.get("User Name", "")
#             due_date = inv.get("Due Date", "")
#             total_amount = inv.get("Total Amount", "")
#             product_details = inv.get("Product Details", [])
#             if isinstance(product_details, list):
#                 for product in product_details:
#                     rows.append({
#                         "Invoice Number": invoice_number,
#                         "User Name": user_name,
#                         "Due Date": due_date,
#                         "Item Name": product.get("name", ""),
#                         "Quantity": product.get("quantity", ""),
#                         "Price": product.get("price", ""),
#                         "Total": product.get("total", ""),
#                         "Invoice Total Amount": total_amount
#                     })
#             else:
#                 rows.append({
#                     "Invoice Number": invoice_number,
#                     "User Name": user_name,
#                     "Due Date": due_date,
#                     "Item Name": "",
#                     "Quantity": "",
#                     "Price": "",
#                     "Total": "",
#                     "Invoice Total Amount": total_amount
#                 })
#             import io
#             import pandas as pd
#             df_flat = pd.DataFrame(rows)
#             csv_buffer = io.StringIO()
#             df_flat.to_csv(csv_buffer, index=False)
#             st.download_button(
#                 "⬇️ CSV",
#                 data=csv_buffer.getvalue(),
#                 file_name=f"{safe_name}.csv",
#                 mime="text/csv",
#                 key=f"invoice_{idx}_download"
#             )
#     # Download all invoices as one file if possible
#     # Always provide download for all invoices in memory, even if files are missing
#     import io
#     import pandas as pd
#     from utils.csv_helper import save_to_csv
#     # Flatten invoices to row-per-item format
#     invoices = meta.get("invoices", [])
#     # Use the same logic as save_to_csv but in-memory
#     rows = []
#     for invoice in invoices:
#         invoice_number = invoice.get("Invoice Number", "")
#         user_name = invoice.get("User Name", "")
#         due_date = invoice.get("Due Date", "")
#         total_amount = invoice.get("Total Amount", "")
#         product_details = invoice.get("Product Details", [])
#         if isinstance(product_details, list):
#             for product in product_details:
#                 rows.append({
#                     "Invoice Number": invoice_number,
#                     "User Name": user_name,
#                     "Due Date": due_date,
#                     "Item Name": product.get("name", ""),
#                     "Quantity": product.get("quantity", ""),
#                     "Price": product.get("price", ""),
#                     "Total": product.get("total", ""),
#                     "Invoice Total Amount": total_amount
#                 })
#         else:
#             rows.append({
#                 "Invoice Number": invoice_number,
#                 "User Name": user_name,
#                 "Due Date": due_date,
#                 "Item Name": "",
#                 "Quantity": "",
#                 "Price": "",
#                 "Total": "",
#                 "Invoice Total Amount": total_amount
#             })
#     df_flat = pd.DataFrame(rows)
#     csv_buffer = io.StringIO()
#     df_flat.to_csv(csv_buffer, index=False)
#     st.download_button("📥 Download All (CSV)", data=csv_buffer.getvalue(), file_name="all_invoices.csv", mime="text/csv")
#     xlsx_buffer = io.BytesIO()
#     df_flat.to_excel(xlsx_buffer, index=False)
#     st.download_button("📥 Download All (Excel)", data=xlsx_buffer.getvalue(), file_name="all_invoices.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
#     if st.button("⬅️ Back to Input Selection"):
#         st.session_state["current_page"] = "input_source"
#         st.rerun()

#     # --- Email Sending Section ---
#     st.markdown("### 📧 Send These Invoices via Email")
#     with st.form("saved_email_form"):
#         sender_email = st.text_input("Your Email (Gmail recommended)", key="saved_sender_email")
#         sender_pass = st.text_input("App Password", type="password", key="saved_sender_pass")
#         recipient_email = st.text_input("Recipient Email", key="saved_recipient_email")
#         email_subject = st.text_input("Subject", "Invoice Data", key="saved_email_subject")
#         email_body = st.text_area("Email Body", "Hello,\n\nPlease find the attached invoice data.\n\nRegards", key="saved_email_body")
#         send_btn = st.form_submit_button("Send Email")

#     if send_btn:
#         attachments = []
#         if "csv" in meta and os.path.exists(meta["csv"]):
#             attachments.append(meta["csv"])
#             # Always generate Excel from the normalized CSV for email
#             import pandas as pd
#             combined_xlsx = "all_invoices.xlsx"
#             df_flat = pd.read_csv(meta["csv"])
#             df_flat.to_excel(combined_xlsx, index=False)
#             attachments.append(combined_xlsx)
#         if not sender_email or not sender_pass or not recipient_email:
#             st.error("Please fill all email fields.")
#         elif not attachments:
#             st.error("No files available to send.")
#         else:
#             with st.spinner("📤 Sending email..."):
#                 success, msg = send_email_with_attachments(sender_email, sender_pass, recipient_email, email_subject, email_body, attachments)
#                 if success:
#                     st.success("✅ " + msg)
#                 else:
#                     st.error("❌ " + msg)
# # ---------------- Main Controller ---------------- #
# if "authenticated" not in st.session_state:
#     st.session_state["authenticated"] = False
# if "auth_page" not in st.session_state:
#     st.session_state["auth_page"] = "Login"
# if "current_page" not in st.session_state:
#     st.session_state["current_page"] = "input_source"

# if not st.session_state["authenticated"]:
#     if st.session_state["auth_page"] == "Login":
#         login_page()
#     else:
#         signup_page()
# else:
#     if st.session_state["current_page"] == "input_source":
#         input_source_page()
#     elif st.session_state["current_page"] == "output_options":
#         output_options_page()
#     elif st.session_state["current_page"] == "saved_data":
#         saved_data_page()


import streamlit as st
import json
import os
import hashlib
import re
import pandas as pd
import imaplib
import email
from email.header import decode_header
import io
import datetime
from utils.pdf_parser import read_pdf_from_streamlit
from utils.data_extractor import extract_invoice_data, is_invoice_text
from utils.csv_helper import save_to_csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# ---------------- Fetch History Helpers ---------------- #
FETCH_HISTORY_FILE = "data/fetch_history.json"

def load_fetch_history():
    if os.path.exists(FETCH_HISTORY_FILE):
        with open(FETCH_HISTORY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_fetch_history(history):
    with open(FETCH_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def get_fetch_key(email, start_date, end_date):
    return f"{email}|{start_date}|{end_date}"


# ---------------- Utility Functions ---------------- #
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def make_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_password(password):
    if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        return False
    return True

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def add_user(name, email, password):
    users = load_users()
    if email in users:
        return False
    users[email] = {"name": name, "password": make_hash(password)}
    save_users(users)
    return True

def check_user(identifier, password):
    users = load_users()
    hashed = make_hash(password)
    # Check if identifier is an email/username in users
    if identifier in users:
        user_record = users[identifier]
        if isinstance(user_record, dict):
            if user_record.get("password") == hashed:
                return user_record
            else:
                raise ValueError("Invalid password.")
        else:
            raise ValueError("Corrupted user record. Please contact support.")
    # Check by username
    for info in users.values():
        if isinstance(info, dict) and info.get("name", "").lower() == identifier.lower():
            if info.get("password") == hashed:
                return info
            else:
                raise ValueError("Invalid password.")
    # If not found
    raise ValueError("User not found. Please sign up first.")

# ---------------- Helper to fetch PDFs from Email ---------------- #
def _decode_header_part(hdr):
    try:
        dh = decode_header(hdr)
        parts = []
        for part, enc in dh:
            if isinstance(part, bytes):
                parts.append(part.decode(enc or "utf-8", errors="ignore"))
            else:
                parts.append(part)
        return "".join(parts)
    except:
        return hdr

def fetch_pdfs_from_email(email_user, email_pass, imap_server="imap.gmail.com", folder="INBOX", start_date=None, end_date=None):
    try:
        mail = imaplib.IMAP4_SSL(imap_server, timeout=30)
        mail.login(email_user, email_pass)
        mail.select(folder)
        search_criteria = "ALL"
        if start_date and end_date:
            start_str = start_date.strftime("%d-%b-%Y")
            end_str = (end_date + datetime.timedelta(days=1)).strftime("%d-%b-%Y")
            search_criteria = f'(SINCE {start_str} BEFORE {end_str})'

        status, messages = mail.search(None, search_criteria)
        if status != "OK":
            mail.logout()
            return {"error": f"IMAP search failed with status {status}"}

        email_ids = messages[0].split()
        if not email_ids:
            mail.logout()
            return {"files": []}

        pdf_files = []
        progress_bar = st.progress(0, text="Fetching emails...")
        for idx, e_id in enumerate(email_ids, start=1):
            status, data = mail.fetch(e_id, "(RFC822)")
            if status != "OK" or not data or not data[0]:
                continue
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            for part in msg.walk():
                if part.get_content_maintype() == "multipart":
                    continue
                content_disposition = part.get("Content-Disposition", "")
                if not content_disposition:
                    continue
                filename = part.get_filename()
                if filename:
                    filename = _decode_header_part(filename)
                if filename and filename.lower().endswith(".pdf"):
                    file_bytes = part.get_payload(decode=True)
                    if file_bytes:
                        pdf_files.append((filename, file_bytes))
            progress_bar.progress(idx / len(email_ids), text=f"Fetching emails... {idx}/{len(email_ids)}")
        mail.logout()
        progress_bar.empty()
        return {"files": pdf_files}
    except imaplib.IMAP4.error as e:
        return {"error": f"IMAP authentication/connection error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

# ---------------- Authentication Pages ---------------- #
def login_page():
    st.title("🔐 Login to Invoice Data Extractor")
    with st.form("login_form"):
        identifier = st.text_input("Email or Username")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")

    if login_btn:
        try:
            user = check_user(identifier, password)
            st.session_state["authenticated"] = True
            st.session_state["user_name"] = user["name"]
            st.session_state["current_page"] = "input_source"
            st.success(f"Welcome {user['name']}! 🎉")
            st.rerun()
        except ValueError as ve:
            st.error(str(ve))
        except Exception as e:
            st.error("An unexpected error occurred. Please contact support.")

    if st.button("👉 Don't have an account? Sign Up"):
        st.session_state["auth_page"] = "Sign Up"
        st.rerun()

def signup_page():
    st.title("📝 Create a New Account")
    with st.form("signup_form"):
        name = st.text_input("Full Name / Username")
        email_id = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Sign Up")

    if submit:
        if not validate_email(email_id):
            st.error("❌ Please enter a valid email address.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        elif not validate_password(password):
            st.error("Password must be at least 8 characters long and contain letters and numbers.")
        elif add_user(name, email_id, password):
            st.success("✅ Account created successfully! Please login.")
            st.session_state["auth_page"] = "Login"
            st.rerun()
        else:
            st.error("User already exists with this email.")

    if st.button("🔑 Already have an account? Login"):
        st.session_state["auth_page"] = "Login"
        st.rerun()


# ---------------- Sidebar Fetch History (Global) ---------------- #
def sidebar_fetch_history():
    st.sidebar.success(f"Logged in as {st.session_state['user_name']}")
    fetch_history = load_fetch_history()
    if fetch_history:
        st.sidebar.markdown("### 📁 Previous Fetches")
        from collections import defaultdict
        email_to_ranges = defaultdict(list)
        for key, meta in fetch_history.items():
            email, start, end = key.split("|")
            email_to_ranges[email].append((start, end, key, meta))

        for email, ranges in email_to_ranges.items():
            st.sidebar.markdown(f"<span style='font-size: 0.95em;'>{email}</span>", unsafe_allow_html=True)
            btn_label = "View/Download 📥"
            if st.sidebar.button(btn_label, key=f"view_{email}"):
                st.session_state['show_ranges_for_email'] = email
                # Do not rerun here, let the main page continue
            if st.session_state.get('show_ranges_for_email') == email:
                for idx, (start, end, key, meta) in enumerate(sorted(ranges)):
                    cols = st.sidebar.columns([3,1])
                    range_label = f"{start} to {end}"
                    with cols[0]:
                        if st.button(range_label, key=f"range_{key}_{idx}"):
                            st.session_state['saved_fetch'] = meta
                            st.session_state['current_page'] = 'saved_data'
                            st.session_state['show_ranges_for_email'] = None
                            # Do not rerun here, let the main page continue
                    with cols[1]:
                        if st.button("🗑️", key=f"delete_{key}_{idx}", help="Delete this fetch"):
                            fetch_history.pop(key, None)
                            save_fetch_history(fetch_history)
                            st.session_state['show_ranges_for_email'] = email
                            # Do not rerun here, let the main page continue
    if st.sidebar.button("🚪 Logout"):
        st.session_state["authenticated"] = False
        st.session_state["auth_page"] = "Login"
        st.rerun()


# ---------------- Input Source Page ---------------- #
class FakeUpload(io.BytesIO):
    def __init__(self, name, content_bytes):
        super().__init__(content_bytes)
        self.name = name

def input_source_page():
    st.title("📂 Select Input Source")
    fetch_history = load_fetch_history()


    input_method = st.radio("Choose Input Method", ["Upload PDFs", "Fetch from Email"])
    uploaded_files = []

    if input_method == "Upload PDFs":
        uploaded_files = st.file_uploader("Upload PDF invoices", type=["pdf"], accept_multiple_files=True)
        if uploaded_files:
            st.session_state["uploaded_files"] = uploaded_files

    else:  # Fetch from Email
        st.markdown("### 📧 Enter Email Credentials (use App Password for Gmail)")
        email_user = st.text_input("Email Address")
        email_pass = st.text_input("App Password", type="password")
        imap_server = st.text_input("IMAP Server", value="imap.gmail.com")

        today = datetime.date.today()
        date_input = st.date_input(
            "Select date range:",
            value=(today, today),
            min_value=today - datetime.timedelta(days=30),
            max_value=today
        )
        start_date, end_date = date_input if isinstance(date_input, tuple) and len(date_input) == 2 else (None, None)

        fetch_btn = st.button("📥 Fetch Emails")
        if fetch_btn:
            if not email_user or not email_pass:
                st.error("Please enter both email address and app password.")
            elif not start_date or not end_date:
                st.error("Please select a valid date range first.")
            else:
                # --- New logic: Only fetch dates not already fetched ---
                from datetime import timedelta
                def daterange(start, end):
                    for n in range((end - start).days + 1):
                        yield start + timedelta(n)

                # Collect all already fetched dates for this email
                fetched_dates = set()
                for k in fetch_history:
                    em, s, e = k.split("|")
                    if em == email_user:
                        s_dt = datetime.datetime.strptime(s, "%Y-%m-%d").date()
                        e_dt = datetime.datetime.strptime(e, "%Y-%m-%d").date()
                        for d in daterange(s_dt, e_dt):
                            fetched_dates.add(d)

                req_start = start_date
                req_end = end_date
                to_fetch = [d for d in daterange(req_start, req_end) if d not in fetched_dates]
                already_fetched = [d for d in daterange(req_start, req_end) if d in fetched_dates]

                if not to_fetch:
                    # All dates already fetched
                    st.info("All data for this date range already fetched.")
                    # Find the fetch key(s) covering these dates
                    for k, meta in fetch_history.items():
                        em, s, e = k.split("|")
                        if em == email_user:
                            s_dt = datetime.datetime.strptime(s, "%Y-%m-%d").date()
                            e_dt = datetime.datetime.strptime(e, "%Y-%m-%d").date()
                            if s_dt <= req_start and e_dt >= req_end:
                                if st.button(f"View/Download data for {s} to {e}", key=f"viewdl_{k}"):
                                    st.session_state['saved_fetch'] = meta
                                    st.session_state['current_page'] = 'saved_data'
                                    st.rerun()
                    return

                # If some dates are already fetched, notify user
                if already_fetched:
                    st.info(f"Data for these dates already fetched: {', '.join(str(d) for d in already_fetched)}")
                    # Provide a button to view/download the relevant fetch
                    for k, meta in fetch_history.items():
                        em, s, e = k.split("|")
                        if em == email_user:
                            s_dt = datetime.datetime.strptime(s, "%Y-%m-%d").date()
                            e_dt = datetime.datetime.strptime(e, "%Y-%m-%d").date()
                            overlap = [d for d in already_fetched if s_dt <= d <= e_dt]
                            if overlap:
                                if st.button(f"View/Download data for {s} to {e}", key=f"viewdl_{k}"):
                                    st.session_state['saved_fetch'] = meta
                                    st.session_state['current_page'] = 'saved_data'
                                    st.rerun()

                # Only fetch the new dates (to_fetch)
                if to_fetch:
                    # Fetch all unfetched dates in a single call as a range
                    fetch_start = min(to_fetch)
                    fetch_end = max(to_fetch)
                    merged_invoices = []
                    merged_files = []
                    for k, meta in fetch_history.items():
                        em, s, e = k.split("|")
                        if em == email_user:
                            s_dt = datetime.datetime.strptime(s, "%Y-%m-%d").date()
                            e_dt = datetime.datetime.strptime(e, "%Y-%m-%d").date()
                            if not (e_dt < req_start or s_dt > req_end):
                                merged_invoices.extend(meta.get("invoices", []))
                                merged_files.extend(meta.get("files", []))
                    all_files = merged_files[:]
                    all_uploaded_files = []
                    with st.spinner(f"⏳ Fetching emails for {fetch_start} to {fetch_end}..."):
                        resp = fetch_pdfs_from_email(email_user, email_pass, imap_server, "INBOX", fetch_start, fetch_end)
                        if "error" in resp:
                            st.error(f"❌ Failed to fetch: {resp['error']}")
                        else:
                            files = resp.get("files", [])
                            all_files += [fname for fname, _ in files]
                            all_uploaded_files += [FakeUpload(fname, content) for fname, content in files]
                    st.session_state["uploaded_files"] = all_uploaded_files
                    st.session_state["fetch_meta"] = {
                        "email": email_user,
                        "start_date": str(req_start),
                        "end_date": str(req_end),
                        "merged_invoices": merged_invoices,
                        "merged_files": all_files
                    }

        # Show Next: Extract Data button if there are any files to process (even if some dates are already fetched)
        uploaded_files = st.session_state.get("uploaded_files")
        if uploaded_files is not None and len(uploaded_files) > 0:
            if st.button("➡️ Next: Extract Data"):
                st.session_state["current_page"] = "output_options"
                st.rerun()

def send_email_with_attachments(sender_email, sender_pass, recipient_email, subject, body, attachments):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        # Attach the email body
        msg.attach(MIMEBase('text', 'plain'))
        msg.attachments = []

        # Attach files
        for file_path in attachments:
            part = MIMEBase('application', 'octet-stream')
            with open(file_path, 'rb') as f:
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
            msg.attach(part)

        # Connect and send
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_pass)
        server.send_message(msg)
        server.quit()
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)

def output_options_page():
    st.title("📑 Invoice Data Extractor - Output Options")
    uploaded_files = st.session_state.get("uploaded_files", [])
    fetch_meta = st.session_state.get("fetch_meta", {})
    # Use merged_invoices if present (for combined fetches)
    valid_invoices = fetch_meta.get("merged_invoices", [])[:]
    flattened_rows = []
    # Only extract from uploaded_files (newly fetched)
    for idx, uploaded_file in enumerate(uploaded_files, start=1):
        st.subheader(f"📄 {uploaded_file.name}")
        try:
            pdf_text = read_pdf_from_streamlit(uploaded_file)
        except Exception as e:
            st.error(f"Failed to read PDF {uploaded_file.name}: {e}")
            continue
        invoice_data = extract_invoice_data(pdf_text) if is_invoice_text(pdf_text) else None
        if isinstance(invoice_data, str):
            cleaned = re.sub(r"```json|```", "", invoice_data, flags=re.IGNORECASE).strip()
            json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if json_match:
                cleaned = json_match.group(0)
            try:
                invoice_data = json.loads(cleaned)
            except:
                invoice_data = None
        if not invoice_data or not invoice_data.get("Invoice Number"):
            st.warning("⚠️ Skipped: Not a valid invoice or missing Invoice Number.")
            continue
        valid_invoices.append(invoice_data)
        st.write(f"**Invoice Number:** {invoice_data.get('Invoice Number')}")
        st.write(f"**User Name:** {invoice_data.get('User Name', 'N/A')}")
    # Flatten all invoices (merged + new)
    for invoice_data in valid_invoices:
        invoice_number = invoice_data.get("Invoice Number", "")
        user_name = invoice_data.get("User Name", "")
        due_date = invoice_data.get("Due Date", "")
        total_amount = invoice_data.get("Total Amount", "")
        product_details = invoice_data.get("Product Details", [])
        if isinstance(product_details, list):
            for product in product_details:
                flattened_rows.append({
                    "Invoice Number": invoice_number,
                    "User Name": user_name,
                    "Due Date": due_date,
                    "Item Name": product.get("name", ""),
                    "Quantity": product.get("quantity", ""),
                    "Price": product.get("price", ""),
                    "Total": product.get("total", ""),
                    "Invoice Total Amount": total_amount
                })
        else:
            flattened_rows.append({
                "Invoice Number": invoice_number,
                "User Name": user_name,
                "Due Date": due_date,
                "Item Name": "",
                "Quantity": "",
                "Price": "",
                "Total": "",
                "Invoice Total Amount": total_amount
            })
    if not valid_invoices:
        st.info("No valid invoices to download or process.")
        return

    # ---------------- Download Options ---------------- #
    st.markdown("### ⬇️ Download Options")
    col1, col2 = st.columns(2)
    import io
    import pandas as pd
    df_flat = pd.DataFrame(flattened_rows)
    # Save CSV/XLSX to disk for fetch history and email attachments
    combined_csv_path = "data/exports/all_invoices.csv"
    combined_xlsx_path = "data/exports/all_invoices.xlsx"
    df_flat.to_csv(combined_csv_path, index=False)
    df_flat.to_excel(combined_xlsx_path, index=False)
    # For instant download, use saved file if exists
    if os.path.exists(combined_csv_path):
        with open(combined_csv_path, "r", encoding="utf-8") as f:
            csv_data = f.read()
    else:
        csv_buffer = io.StringIO()
        df_flat.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
    st.download_button("📥 Download All (CSV)", data=csv_data, file_name="all_invoices.csv", mime="text/csv")
    if os.path.exists(combined_xlsx_path):
        with open(combined_xlsx_path, "rb") as f:
            xlsx_data = f.read()
    else:
        xlsx_buffer = io.BytesIO()
        df_flat.to_excel(xlsx_buffer, index=False)
        xlsx_data = xlsx_buffer.getvalue()
    st.download_button("📥 Download All (Excel)", data=xlsx_data, file_name="all_invoices.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with col2:
        # Only show one download button per unique invoice number
        seen_invoice_numbers = set()
        for idx, invoice in enumerate(valid_invoices, start=1):
            inv_num = invoice.get("Invoice Number", f"Invoice_{idx}")
            if inv_num in seen_invoice_numbers:
                continue
            seen_invoice_numbers.add(inv_num)
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', str(inv_num))
            # Flatten the invoice to row-per-item format
            rows = []
            invoice_number = invoice.get("Invoice Number", "")
            user_name = invoice.get("User Name", "")
            due_date = invoice.get("Due Date", "")
            total_amount = invoice.get("Total Amount", "")
            product_details = invoice.get("Product Details", [])
            if isinstance(product_details, list):
                for product in product_details:
                    rows.append({
                        "Invoice Number": invoice_number,
                        "User Name": user_name,
                        "Due Date": due_date,
                        "Item Name": product.get("name", ""),
                        "Quantity": product.get("quantity", ""),
                        "Price": product.get("price", ""),
                        "Total": product.get("total", ""),
                        "Invoice Total Amount": total_amount
                    })
            else:
                rows.append({
                    "Invoice Number": invoice_number,
                    "User Name": user_name,
                    "Due Date": due_date,
                    "Item Name": "",
                    "Quantity": "",
                    "Price": "",
                    "Total": "",
                    "Invoice Total Amount": total_amount
                })
            import io
            import pandas as pd
            df_flat = pd.DataFrame(rows)
            csv_buffer = io.StringIO()
            df_flat.to_csv(csv_buffer, index=False)
            st.download_button(
                f"📥 {safe_name}.csv",
                data=csv_buffer.getvalue(),
                file_name=f"{safe_name}.csv",
                mime="text/csv",
                key=f"invoice_{safe_name}_download"
            )

    # Save fetch history if coming from email fetch
    if "fetch_meta" in st.session_state:
        fetch_meta = st.session_state.pop("fetch_meta")
        fetch_key = get_fetch_key(fetch_meta["email"], fetch_meta["start_date"], fetch_meta["end_date"])
        fetch_history = load_fetch_history()
        # Merge files from fetch_meta if present
        files_to_save = fetch_meta.get("merged_files", []) + [f.name for f in uploaded_files]
        fetch_history[fetch_key] = {
            "files": files_to_save,
            "invoices": valid_invoices,
            "csv": combined_csv_path,
            "xlsx": combined_xlsx_path
        }
        save_fetch_history(fetch_history)

    # ---------------- Back Button ---------------- #
    if st.button("⬅️ Back to Input Selection"):
        st.session_state["current_page"] = "input_source"
        # Clear all session state related to fetch/upload to avoid re-processing
        for key in ["uploaded_files", "fetch_meta", "saved_fetch", "show_ranges_for_email"]:
            st.session_state.pop(key, None)
        st.rerun()

    # ---------------- Email Sending ---------------- #
    st.markdown("### 📧 Send Valid Invoices via Email")
    with st.form("email_form"):
        sender_email = st.text_input("Your Email (Gmail recommended)")
        sender_pass = st.text_input("App Password", type="password")
        recipient_email = st.text_input("Recipient Email")
        email_subject = st.text_input("Subject", "Invoice Data")
        email_body = st.text_area("Email Body", "Hello,\n\nPlease find the attached invoice data.\n\nRegards")
        send_btn = st.form_submit_button("Send Email")

    if send_btn:
        attachments = [combined_csv_path, combined_xlsx_path]
        if not sender_email or not sender_pass or not recipient_email:
            st.error("Please fill all email fields.")
        else:
            with st.spinner("📤 Sending email..."):
                success, msg = send_email_with_attachments(sender_email, sender_pass, recipient_email, email_subject, email_body, attachments)
                if success:
                    st.success("✅ " + msg)
                else:
                    st.error("❌ " + msg)

# ---------------- Saved Data Page ---------------- #
def saved_data_page():
    meta = st.session_state.get('saved_fetch')
    if not meta:
        st.warning("No saved data selected.")
        return
    st.title("📁 Previously Fetched Invoice Data")
    st.write("**Invoices:**")
    invoices = meta.get("invoices", [])
    import io
    import pandas as pd
    import re
    # Show fetch date range at the top
    fetch_key = None
    fetch_history = load_fetch_history()
    for k, v in fetch_history.items():
        if v == meta:
            fetch_key = k
            break
    fetch_range = ""
    if fetch_key:
        email, start, end = fetch_key.split("|")
        fetch_range = f"**Fetched for:** {email}  **Date Range:** {start} to {end}"
        st.markdown(fetch_range)
    st.markdown("### Invoice Details")
    for idx, inv in enumerate(invoices, start=1):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**Invoice Number:** {inv.get('Invoice Number')}")
            st.write(f"**User Name:** {inv.get('User Name', 'N/A')}")
        with col2:
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', str(inv.get("Invoice Number", f"Invoice_{idx}")))
            # Flatten the invoice to row-per-item format
            rows = []
            invoice_number = inv.get("Invoice Number", "")
            user_name = inv.get("User Name", "")
            due_date = inv.get("Due Date", "")
            total_amount = inv.get("Total Amount", "")
            product_details = inv.get("Product Details", [])
            if isinstance(product_details, list):
                for product in product_details:
                    rows.append({
                        "Invoice Number": invoice_number,
                        "User Name": user_name,
                        "Due Date": due_date,
                        "Item Name": product.get("name", ""),
                        "Quantity": product.get("quantity", ""),
                        "Price": product.get("price", ""),
                        "Total": product.get("total", ""),
                        "Invoice Total Amount": total_amount
                    })
            else:
                rows.append({
                    "Invoice Number": invoice_number,
                    "User Name": user_name,
                    "Due Date": due_date,
                    "Item Name": "",
                    "Quantity": "",
                    "Price": "",
                    "Total": "",
                    "Invoice Total Amount": total_amount
                })
            import io
            import pandas as pd
            df_flat = pd.DataFrame(rows)
            csv_buffer = io.StringIO()
            df_flat.to_csv(csv_buffer, index=False)
            st.download_button(
                "⬇️ CSV",
                data=csv_buffer.getvalue(),
                file_name=f"{safe_name}.csv",
                mime="text/csv",
                key=f"invoice_{idx}_download"
            )
    # Download all invoices as one file if possible
    # Always provide download for all invoices in memory, even if files are missing
    import io
    import pandas as pd
    from utils.csv_helper import save_to_csv
    # Flatten invoices to row-per-item format
    invoices = meta.get("invoices", [])
    # Use the same logic as save_to_csv but in-memory
    rows = []
    for invoice in invoices:
        invoice_number = invoice.get("Invoice Number", "")
        user_name = invoice.get("User Name", "")
        due_date = invoice.get("Due Date", "")
        total_amount = invoice.get("Total Amount", "")
        product_details = invoice.get("Product Details", [])
        if isinstance(product_details, list):
            for product in product_details:
                rows.append({
                    "Invoice Number": invoice_number,
                    "User Name": user_name,
                    "Due Date": due_date,
                    "Item Name": product.get("name", ""),
                    "Quantity": product.get("quantity", ""),
                    "Price": product.get("price", ""),
                    "Total": product.get("total", ""),
                    "Invoice Total Amount": total_amount
                })
        else:
            rows.append({
                "Invoice Number": invoice_number,
                "User Name": user_name,
                "Due Date": due_date,
                "Item Name": "",
                "Quantity": "",
                "Price": "",
                "Total": "",
                "Invoice Total Amount": total_amount
            })
    df_flat = pd.DataFrame(rows)
    csv_buffer = io.StringIO()
    df_flat.to_csv(csv_buffer, index=False)
    st.download_button("📥 Download All (CSV)", data=csv_buffer.getvalue(), file_name="all_invoices.csv", mime="text/csv")
    xlsx_buffer = io.BytesIO()
    df_flat.to_excel(xlsx_buffer, index=False)
    st.download_button("📥 Download All (Excel)", data=xlsx_buffer.getvalue(), file_name="all_invoices.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if st.button("⬅️ Back to Input Selection"):
        st.session_state["current_page"] = "input_source"
        # Clear saved_fetch to avoid re-processing
        st.session_state.pop("saved_fetch", None)
        st.rerun()

    # --- Email Sending Section ---
    st.markdown("### 📧 Send These Invoices via Email")
    with st.form("saved_email_form"):
        sender_email = st.text_input("Your Email (Gmail recommended)", key="saved_sender_email")
        sender_pass = st.text_input("App Password", type="password", key="saved_sender_pass")
        recipient_email = st.text_input("Recipient Email", key="saved_recipient_email")
        email_subject = st.text_input("Subject", "Invoice Data", key="saved_email_subject")
        email_body = st.text_area("Email Body", "Hello,\n\nPlease find the attached invoice data.\n\nRegards", key="saved_email_body")
        send_btn = st.form_submit_button("Send Email")

    if send_btn:
        attachments = []
        if "csv" in meta and os.path.exists(meta["csv"]):
            attachments.append(meta["csv"])
            # Always generate Excel from the normalized CSV for email
            import pandas as pd
            combined_xlsx = "all_invoices.xlsx"
            df_flat = pd.read_csv(meta["csv"])
            df_flat.to_excel(combined_xlsx, index=False)
            attachments.append(combined_xlsx)
        if not sender_email or not sender_pass or not recipient_email:
            st.error("Please fill all email fields.")
        elif not attachments:
            st.error("No files available to send.")
        else:
            with st.spinner("📤 Sending email..."):
                success, msg = send_email_with_attachments(sender_email, sender_pass, recipient_email, email_subject, email_body, attachments)
                if success:
                    st.success("✅ " + msg)
                else:
                    st.error("❌ " + msg)
# ---------------- Main Controller ---------------- #
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "auth_page" not in st.session_state:
    st.session_state["auth_page"] = "Login"
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "input_source"

if not st.session_state["authenticated"]:
    if st.session_state["auth_page"] == "Login":
        login_page()
    else:
        signup_page()
else:
    sidebar_fetch_history()
    if st.session_state["current_page"] == "input_source":
        input_source_page()
    elif st.session_state["current_page"] == "output_options":
        output_options_page()
    elif st.session_state["current_page"] == "saved_data":
        saved_data_page()

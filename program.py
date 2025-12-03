import streamlit as st
import gspread
import datetime

# Terminal -> streamlit run program.py

st.set_page_config(
    page_title="Cafe Order Chatbot",
    layout="centered"
)

menu_list = {
    "Beverage": {
        "Caramel Macchiato": 500,
        "Cold Brew": 400,
        "Earl Grey Tea": 300,
        "Java Chip Frappe": 700,
        "Vanilla Latte": 600,
    },
    "Food": {
        "Biscuit": 200,
        "Croissant": 400,
        "Donut": 300,
        "Naan": 600,
        "Sandwich": 500,
    }
}

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1nBCmdsigsspTA2B3zAHOt8PhZv_O2G2OG-T5uEM7sis/edit?usp=sharing"
SHEET_NAME = "Orders"

@st.cache_resource(ttl=3600)
def get_sheets_client():
    try:
        creds = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(creds)
        spreadsheet = gc.open_by_url(SPREADSHEET_URL)
        return spreadsheet.worksheet(SHEET_NAME)
    except Exception as e:
        st.error(f"Error connecting: {e}")
        return None
    
def write_order_to_sheet(order_data):
    sheet = get_sheets_client()
    if sheet is None:
        return False
    try:
        sheet.append_row(order_data)
        return True
    except Exception as e:
        st.error(f"Error writing: {e}")
        return False

# Initialize
if 'order' not in st.session_state:
    st.session_state.order = []
if 'step' not in st.session_state:
    st.session_state.step = "welcome"
if 'customer_name' not in st.session_state:
    st.session_state.customer_name = None
if 'name_error' not in st.session_state:
    st.session_state.name_error = None
if 'current_category' not in st.session_state:
    st.session_state.current_category = None
if 'current_item' not in st.session_state:
    st.session_state.current_item = None
if 'current_price' not in st.session_state:
    st.session_state.current_price = 0

# Functions
def reset_current_selection():
    st.session_state.current_category = None
    st.session_state.current_item = None
    st.session_state.current_price = 0

def calculate_total(order):
    return sum(item['total'] for item in order)

# on_click Functions
def set_step(new_step):
    st.session_state.step = new_step

def process_customer_name(name_input):
    clean_name = name_input.strip()

    if not clean_name:
        st.session_state.name_error = "Please enter a valid name."
        return

    only_letters_spaces = True
    for char in clean_name:
        if not char.isalpha() and not char.isspace():
            only_letters_spaces = False
            break

    if only_letters_spaces:
        st.session_state.customer_name = clean_name.title()
        st.session_state.step = "start"
        st.session_state.name_error = None
    else:
        st.session_state.name_error = "Name must only contain letters and spaces."

def set_category(category_name):
    st.session_state.current_category = category_name
    st.session_state.step = "select_item"

def handle_item_selection(selected_item, category):
    st.session_state.current_item = selected_item
    st.session_state.current_price = menu_list[category][selected_item]
    st.session_state.step = "select_quantity"

def handle_add_order(item, price, quantity):
    st.session_state.order.append({
        "item": item,
        "price": price,
        "quantity": quantity,
        "total": price * quantity
    })
    reset_current_selection()
    st.session_state.step = "start"

def handle_clear_cart():
    st.session_state.order = []
    st.session_state.step = "start"

def handle_confirm_order():
    grand_total = calculate_total(st.session_state.order)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in st.session_state.order:
        data_row = [
            timestamp,
            st.session_state.customer_name,
            item['item'],
            item['quantity'],
            item['price'],
            item['total'],
            grand_total
        ]
        if not write_order_to_sheet(data_row):
            st.warning("Error saving.")
            
    st.session_state.step = "thanks"

def reset_app_state():
    st.session_state.order = []
    st.session_state.step = "welcome"
    st.session_state.customer_name = None
    st.session_state.name_error = None
    reset_current_selection()

# Display Functions
def display_name_input():
    st.title("Welcome to Wime Cafe!")
    st.info("Please enter your name to start.")

    name_input = st.text_input("Your Name: ", key="customer_name_input")

    if st.session_state.name_error:
        st.error(st.session_state.name_error)

    if st.button("Start Ordering", type="primary", on_click=process_customer_name, args=(name_input,)):
        st.rerun()

def display_start():
    st.subheader(f"Hello, {st.session_state.customer_name}!")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Order Beverage", on_click=set_category, args=("Beverage",)):
            pass
    with col2:
        if st.button("Order Food", on_click=set_category, args=("Food",)):
            pass
    
    if st.session_state.order:
        if st.button("Proceed to Checkout", type="primary", on_click=set_step, args=("checkout",)):
            pass

def display_item_selection():
    category = st.session_state.current_category
    st.subheader(f"What {category} would you like?")

    item_names = list(menu_list[category].keys())

    selected_item = st.radio("Choose an item: ", item_names, index=0, key="item_select")

    if st.button("Confirm Selection", type="primary", on_click=handle_item_selection, args=(selected_item, category)):
        pass

    if st.button("Back to Main Menu", on_click=set_step, args=("start",)):
        reset_current_selection()

def display_quantity_selection():
    item = st.session_state.current_item
    price = st.session_state.current_price

    st.subheader(f"You selected {item}. How many would you like?")
    quantity = st.number_input("Quantity: ", min_value=1, max_value=100, value=1, step=1, key="quantity_input")

    subtotal = price * quantity
    st.metric("Item Subtotal", f"¥{subtotal}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Add Order", type="primary", on_click=handle_add_order, args=(item, price, quantity)):
            st.success(f"{quantity}x {item} added to your order!")
            st.balloons()
            st.rerun()
    with col2:
        if st.button("Change Selection", on_click=set_step, args=("select_item",)):
            pass
    
    if st.button("Back to Main Menu", key="back_from_quantity", on_click=set_step, args=("start",)):
        reset_current_selection()

def display_checkout():
    st.title("Order Summary")

    if not st.session_state.order:
        st.error("Please add some items first.")
        if st.button("Return to Ordering", on_click=set_step, args=("start",)):
            pass
        return
    
    order_data = [
        {"Item": item['item'], "Price": f"¥{item['price']}", "Quantity": item['quantity'], "Total": f"¥{item['total']}"}
        for item in st.session_state.order
    ]
    st.table(order_data)

    grand_total = calculate_total(st.session_state.order)
    st.metric("Grand Total", f"¥{grand_total}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Confirm Order", type="primary", on_click=handle_confirm_order):
            st.rerun()
    
    with col2:
        if st.button("Add More Items", on_click=set_step, args=("start",)):
            pass
    
    if st.button("Clear Cart", help="Removes all items from your cart", on_click=handle_clear_cart):
        st.success("Your cart has been cleared.")
        st.rerun()

def display_thanks():
    st.title(f"Thank You, {st.session_state.customer_name}!")
    st.balloons()

    st.success("Your order will be ready in a minute.")

    if st.button("Start a New Order", on_click=reset_app_state):
        pass

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    load_css("style.css")

    st.sidebar.title("Current Order")
    if st.session_state.order:
        st.sidebar.dataframe([
            {"Item": item['item'], "Quantity": item['quantity'], "Total": f"¥{item['total']}"}
            for item in st.session_state.order
        ], hide_index=True)
        st.sidebar.metric("Order Total", f"¥{calculate_total(st.session_state.order)}")
    else:
        st.sidebar.info("Your cart is empty.")

    if st.session_state.step == "welcome":
        display_name_input()
    elif st.session_state.step == "start":
        display_start()
    elif st.session_state.step == "select_item":
        display_item_selection()
    elif st.session_state.step == "select_quantity":
        display_quantity_selection()
    elif st.session_state.step == "checkout":
        display_checkout()
    elif st.session_state.step == "thanks":
        display_thanks()

if __name__ == '__main__':
    main()
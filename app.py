from flask import Flask, render_template, request
import os
import pandas as pd

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filename)
            
            try:
                # ✅ Validate Sheets
                xls = pd.ExcelFile(filename)
                sheet_names = xls.sheet_names
                print("Sheets found:", sheet_names)

                required_sheets = ['Transactions', 'Customers', 'Products']

                if all(sheet in sheet_names for sheet in required_sheets):
                    # ✅ Load Sheets
                    transactions_df = pd.read_excel(filename, sheet_name='Transactions')
                    customers_df = pd.read_excel(filename, sheet_name='Customers', header=0)
                    products_df = pd.read_excel(filename, sheet_name='Products')

                    print("Transactions Data:")
                    print(transactions_df.head())

                    print("\nCustomers Data (Before Splitting):")
                    print(customers_df.head())

                    print("\nProducts Data:")
                    print(products_df.head())

                    # ✅ Split Customers Sheet
                    first_col_name = customers_df.columns[0]
                    customers_df = customers_df[first_col_name].str.split('-', expand=True)
                    customers_df.columns = ['customer_id', 'name', 'email', 'dob', 'address', 'created_date']

                    print("\nCustomers Data (After Splitting):")
                    print(customers_df.head())

                    # ✅ Detect Address Changes
                    def track_address_changes(customers_df):
                        history = {}
                        for customer_id, group in customers_df.groupby('customer_id'):
                            address_history = group['address'].unique().tolist()
                            history[customer_id] = address_history
                        return history

                    address_change_history = track_address_changes(customers_df)

                    print("\nAddress Change History (per customer):")
                    for customer_id, addresses in address_change_history.items():
                        print(f"Customer {customer_id}: {addresses}")

                    # ✅ Total Transaction Amount Per Product Category
                    transactions_merged = transactions_df.merge(products_df, on='product_id')
                    category_spending = transactions_merged.groupby(['customer_id', 'category'])['amount'].sum().reset_index()

                    print("\nTotal Transaction Amount Per Customer Per Product Category:")
                    print(category_spending)
                    
                    # ✅ Identify Top Spender in Each Category
                    top_spenders = category_spending.loc[category_spending.groupby('category')['amount'].idxmax()]

                    print("\nTop Spender in Each Product Category:")
                    print(top_spenders)
                    
                      # ✅ Rank All Customers Based on Total Spending
                    total_spending_per_customer = transactions_df.groupby('customer_id')['amount'].sum().reset_index()

                        # Add rank column (highest spender gets rank 1)
                    total_spending_per_customer['rank'] = total_spending_per_customer['amount'].rank(method='dense', ascending=False).astype(int)

                        # Sort by rank
                    total_spending_per_customer = total_spending_per_customer.sort_values('rank')

                    print("\nRanking of Customers Based on Total Spending:")
                    print(total_spending_per_customer)



                    return '✅ File processed successfully! Check terminal for address history and spending report.'

                else:
                    return '❌ Error: File must contain sheets: Transactions, Customers, Products'

            except Exception as e:
                return f'❌ Error reading Excel file: {e}'
    
    return render_template('upload.html')


if __name__ == '__main__':
    app.run(debug=True)

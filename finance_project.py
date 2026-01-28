from datetime import datetime
from collections import defaultdict
import csv
import json
import hashlib

def make_transaction_id(date, description, amount, source, row):
    raw = f"{date.isoformat()}|{description.strip().lower()}|{amount:.2f}|{source}|{row}"
    return hashlib.sha256(raw.encode()).hexdigest()

def load_json(filename = "transactions_data.json"):
    #load in the transactions data into the program
    
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
        for t in data:
            t["date"] = datetime.fromisoformat(t["date"])
        return data
    
    except FileNotFoundError:
        print("File not found or couldn't be loaded. Starting fresh")
        return []
    
    except json.JSONDecodeError:
        print("File is corrupted or empty, starting fresh")
        return []

def ask_yes_no(prompt):  
    #helper function to prompt the user for yes no questions
    while True:
        answer = input(prompt).lower()
        if answer in ("yes", "no"):
            return answer
        print("Please enter yes or no")
        
def read_csv(file_name, existing_ids):
    #import data from the user provided file 
    items = []
    
    try:
        with open(file_name, "r", newline="") as read_file:
            data = csv.DictReader(read_file)

            for line_index, line in enumerate(data):
                try:
                    date = datetime.strptime(line["Transaction Date"], "%Y-%m-%d")
                    description = line["Description"]
                    category = line["Category"]
                    amount = round(float(line["Amount"]),2)
                    tx_id = make_transaction_id(date,description,category,amount,file_name,line_index)

                    if tx_id in existing_ids:
                        continue 

                    item = {
                        "id" : tx_id,
                        "date" : date,
                        "description" : description.strip(),
                        "category" : category.lower().strip(),
                        "amount" : amount
                    }
                    items.append(item)
                    existing_ids.add(tx_id)

                except (ValueError, KeyError) as e:
                    continue

    except FileNotFoundError:
        print("Error: File not found.")
    except PermissionError:
        print("Permission denied! Change file permission and try again.")
    except Exception as e:
        print("There was an error loading the file.")
    return items
        
def get_csv_files(expenses, existing_ids):
    #get all the files to be imported
    
    while True:
        file_name = input("enter the file name (please ensure it is a .csv file): ")
        expenses.extend(read_csv(file_name, existing_ids))

        if ask_yes_no("Do you want to import another csv file?: ") == "no":
            break

def get_manual_inputs(expenses, existing_ids):
    
    transactions = []
    
    print('----Lets gather information about your transation----\n')

    while True:
        transaction = {}
        
        while True:
            info = input("What's the date of the transaction? (enter in the form '00-00-0000' month-day-year): ")
            try:
                transaction["date"] = datetime.strptime(info, "%m-%d-%Y")
                break
            except ValueError:
                print("Invalid date format. Make sure you enter MM-DD-YYYY.")

        transaction['description'] = input("Who is the merchant? include details like the store ID: ")
    
        CATEGORIES = ["dining", "grocery", "transportation", "utilities" , "entertainment", "merchendise", "other"]
        category = ''
        while category not in CATEGORIES:
            category = input(f"Please choose a catagory that best fits the transaction from this list \n{CATEGORIES}: ")
        transaction['category'] = category

        while True:
            cost = input("Enter the transaction amount (e.g., 3.50): ")
            try:
                transaction['amount'] = round(float(cost), 2)
                break  # exit loop if input is valid
            except ValueError:
                print("Invalid input! Please enter a number like 3.50")

        print(f"\nHere is the information you provided ->  \n{transaction}")
        if ask_yes_no(f"Does everythting look correct? (Enter yes to save the transaction): ") == 'yes':
            tx_id = make_transaction_id(
                date=transaction["date"],
                description=transaction["description"],
                amount=transaction["amount"],
                source="manual",
                row=len(expenses) + len(transactions)
            )
            transaction["id"] = tx_id
            transactions.append(transaction)
            existing_ids.add(tx_id)

        else:
            print("Transaction discarded!")

        if(ask_yes_no("Would you like to add another transaction?: ")) == "no":
            break

    return transactions 

def serialize_transactions(data):
    serialized = []
    for t in data:
        serialized.append({
            **t,
            "date": t["date"].isoformat()
        })
    return serialized

def write_json(data, filename = "transactions_data.json"):

    with open(filename, 'w') as write_file:
        json.dump(data, write_file, indent = 4)

def view_transactions(expenses):
    if not expenses:
        print("No transactions to display.")
        return

    grouped = defaultdict(list)

    # Group by (year, month)
    for t in expenses:
        key = (t["date"].year, t["date"].month)
        grouped[key].append(t)

    for (year, month) in sorted(grouped):
        month_name = datetime(year, month, 1).strftime("%B %Y")

        print(f"\n{'-' * 24}{month_name}{'-' * 25}")

        # Sort by amount (highest → lowest)
        month_transactions = sorted(
            grouped[(year, month)],
            key=lambda t: t["amount"],
            reverse=True
        )

        month_total = 0.0

        for t in month_transactions:
            print(
                f"{t['description']:<35} "
                f"{t['category']:<15}"
                f"{t['amount']:>10.2f}"
            )
            month_total += t["amount"]

        print("-" * (25))
        print(f"month total:{month_total:>13.2f}")
    
def main():
    """This is an expense tracking app that I'm going to continue to develop overtime in order to use it 
        to help me budget and limit my spending"""
    
    #inialize the transactions list, load previous transactions data into the program
    expenses = load_json()
 
       
    #make a set of the existing keys
    existing_ids = {t["id"] for t in expenses}

    #load new csv transactions data from the user
    if ask_yes_no("do you want to import a csv file? ") == 'yes':
        get_csv_files(expenses,existing_ids)
   
    #prompt the user for manual transaction inputs 
    if ask_yes_no("do you want to manually enter a transaction?: ") == 'yes':
        expenses.extend(get_manual_inputs(expenses, existing_ids))

    #export transactions data to json file
    write_json(serialize_transactions(expenses))

    if ask_yes_no("Would you like to view transactions? ") == "yes":
        view_transactions(expenses)

if __name__ == "__main__":
    main()

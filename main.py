import requests
from bs4 import BeautifulSoup
from lxml import etree as et
import re
import mysql.connector as sqltor
from datetime import datetime as dt
from tkinter import *
from tkinter import messagebox
import tkinter.ttk as ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)


def onClickURL():
    '''
    Function to implement adding or removing URLs from the URL watchlists.
    '''

    w1 = Tk()
    w1.title('Edit URLs')
    w1.geometry('620x200')

    def onClickAdd():
        def AddURL():
            URL = entrybox1.get()
            entrybox1.setvar("Enter URL")
            if "amazon" in URL:
                uid = gen_UID("Amazon")
            elif "flipkart" in URL:
                uid = gen_UID("Flipkart")
            else:
                messagebox.showwarning("Warning", "Not an Amazon or Flipkart URL! Try again.")
                return
            try:
                curs.execute("INSERT INTO URLS (UID, URL) VALUES (%s, %s);", (uid, URL))
            except:
                messagebox.showwarning("Warning", "URL entered is too long for the database. Use another one and try again!")
                w2.destroy()
            mydb.commit()
            curs.execute("SELECT URL FROM URLS WHERE URL = %s;", (URL,))
            if URL in curs.fetchall()[0][0]:
                messagebox.showinfo("Success", "URL added to database successfully!")
            else:
                messagebox.showwarning("Warning", "Something went wrong! Try again later.")
            w2.destroy()

        w2 = Tk()
        w2.title("Add URLs")
        w2.geometry("600x150")
        entrybox1 = Entry(w2)
        entrybox1.place(relx = 0.015, rely = 0.2, width = 580)
        submit_btn = Button(w2, text = "Submit", font = ("Arial 14"), relief = RIDGE, bd = 3, command = AddURL)
        submit_btn.place(relx = 0.42, rely = 0.6)
        w2.mainloop() 

    def onClickDel():
        def DelURL():
            URL = entrybox2.get()
            entrybox2.setvar("Enter URL")
            curs.execute("SELECT URL FROM URLS WHERE URL = %s;", (URL,))
            urls = list(map(lambda x: x[0], curs.fetchall()))
            if URL in urls:
                curs.execute("DELETE FROM URLS WHERE URL = %s;", (URL,))
                mydb.commit()
                curs.execute("SELECT URL FROM URLS WHERE URL = %s;", (URL,))
                if not(curs.fetchall()):
                    messagebox.showinfo("Success", "URL removed from database successfully!")
                else:
                    messagebox.showwarning("Warning", "URL could not be removed. Please try again later.")
            else:
                messagebox.showwarning("Warning", "This URL doesn't exist in the table.")
            w2.destroy()

        w2 = Tk()
        w2.title("Delete URLs")
        w2.geometry("600x200")
        entrybox2 = Entry(w2)
        entrybox2.place(relx = 0.015, rely = 0.2, width = 580)
        submit_btn = Button(w2, text = "Submit", font = ("Arial 14"), relief = RIDGE, bd = 3, command = DelURL)
        submit_btn.place(relx = 0.42, rely = 0.6)
        w2.mainloop()

    bt1 = Button(w1, text="Add URLs", font = ("Arial 12"), relief = RIDGE, bd = 3, command=onClickAdd)
    bt1.place(relx = 0.2, rely = 0.4)
    bt2 = Button(w1, text='Delete URLs', font = ("Arial 12"), relief = RIDGE, bd = 3, command=onClickDel)
    bt2.place(relx = 0.65, rely = 0.4)
    w1.mainloop()


def onClickVary():
    '''
    Function to show the Price variations of each product as a table.
    '''

    w2 = Tk()
    w2.title('Price Variations')
    w2.geometry("1280x500")

    style = ttk.Style(w2)
    style.theme_use('clam')

    curs.execute("SELECT DISTINCT Name FROM Products;")
    data = curs.fetchall()
    options = list(map(lambda x: x[0], data))
    menu = StringVar(w2)
    menu.set("Select Any Product")
    drop = OptionMenu(w2, menu, *options, command = lambda x: showTable(w2, menu.get()))
    drop.place(relx = 0.4, rely = 0.05)

    w2.mainloop()


def showTable(w2, name):
    '''
    Function to display the MySQL table storing products' names and prices along with the timestamp. 
    '''

    tree = ttk.Treeview(w2, column=("Timestamp", "Product Name", "Price"), show='headings', height=15)
    tree.column("#1", anchor=CENTER, width = 300)
    tree.heading("#1", text="Timestamp")
    tree.column("#2", anchor=CENTER, width = 500)
    tree.heading("#2", text="Product Name")
    tree.column("#3", anchor=CENTER, width = 400)
    tree.heading("#3", text="Price")
    curs.execute("SELECT Timestamp, Name, Price FROM Products WHERE Name = %s ORDER BY Timestamp;", (name,))
    data = curs.fetchall()
    for i in data:
        tree.insert('', 'end', text = "1", values = i)
    tree.place(relx = 0.03, rely = 0.2)


def gen_UID(website):
    '''
    Function to generate unique identification codes for all URLs being added to the table.
    '''

    curs.execute("SELECT DISTINCT UID FROM URLS WHERE UID REGEXP %s ORDER BY UID DESC LIMIT 1;", (website[0] + '%',))
    l_uid = curs.fetchall()
    if not(l_uid):
        uid = 'P1'+website[0]
    else:
        num = ""
        for i in l_uid[0][0]:
            if i.isdigit():
                num += i
        uid = 'P' + str(int(num)+1) + website[0]
    return uid


def get_amazon_name(dom):
    '''
    To get product names from Amazon URLs by inspecting the HTML.
    '''

    try:
        name = dom.xpath('//span[@id="productTitle"]/text()')
        [name.strip() for name in name]
        return name[0]
    except Exception:
        return None


def get_amazon_price(dom):
    '''
    To get product prices from Amazon URLs by inspecting the HTML.
    '''

    try:
        price = dom.xpath('//span[@class="a-price-whole"]/text()')[0]
        price = price.replace(',', '').replace('₹', '').replace('.00', '')
        return int(price)
    except Exception:
        return None


def get_flipkart_details(product_url):
    '''
    To get product names and prices from Flipkart URLs by inspecting the HTML.
    '''

    response = requests.get(product_url, headers=header)
    soup = BeautifulSoup(response.content, 'html.parser')

    product_name = soup.find("span",{"class":"B_NuCI"}).get_text()
    price = soup.find("div",{"class":"_30jeq3 _16Jk6d"}).get_text()
    timestamp = dt.now().strftime("%Y-%m-%d %H:%M:%S")
    price_int = int(''.join(re.findall(r'\d+', price)))
    print(product_name + " is at " + price)
    curs.execute("SELECT UID FROM URLS WHERE URL = %s", (product_url,))
    uid = curs.fetchall()[0][0]
    curs.execute("INSERT INTO Products (Timestamp, UID, Name, Price) VALUES (%s, %s, %s, %s);", (timestamp, uid, product_name, price_int))
    mydb.commit()


def mysqllogin():
    f = open("mysql_auth.txt", "a+")
    f.seek(0)
    data = f.read()
    if not(data):
        sqllogin = Tk()
        sqllogin.title("MySQL Login")
        sqllogin.geometry("400x300")
        username = StringVar()
        username.set("Enter MySQL username")
        pwd = StringVar()
        pwd.set("Enter MySQL password")
        userentry = Entry(sqllogin, textvariable = username)
        userentry.place(relx = 0.35, rely = 0.2)
        passentry = Entry(sqllogin, textvariable = pwd)
        passentry.place(relx = 0.35, rely = 0.5)
        submit_btn = Button(sqllogin, text = "Submit", font = ("Arial 14"), relief = RIDGE, bd = 3, command = lambda: f.writelines([userentry.get()+"\n", passentry.get()]) or sqllogin.destroy())
        submit_btn.place(relx = 0.42, rely = 0.8)
        sqllogin.mainloop()
    f.seek(0)
    details = f.readlines()
    f.close()
    return details


def GUI():
    '''
    Function to start the GUI of the program. It contains the menu options
    for the user to interact with.
    '''

    root = Tk()
    root.title("Price Tracker")
    root.geometry("1000x600")

    menu = StringVar(root)
    menu.set("Select Any Product")
    options = ["Amazon", "Flipkart"]

    drop = OptionMenu(root, menu, *options, command=lambda x: graph(menu.get(), fig, canvas))
    drop.place(relx = 0.4, rely = 0.05)

    def refresh_data():
        w = Tk()
        w.title("Refreshing Data")
        w.geometry("400x200")
        def save():
            URL = entrybox.get()
            if "amazon" in URL:
                dom = et.fromstring(requests.get(URL, headers=header).content)
                name = get_amazon_name(dom)
                price = get_amazon_price(dom)
                if name and price:
                    curs.execute("SELECT UID FROM URLS WHERE URL = %s;", (URL,))
                    uid = curs.fetchall()[0][0]
                    timestamp = dt.now().strftime("%Y-%m-%d %H:%M:%S")
                    curs.execute("INSERT INTO Products (Timestamp, UID, Name, Price) VALUES (%s, %s, %s, %s);", (timestamp, uid, name, price))
                    mydb.commit()
                else:
                    messagebox.showwarning("Warning", "Could not fetch details. Please check the URL.")
            elif "flipkart" in URL:
                get_flipkart_details(URL)
            else:
                messagebox.showwarning("Warning", "Not an Amazon or Flipkart URL!")
            w.destroy()
        
        entrybox = Entry(w)
        entrybox.place(relx = 0.1, rely = 0.2, width = 280)
        submit_btn = Button(w, text = "Submit", font = ("Arial 14"), relief = RIDGE, bd = 3, command = save)
        submit_btn.place(relx = 0.35, rely = 0.5)
        w.mainloop()

    refresh_btn = Button(root, text="Refresh Data", font = ("Arial 12"), relief = RIDGE, bd = 3, command=refresh_data)
    refresh_btn.place(relx = 0.05, rely = 0.15)
    view_btn = Button(root, text="View Data", font = ("Arial 12"), relief = RIDGE, bd = 3, command=onClickVary)
    view_btn.place(relx = 0.25, rely = 0.15)
    edit_btn = Button(root, text="Edit URLs", font = ("Arial 12"), relief = RIDGE, bd = 3, command=onClickURL)
    edit_btn.place(relx = 0.45, rely = 0.15)

    fig = Figure(figsize=(7, 4), dpi=100)
    ax = fig.add_subplot(111)
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().place(relx=0.05, rely=0.25, width=900, height=300)

    def graph(website, fig, canvas):
        ax.clear()
        if website == "Amazon":
            curs.execute("SELECT Name, Price FROM Products WHERE UID LIKE %s ORDER BY Timestamp DESC;", ("P1Amazon%",))
        elif website == "Flipkart":
            curs.execute("SELECT Name, Price FROM Products WHERE UID LIKE %s ORDER BY Timestamp DESC;", ("P1Flipkart%",))
        else:
            return
        data = curs.fetchall()
        if data:
            x = [i[0] for i in data]
            y = [i[1] for i in data]
            ax.plot(x, y, marker='o')
            ax.set_xlabel('Product Name')
            ax.set_ylabel('Price')
            ax.set_title(f'Price Trends for {website}')
            canvas.draw()
        else:
            messagebox.showwarning("Warning", "No data available for the selected product.")

    root.mainloop()


if __name__ == "__main__":
    # MySQL Connection
    mydb = sqltor.connect(
        host="localhost",
        user=mysqllogin()[0].strip(),
        password=mysqllogin()[1].strip(),
        database="price_tracker"
    )
    curs = mydb.cursor()
    header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36"}
    GUI()
    
    # Close the database connection
    mydb.close()

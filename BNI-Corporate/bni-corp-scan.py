# imports
import cv2
import pandas as pd
import fitz
import pytesseract
import time

def raw_values(img_name):
    # define tesseract OCT model 
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    # read png
    page = cv2.imread(img_name)

    # to grayscale for model to easily process
    page = cv2.cvtColor(page, cv2.COLOR_BGR2GRAY)

    # get page height
    page_height = page.shape[0]

    # crop page
    page = page[int(page_height * 0.332):, :]

    # define threshold
    retval, thresh = cv2.threshold(page, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

    # dilation parameter; bigger tuple = smaller rectangle
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 20))

    # apply dilation to the thresholded monochrome image
    dilation = cv2.dilate(thresh, rect_kernel, iterations=1)

    # find contours and rectangles
    contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # copy grayscale image from earlier to see the contours
    page_copy = page.copy()

    # make contour list to store text and its corresponding coordinates
    cnt_list = []

    # loop for each contour detected
    for cnt in contours:

        # get coordinates of contours
        x, y, w, h = cv2.boundingRect(cnt)

        # crop text block by rectangle text block
        crop = page_copy[y:y+h, x:x+w]

        # use ocr model cropped image
        text = pytesseract.image_to_string(crop, config="--psm 13")

        # store coordinates and text
        cnt_list.append([x, y, text])

    return cnt_list, page
    
def sorting(list, page, page_num):
    sorted_list = sorted(list, key = lambda x: x[0]) # sort by width first
    sorted_list = sorted(sorted_list, key = lambda x: x[1]) # then height
    
    # create dataframe
    df = pd.DataFrame(sorted_list)
    df.columns = ["x", "y", "Text"]

    # omit trivial texts
    df = df.drop(df[(df.Text == "")].index)

    # Remove the \n in text
    df["Text"] = df["Text"].str.replace("\n", "")
    df = df.drop(df[(df.Text == "|") | (df.Text == "| |")].index)



    r = df[df["x"] == df["x"].min()]["y"].iloc[0]

    for i in range(df.shape[0]):
        y = df["y"].iloc[i]

        if r-5 <= y <= r+5:
            df["y"].iloc[i] = r
        else:
            r = y

    # sort again left to right, top to bottom
    df = df.sort_values(by=["y", "x"])

    for i in range(df.shape[0]):
        y = df["y"].iloc[i]
        next_y = y

        for j in range(df.shape[0]-i):
            new_y = df["y"].iloc[i+j]
            if new_y != next_y:
                next_y = new_y
                break
        
        if next_y-y < 35:
            df["y"].iloc[i] = next_y

    # sort again left to right, top to bottom
    df = df.sort_values(by=["y", "x"])



    pdate = ""; edate = ""; branch = ""; journal = ""; tdesc = ""; amount = ""; dbcr = ""; bal = ""
    pdates = []; edates = []; branchs = []; journals = []; tdescs = []; amounts = []; dbcrs = []; bals = []

    # prevents summary at the end of pdf to be added
    # exit = 0 # if SALDO and AWAL is detected in columns keterangan1 and keterangan2 correspondingly, append arrays and break

    df = df._append({"x": 500, "y": 0, "Text": "a"}, ignore_index=True)

    for i in range(df.shape[0]):
        x = df["x"].iloc[i]
        text = df["Text"].iloc[i]
        
        if x < 1000:
            if "Ledger" in edate:
                pdate = ""; edate = ""; branch = ""; journal = ""; tdesc = ""; amount = ""; dbcr = ""; bal = ""
            elif not (220 < x):
                pdates.append(pdate)
                edates.append(edate)
                branchs.append(branch)
                journals.append(journal)
                tdescs.append(tdesc)
                amounts.append(amount)
                dbcrs.append(dbcr)
                bals.append(bal)

                pdate = ""; edate = ""; branch = ""; journal = ""; tdesc = ""; amount = ""; dbcr = ""; bal = ""

            pdate += text

        elif 1000 < x < 1950:
            if text == "Ending": # last page
                pdates.append(pdate)
                edates.append(edate)
                branchs.append(branch)
                journals.append(journal)
                tdescs.append(tdesc)
                amounts.append(amount)
                dbcrs.append(dbcr)
                bals.append(bal)

                break
            else:
                edate += text
        elif 1950 < x < 2450:
            branch += text + " "
        elif 2450 < x < 2790:
            journal += text
        elif 2790 < x < 4170:
            tdesc += text + " "
        elif 4170 < x < 4850:
            amount += text
        elif 4850 < x < 5100:
            dbcr += text
        elif 5100 < x:
            bal += text


    t = pd.DataFrame({
                "Posting Date": pdates,
                "Effective Date": edates,
                "Branch": branchs,
                "Journal": journals,
                "Transaction Description": tdescs,
                "Amount": amounts,
                "DB/CR": dbcrs,
                "Balance": bals
            })

    t = t[(t["Posting Date"] == "a") == False] # delete
    t = t[(t["Posting Date"] == "") == False]



    # remove every element's last character (which is some unnecessary space)
    for col in t.columns:
        if col == "Branch" or col == "Transaction Description":
            t[col] = t[col].str[:-1]
    
    # erase any non-numeric character at the end of dates
    for i in range(t.shape[0]):
        p = t["Posting Date"].iloc[i]
        e = t["Effective Date"].iloc[i]

        while not p[-1:].isnumeric():
            p = p[:-1]
        t["Posting Date"].iloc[i] = p

        while not e[-1:].isnumeric():
            e = e[:-1]
        t["Effective Date"].iloc[i] = e

    # for posting and effective date, split and add space after date
    t["Posting Date"] = t["Posting Date"].str[:-8] + " " + t["Posting Date"].str[-8:]
    t["Effective Date"] = t["Effective Date"].str[:-8] + " " + t["Effective Date"].str[-8:]

    # emphasize perak in amount
    for i in range(t.shape[0]):
        a = t["Amount"].iloc[i]

        if a[-3:-2] != ".":
            a = a[:-2] + "." + a[-2:]

    final = t.copy()

    return final


# global variables

names = []
dfs = []
all = pd.DataFrame(columns=["Posting Date", "Effective Date", "Branch", "Journal", "Transaction Description", "Amount", "DB/CR", "Balance"])

start_time = time.time()


# process starts here

pdf_name = "BNI_CORPORATE.pdf"

doc = fitz.open(pdf_name)

for page in doc:
    pix = page.get_pixmap(dpi=600)
    name = pdf_name[:-4] + "-page-" + str(page.number) + ".png"
    names.append(name)
    pix.save(name)


for name in names:
    print("\nProcessing " + name)

    cnt_list, page = raw_values(name)

    page_num = name[-5:-4]

    trans = sorting(cnt_list, page, page_num)

    dfs.append(trans)

for df in dfs:
    all = all._append(df, sort=False)

df = df.reset_index(drop = True)

all.to_csv("transactions.csv", index=False, sep=";")

end_time = time.time()
total_time = end_time-start_time
print("\nElapsed time: " + str(total_time) + "s")
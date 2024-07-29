# known issue: really stupid fucking bug where height categorizations does not work for a fucking reason 
# even though i copied the exact fucking code from ipynb what the fuck holy shit i hate this

# imports
import cv2
import pandas as pd
import fitz
import pytesseract
import time

def raw_values(img_name, page_num):
    # define tesseract OCT model 
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    # read png
    page = cv2.imread(img_name)

    # to grayscale for model to easily process
    page = cv2.cvtColor(page, cv2.COLOR_BGR2GRAY)

    # get page height
    page_height = page.shape[0]

    # crop to only table
    page = page[int(page_height * 0.343):, :]

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
        
        if next_y-y < 20:
            df["y"].iloc[i] = next_y

    # sort again left to right, top to bottom
    df = df.sort_values(by=["y", "x"])

    df.to_csv("dc.csv", index=False, sep=";")


    date="";vdate="";desc="";ref="";debit="";kredit="";saldo=""
    dates=[];vdates=[];descs=[];refs=[];debits=[];kredits=[];saldos=[]

    # prevents summary at the end of pdf to be added
    # exit = 0 # if SALDO and AWAL is detected in columns keterangan1 and keterangan2 correspondingly, append arrays and break

    df = df._append({"x": 500, "y": 0, "Text": "a"}, ignore_index=True)

    for i in range(df.shape[0]):
        x = df["x"].iloc[i]
        text = df["Text"].iloc[i]
        
        if x < 1000:
            if vdate != "" or not 300 < x:
                dates.append(date)
                vdates.append(vdate)
                descs.append(desc)
                refs.append(ref)
                debits.append(debit)
                kredits.append(kredit)
                saldos.append(saldo)

                date="";vdate="";desc="";ref="";debit="";kredit="";saldo=""
                
            if text.strip() == "Total":
                dates.append(date)
                vdates.append(vdate)
                descs.append(desc)
                refs.append(ref)
                debits.append(debit)
                kredits.append(kredit)
                saldos.append(saldo)

                break
            
            date += text
        elif 1000 < x < 1600:
            vdate += text
        elif 1600 < x < 2950:
            desc += text + " "
        elif 2950 < x < 3800:
            ref += text + " "
        elif 3800 < x < 4400:
            debit += text
        elif 4400 < x < 4950:
            kredit += text
        elif 4950 < x:
            saldo += text

    t = pd.DataFrame({
                "Date & Time": dates,
                "Value Date": vdates,
                "Description": descs,
                "Reference No.": refs,
                "Debit": debits,
                "Credit": kredits, 
                "Saldo": saldos
            })

    t = t[t["Date & Time"].str.contains("a") == False] # delete
    t = t[(t["Date & Time"] == "") == False]


    # remove every element's last character (which is some unnecessary space)
    t["Description"] = t["Description"].str[:-1]
    t["Reference No."] = t["Reference No."].str[:-1]

    # for posting and effective date, split and add space after date
    t["Date & Time"] = t["Date & Time"].str[:-8] + " " + t["Date & Time"].str[-8:]

    # emphasize perak in amount
    for i in range(t.shape[0]):
        d = t["Debit"].iloc[i]
        k = t["Credit"].iloc[i]
        s = t["Saldo"].iloc[i]

        if d[-3:-2] != ".":
            t["Debit"].iloc[i] = d[:-2] + "." + d[-2:]

        if k[-3:-2] != ".":
            t["Credit"].iloc[i] = k[:-2] + "." + k[-2:]

        if s[-3:-2] != ".":
            t["Saldo"].iloc[i] = s[:-2] + "." + s[-2:]
    
    # final = t.drop(["CBG", "Saldo"], axis=1)
    final = t.copy()

    return final


# global variables

names = ["MANDIRI_PERSONAL_4-page-1.png"]
dfs = []
all = pd.DataFrame(columns=["Date & Time", "Value Date", "Description", "Reference No.", "Debit", "Credit", "Saldo"])

start_time = time.time()


# process starts here

# pdf_name = "MANDIRI_PERSONAL_4.pdf"

# doc = fitz.open(pdf_name)

# for page in doc:
#     pix = page.get_pixmap(dpi=600)
#     name = pdf_name[:-4] + "-page-" + str(page.number) + ".png"
#     names.append(name)
#     pix.save(name)


for name in names:
    print("\nProcessing " + name)

    page_num = name[-5:-4]

    cnt_list, page = raw_values(name, page_num)

    trans = sorting(cnt_list, page, page_num)

    dfs.append(trans)

for df in dfs:
    all = all._append(df, sort=False)

df = df.reset_index(drop = True)

all.to_csv("transactions.csv", index=False, sep=";")

end_time = time.time()
total_time = end_time-start_time
print("\nElapsed time: " + str(total_time) + "s")
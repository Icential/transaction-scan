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

    # start of table is different per page
    if page_num == "0":
        page = page[int(page_height * 0.395):, :]
    else:
        page = page[int(page_height * 0.138):, :]

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



    r = 0

    # create dataframe
    df = pd.DataFrame(sorted_list)
    df.columns = ["x", "y", "Text"]

    # omit trivial texts
    df = df.drop(df[(df.Text == "")].index)

    # Remove the \n in text
    df["Text"] = df["Text"].str.replace("\n", "")
    df = df.drop(df[(df.Text == "|") | (df.Text == "| |")].index)



    for i in range(df.shape[0]):
        if i == 0:
            r = df["y"].iloc[0]

        y = df["y"].iloc[i]

        if y <= r+5:
            df["y"].iloc[i] = r
        else:
            r = y

    # sort again left to right, top to bottom
    df = df.sort_values(by=["y", "x"])



    t = pd.DataFrame(columns=["Tanggal Transaksi", "Uraian Transaksi", "Teller", "Debet", "Kredit", "Saldo"])

    tantran="";uratra="";teller="";debet="";kredit="";saldo=""
    tantrans=[];uratras=[];tellers=[];debets=[];kredits=[];saldos=[]

    # prevents summary at the end of pdf to be added
    # exit = 0 # if SALDO and AWAL is detected in columns keterangan1 and keterangan2 correspondingly, append arrays and break

    df = df._append({"x": 500, "y": 0, "Text": "a"}, ignore_index=True)

    for i in range(df.shape[0]):
        x = df["x"].iloc[i]
        text = df["Text"].iloc[i]
        
        if x < 870:
            if uratra != "" or not 350 < x:
                tantrans.append(tantran)
                uratras.append(uratra)
                tellers.append(teller)
                debets.append(debet)
                kredits.append(kredit)
                saldos.append(saldo)

                tantran="";uratra="";teller="";debet="";kredit="";saldo=""
                
            if text.strip() == "Saldo" or text.strip() == "Opening":
                tantrans.append(tantran)
                uratras.append(uratra)
                tellers.append(teller)
                debets.append(debet)
                kredits.append(kredit)
                saldos.append(saldo)

                break
            
            tantran += text
        elif 870 < x < 2500:
            uratra += text + " "
        elif 2500 < x < 2850:
            teller += text
        elif 2850 < x < 3750:
            debet += text
        elif 3750 < x < 4550:
            kredit += text
        elif 4550 < x:
            if "/" in text:
                tantrans.append(tantran)
                uratras.append(uratra)
                tellers.append(teller)
                debets.append(debet)
                kredits.append(kredit)
                saldos.append(saldo)

                break
            else:
                saldo += text

    t = pd.DataFrame({
                "Tanggal Transaksi": tantrans,
                "Uraian Transaksi": uratras,
                "Teller": tellers,
                "Debet": debets,
                "Kredit": kredits,
                "Saldo": saldos
            })

    t = t[t["Tanggal Transaksi"].str.contains("a") == False] # delete
    t = t[(t["Tanggal Transaksi"] == "") == False]



    # remove every element's last character (which is some unnecessary space)
    t["Uraian Transaksi"] = t["Uraian Transaksi"].str[:-1]

    # for posting and effective date, split and add space after date
    t["Tanggal Transaksi"] = t["Tanggal Transaksi"].str[:-8] + " " + t["Tanggal Transaksi"].str[-8:]

    # emphasize perak in amount
    for i in range(t.shape[0]):
        d = t["Debet"].iloc[i]
        k = t["Kredit"].iloc[i]
        s = t["Saldo"].iloc[i]

        if d[-3:-2] != ".":
            d = d[:-2] + "." + d[-2:]

        if k[-3:-2] != ".":
            k = k[:-2] + "." + k[-2:]

        if s[-3:-2] != ".":
            s = s[:-2] + "." + s[-2:]
    
    # final = t.drop(["CBG", "Saldo"], axis=1)
    final = t.copy()

    return final


# global variables

names = []
dfs = []
all = pd.DataFrame(columns=["Tanggal Transaksi", "Uraian Transaksi", "Teller", "Debet", "Kredit", "Saldo"])

start_time = time.time()


# process starts here

pdf_name = "BRI_PERSONAL.pdf"

doc = fitz.open(pdf_name)

for page in doc:
    pix = page.get_pixmap(dpi=600)
    name = pdf_name[:-4] + "-page-" + str(page.number) + ".png"
    names.append(name)
    pix.save(name)


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
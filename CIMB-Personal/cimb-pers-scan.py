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
    page_width = page.shape[1]

    # crop page to just the table
    page = page[int(page_height * 0.433):, int(page_width * 0.038):int(page_width * 0.98)]

    # define threshold
    retval, thresh = cv2.threshold(page, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

    # dilation parameter; bigger tuple = smaller rectangle
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))

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
    df = df.drop(df[(df.Text == "|") | (df.Text == "| |") | (df.x == 0) | (df.y == 0)].index)



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
        
        if next_y-y < 50:
            df["y"].iloc[i] = next_y

    # sort again left to right, top to bottom
    df = df.sort_values(by=["y", "x"])

    # delete saldo awal
    if df["Text"].iloc[0].strip() == "SALDO":
        saldo_y = df["y"].iloc[0]
        df = df.drop(df[df.y == saldo_y].index)


    t = pd.DataFrame(columns=["Tanggal Transaksi", "Uraian Transaksi", "Teller", "Debet", "Kredit", "Saldo"])

    tt="";tv="";uratra="";bg="";debet="";kredit="";saldo=""
    tts=[];tvs=[];uratras=[];bgs=[];debets=[];kredits=[];saldos=[]

    df = df._append({"x": 500, "y": 0, "Text": "a"}, ignore_index=True)

    for i in range(df.shape[0]):
        x = df["x"].iloc[i]
        text = df["Text"].iloc[i]
        
        if x < 350:
            if tv != "":
                tts.append(tt)
                tvs.append(tv)
                uratras.append(uratra)
                bgs.append(bg)
                debets.append(debet)
                kredits.append(kredit)
                saldos.append(saldo)

                tt="";tv="";uratra="";bg="";debet="";kredit="";saldo=""
                
            if text.strip() == "Terima" or text.strip() == "Total" or "Dis" in text.strip():
                tts.append(tt)
                tvs.append(tv)
                uratras.append(uratra)
                bgs.append(bg)
                debets.append(debet)
                kredits.append(kredit)
                saldos.append(saldo)

                break
            
            tt += text
        elif 350 < x < 870:
            tv += text
        elif 870 < x < 2400:
            uratra += text + " "
        elif 2400 < x < 2950:
            bg += text
        elif 2950 < x < 3600:
            debet += text
        elif 3600 < x < 4250:
            kredit += text
        elif 4250 < x:
            saldo += text

    t = pd.DataFrame({
                "Tgl Txn": tts,
                "Tgl Valuta": tvs,
                "Uraian Transaksi": uratras,
                "No. Cek/BG": bgs,
                "Debet": debets,
                "Kredit": kredits,
                "Saldo": saldos
            })

    t = t[t["Tgl Txn"].str.contains("a") == False] # delete
    t = t[(t["Tgl Txn"] == "") == False]


    # remove every element's last character (which is some unnecessary space)
    t["Uraian Transaksi"] = t["Uraian Transaksi"].str[:-1]

    # emphasize perak in amount
    for i in range(t.shape[0]):
        d = t["Debet"].iloc[i]
        k = t["Kredit"].iloc[i]
        s = t["Saldo"].iloc[i]

        if d[-3:-2] != ".":
            t["Debet"].iloc[i] = d[:-2] + "." + d[-2:]

        if k[-3:-2] != ".":
            t["Kredit"].iloc[i] = k[:-2] + "." + k[-2:]

        if s[-3:-2] != ".":
            t["Saldo"].iloc[i] = s[:-2] + "." + s[-2:]
    
    # final = t.drop(["CBG", "Saldo"], axis=1)
    final = t.copy()

    return final


# global variables

names = []
dfs = []
all = pd.DataFrame(columns=["Tgl Txn", "Tgl Valuta", "Uraian Transaksi", "No. Cek/BG", "Debet", "Kredit", "Saldo"])

start_time = time.time()


# process starts here

pdf_name = "CIMB_PERSONAL.pdf"

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
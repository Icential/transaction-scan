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
    page = page[int(page_height * 0.41):, :]

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



    r = 0

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

    # delete saldo awal
    if df["Text"].iloc[0].strip() == "SALDO":
        saldo_y = df["y"].iloc[0]
        df = df.drop(df[df.y == saldo_y].index)



    t = pd.DataFrame(columns=["Tgl Trx", "Tgl Valuta", "Uraian", "Debit", "Kredit", "Saldo"])

    tt="";tv="";uraian="";debit="";kredit="";saldo=""
    tts=[];tvs=[];uraians=[];debits=[];kredits=[];saldos=[]

    # prevents summary at the end of pdf to be added
    # exit = 0 # if SALDO and AWAL is detected in columns keterangan1 and keterangan2 correspondingly, append arrays and break

    df = df._append({"x": 500, "y": 0, "Text": "a"}, ignore_index=True)

    for i in range(df.shape[0]):
        x = df["x"].iloc[i]
        text = df["Text"].iloc[i]
        
        if x < 550:
            if tv != "":
                tts.append(tt)
                tvs.append(tv)
                uraians.append(uraian)
                debits.append(debit)
                kredits.append(kredit)
                saldos.append(saldo)

                tt="";tv="";uraian="";debit="";kredit="";saldo=""
            
            tt += text
        elif 550 < x < 950:
            tv += text
        elif 950 < x < 2300:
            uraian += text + " "
        elif 2300 < x < 3100:
            debit += text
        elif 3100 < x < 4000:
            if text.strip() == "Halaman":
                tts.append(tt)
                tvs.append(tv)
                uraians.append(uraian)
                debits.append(debit)
                kredits.append(kredit)
                saldos.append(saldo)

                break
            else:
                kredit += text
        elif 4000 < x:
            saldo += text

    t = pd.DataFrame({
                "Tgl Trans": tts,
                "Tgl Valuta": tvs,
                "Uraian": uraians,
                "Debit": debits,
                "Kredit": kredits,
                "Saldo": saldos
            })

    t = t[t["Tgl Trans"].str.contains("a") == False] # delete
    t = t[(t["Tgl Trans"] == "") == False]



    # remove every element's last character (which is some unnecessary space)
    t["Uraian"] = t["Uraian"].str[:-1]

    # emphasize perak in amount
    for i in range(t.shape[0]):
        d = t["Debit"].iloc[i]
        k = t["Kredit"].iloc[i]
        s = t["Saldo"].iloc[i]

        while not d[-1:].isnumeric() and not d.strip() == "":
            d = d[:-1]

        while not k[-1:].isnumeric() and not k.strip() == "":
            k = k[:-1]

        while not s[-1:].isnumeric() and not k.strip() == "":
            s = s[:-1]

        if d[-3:-2] != "." and d[-3:-2] != ",":
            t["Debit"].iloc[i] = d[:-2] + "." + d[-2:]

        if k[-3:-2] != "." and k[-3:-2] != ",":
            t["Kredit"].iloc[i] = k[:-2] + "." + k[-2:]

        if s[-3:-2] != "." and s[-3:-2] != ",":
            t["Saldo"].iloc[i] = s[:-2] + "." + s[-2:]

    
    # final = t.drop(["CBG", "Saldo"], axis=1)
    final = t.copy()

    return final


# global variables

names = []
dfs = []
all = pd.DataFrame(columns=["Tgl Trx", "Tgl Valuta", "Uraian", "Debit", "Kredit", "Saldo"])

start_time = time.time()


# process starts here

pdf_name = "PERMATA_PERSONAL.pdf"

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
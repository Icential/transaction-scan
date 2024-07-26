# imports
import cv2
import pandas as pd
import fitz
import matplotlib.pyplot as plt
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
    page = page[int(page_height * 0.282):, :]

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

    t = pd.DataFrame(columns=["Tanggal", "Keterangan 1", "Keterangan 2", "CBG", "Mutasi", "Saldo"])

    tanggal_text = ""; keterangan1_text = ""; keterangan2_text = ""; cbg_text = ""; mutasi_text = ""; saldo_text = ""
    tanggals = []; keterangan1s = []; keterangan2s = []; cbgs = []; mutasis = []; saldos = []

    # prevents summary at the end of pdf to be added
    exit = 0 # if SALDO and AWAL is detected in columns keterangan1 and keterangan2 correspondingly, append arrays and break

    df = df._append({"x": 500, "y": 0, "Text": "a"}, ignore_index=True)

    for i in range(df.shape[0]):
        x = df["x"].iloc[i]
        text = df["Text"].iloc[i]
        
        if 0 < x < 700:
            if keterangan1_text != "":
                tanggals.append(tanggal_text)
                keterangan1s.append(keterangan1_text)
                keterangan2s.append(keterangan2_text)
                cbgs.append(cbg_text)
                mutasis.append(mutasi_text)
                saldos.append(saldo_text)

                tanggal_text = ""; keterangan1_text = ""; keterangan2_text = ""; cbg_text = ""; mutasi_text = ""; saldo_text = ""

            tanggal_text += text + ""
        elif 700 < x < 1550:
            if text == "SALDO" or text == "AWAL":
                if page_num == "0":
                    continue
                else:
                    exit += 1
            else:
                keterangan1_text += text + " "
        elif 1550 < x < 2500:
            if text == "SALDO" or text == "AWAL":
                if page_num == "0":
                    continue
                else:
                    exit += 1
            else:
                keterangan2_text += text + " "
        elif 2500 < x < 2900:
            cbg_text += text + " "
        elif 2900 < x < 4000:
            mutasi_text += text + " "
        elif 4000 < x < page.shape[1]:
            saldo_text += text + " "

        if exit == 2:
            tanggals.append(tanggal_text)
            keterangan1s.append(keterangan1_text)
            keterangan2s.append(keterangan2_text)
            cbgs.append(cbg_text)
            mutasis.append(mutasi_text)
            saldos.append(saldo_text)

            tanggal_text = ""; keterangan1_text = ""; keterangan2_text = ""; cbg_text = ""; mutasi_text = ""; saldo_text = ""

            break

    t = pd.DataFrame({
                "Tanggal": tanggals,
                "Keterangan 1": keterangan1s,
                "Keterangan 2": keterangan2s,
                "CBG": cbgs,
                "Mutasi": mutasis,
                "Saldo": saldos 
            })
    
    t = t[t["Keterangan 1"].str.contains("AWAL") == False] # delete very first row
    t = t[t["Tanggal"].str.contains("a") == False] # delete

    # remove every element's last character (which is some unnecessary space)
    for col in t.columns:
        if col != "Tanggal":
            t[col] = t[col].str[:-1]

    # remove spacing in saldo
    t["Mutasi"] = t["Mutasi"].str.replace(" ", "")

    # remove string in saldo
    for i in range(t.shape[0]):
        m = t["Mutasi"].iloc[i]

        if m != "":
            for c in range(len(m)):
                if m[-1:].isalpha() or m[-1:] == "-" or m[-1:] == ".":
                    m = m[:-1]

            if m[-3:-2] != ".":
                m = m[:-2] + "." + m[-2:]

            t["Mutasi"].iloc[i] = m

    # replace V with / in tanggal
    for i in range(t.shape[0]):
        m = t["Tanggal"].iloc[i]

        t["Tanggal"].iloc[i] = m.replace("V", "/")
    
    final = t.drop(["CBG", "Saldo"], axis=1)

    return final

names = []
dfs = []
all = pd.DataFrame(columns=["Tanggal", "Keterangan 1", "Keterangan 2", "Mutasi"])

start_time = time.time()

pdf_name = "BCA_CORPORATE.pdf"

doc = fitz.open(pdf_name)

for page in doc:
    pix = page.get_pixmap(dpi=600)
    name = pdf_name[:-4] + "-page-" + str(page.number) + ".png"
    names.append(name)
    pix.save(name)


for name in names:
    print("Processing " + name)

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
print("Elapsed time: " + str(total_time))
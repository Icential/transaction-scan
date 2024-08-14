import spacy
from termcolor import colored

nlp = spacy.load('pengetahu')

#doc = nlp("tampilkann data bpkb dari cabang medan")

answer = "y"

while answer == "y":
    print("\n")
    test_text = input("Mau cari apa pak/bu? : ")
    doc = nlp(test_text)

   

    table = []
    column_condition = []
    logic_condition = []
    value_conditon = []

    for ent in doc.ents:
        #print(ent.text, ent.start_char, ent.end_char, ent.label_)
        if ent.label_ == 'TBL':
            table.append(ent.text)
        elif ent.label_ == 'COC':
            column_condition.append(ent.text)
        elif ent.label_ == 'LGC':
            logic_condition.append(ent.text)
        elif ent.label_ == 'VLC':
            value_conditon.append(ent.text)
       

    if len(logic_condition) == 0:
        logic_condition.append("=")
    else:
        if logic_condition[0] == "atas" or logic_condition[0] == "lebih" or logic_condition[0] == "diatas":
            logic_condition[0] = ">"
        elif logic_condition[0] == "bawah" or logic_condition[0] == "kurang" or logic_condition[0] == "dibawah":
            logic_condition[0] = "<"
    

    #if column_condition[0].endswith('nya'):
    # column_condition[0] = column_condition[0][:-3]


    sql = ""
    if len(table) == 0 or len(column_condition) == 0 or len(logic_condition)  == 0 or len(value_conditon) == 0:
       print(colored("Permintaan tidak bisa diproses. Mohon gunakan kalimat lebih lengkap.", "red"))     
    else:
        sql = "SELECT * FROM " + table[0] + " WHERE " + column_condition[0] + " " + logic_condition[0] + " '" + value_conditon[0] + "'"
        print(colored(sql, "green"))
    

    answer = input("Cari lagi (y/n)? : ")


print('\n\nTerima kasih kakak!')
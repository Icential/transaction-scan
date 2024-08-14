import spacy
import random
from spacy.training.example import Example


TRAIN_DATA = [
    ('tampilkan data contract dari cabang tangerang', {'entities': [(15, 23, 'TBL'), (29, 35, 'COC'), (36, 45, 'VLC')]}), 
    ('tampilkan data cashier dari cabang cideng', {'entities': [(15, 22, 'TBL'), (28, 34, 'COC'), (35, 41, 'VLC')]}), 
    ('tampilkan data kontrak dari cabang tomang', {'entities': [(15, 22, 'TBL'), (28, 34, 'COC'), (35, 41, 'VLC')]}), 
    ('tampilkan data kasir dari cabang grogol', {'entities': [(15, 20, 'TBL'), (26, 32, 'COC'), (33, 39, 'VLC')]}), 
    
    ('tunjukan data contract dari cabang tangerang', {'entities': [(14, 22, 'TBL'), (28, 34, 'COC'), (35, 44, 'VLC')]}),
    ('tunjukan data cashier dari cabang cideng', {'entities': [(14, 21, 'TBL'), (27, 33, 'COC'), (34, 40, 'VLC')]}),  
    ('tunjukan data kontrak dari cabang tomang', {'entities': [(14, 21, 'TBL'), (27, 33, 'COC'), (34, 40, 'VLC')]}), 
    ('tunjukan data kasir dari cabang grogol', {'entities': [(14, 19, 'TBL'), (25, 31, 'COC'), (33, 38, 'VLC')]}), 
    
    ('cari data contract dari cabang tangerang', {'entities': [(10, 19, 'TBL'), (24, 30, 'COC'), (31, 40, 'VLC')]}),
    ('cari data cashier dari cabang cideng', {'entities': [(10, 18, 'TBL'), (23, 29, 'COC'), (30, 36, 'VLC')]}), 
    ('cari data kontrak dari cabang tomang', {'entities': [(10, 18, 'TBL'), (23, 29, 'COC'), (30, 36, 'VLC')]}), 
    ('cari data kasir dari cabang grogol', {'entities': [(10, 14, 'TBL'), (21, 27, 'COC'), (28, 34, 'VLC')]}), 
    
    ('dapatkan data contract dari cabang tangerang', {'entities': [(14, 22, 'TBL'), (28, 34, 'COC'), (35, 44, 'VLC')]}),
    ('dapatkan data cashier dari cabang cideng', {'entities': [(14, 21, 'TBL'), (27, 33, 'COC'), (34, 40, 'VLC')]}), 
    ('dapatkan data kontrak dari cabang tomang', {'entities': [(14, 21, 'TBL'), (27, 33, 'COC'), (34, 40, 'VLC')]}), 
    ('dapatkan data kasir dari cabang grogol', {'entities': [(14, 19, 'TBL'), (25, 31, 'COC'), (33, 38, 'VLC')]}), 
    
    ('ambilkan data contract dari cabang tangerang', {'entities': [(14, 22, 'TBL'), (38, 34, 'COC'), (35, 44, 'VLC')]}), 
    ('ambilkan data cashier dari cabang cideng', {'entities': [(14, 21, 'TBL'), (27, 33, 'COC'), (34, 40, 'VLC')]}),
    ('ambilkan data kontrak dari cabang tomang', {'entities': [(14, 21, 'TBL'), (27, 33, 'COC'), (34, 40, 'VLC')]}), 
    ('ambilkan data kasir dari cabang grogol', {'entities': [(14, 19, 'TBL'), (25, 31, 'COC'), (33, 38, 'VLC')]}), 
    
    ('tampilkan kontrak yang bunganya di atas 10%', {'entities': [(10, 17, 'TBL'), (23, 31, 'COC'), (35, 39, 'LGC'), (40, 43, 'VLC')]}),
    ('tampilkan kontrak yang bunganya di bawah 9%', {'entities': [(10, 17, 'TBL'), (23, 31, 'COC'), (35, 40, 'LGC'), (41, 43, 'VLC')]}),
    ('tampilkan kontrak yang bunganya lebih dari 15%', {'entities': [(10, 17, 'TBL'), (23, 31, 'COC'), (32, 37, 'LGC'), (43, 46, 'VLC')]}),
    ('tampilkan kontrak yang bunganya kurang dari 7%', {'entities': [(10, 17, 'TBL'), (23, 31, 'COC'), (32, 38, 'LGC'), (44, 46, 'VLC')]}),

    ('tunjukan kontrak yang tenornya di atas 12 bulan', {'entities': [(9, 16, 'TBL'), (22, 30, 'COC'), (34, 38, 'LGC'), (39, 41, 'VLC')]}),
    ('tunjukan kontrak yang tenornya di bawah 24 bulan', {'entities': [(9, 16, 'TBL'), (22, 30, 'COC'), (34, 39, 'LGC'), (40, 42, 'VLC')]}),
    ('tunjukan kontrak yang tenornya lebih dari 36 bulan', {'entities': [(9, 16, 'TBL'), (22, 30, 'COC'), (31, 36, 'LGC'), (42, 44, 'VLC')]}),
    ('tunjukan kontrak yang tenornya kurang dari 18 bulan', {'entities': [(9, 16, 'TBL'), (22, 30, 'COC'), (31, 37, 'LGC'), (43, 45, 'VLC')]}),
    
    ('dapatkan customer yang umurnya di atas 45', {'entities': [(9, 16, 'TBL'), (23, 30, 'COC'), (34, 38, 'LGC'), (39, 41, 'VLC')]}),
    ('dapatkan customer yang umurnya di bawah 30', {'entities': [(9, 16, 'TBL'), (23, 30, 'COC'), (34, 39, 'LGC'), (40, 42, 'VLC')]}),
    ('dapatkan customer yang umurnya lebih dari 35', {'entities': [(9, 16, 'TBL'), (23, 30, 'COC'), (31, 36, 'LGC'), (42, 44, 'VLC')]}),
    ('dapatkan customer yang umurnya kurang dari 30', {'entities': [(9, 16, 'TBL'), (23, 30, 'COC'), (31, 37, 'LGC'), (43, 45, 'VLC')]}),

    ('cari customer yang tinggal di kota jakarta pusat', {'entities': [(5, 13, 'TBL'), (19, 26, 'COC'), (35, 48, 'VLC')]}),
    ('cari customer yang tinggal di kota semarang', {'entities': [(5, 13, 'TBL'), (19, 26, 'COC'), (35, 43, 'VLC')]}),
    ('cari customer yang tinggal di surabaya', {'entities': [(5, 13, 'TBL'), (19, 26, 'COC'), (30, 38, 'VLC')]}),
    ('cari customer yang tinggal di semarang', {'entities': [(5, 13, 'TBL'), (19, 26, 'COC'), (30, 38, 'VLC')]}),
    ('cari customer yang tinggal di kota jakarta barat', {'entities': [(5, 13, 'TBL'), (19, 26, 'COC'), (35, 48, 'VLC')]}),

    ('cari customer tinggal di alam sutera', {'entities': [(5, 13, 'TBL'), (14, 21, 'COC'), (25, 36, 'VLC')]}),
    ('cari data customer tinggal di alam sutera', {'entities': [(10, 18, 'TBL'), (19, 26, 'COC'), (30, 41, 'VLC')]}),
    ('customer yg tinggal di alam sutera', {'entities': [(0, 8, 'TBL'), (12, 19, 'COC'), (23, 34, 'VLC')]}),
    ('customer tinggal di alam sutera', {'entities': [(0, 8, 'TBL'), (9, 16, 'COC'), (20, 31, 'VLC')]}),
    ('customer yang tinggal di alam sutera', {'entities': [(0, 8, 'TBL'), (14, 21, 'COC'), (25, 36, 'VLC')]}),

    ('cari kontrak tenor kurang dari 120 bulan', {'entities': [(5, 12, 'TBL'), (13, 18, 'COC'), (19, 25, 'LGC'), (31, 34, 'VLC')]}),
    ('cari data kontrak tenor di bawah 3 bulan', {'entities': [(10, 17, 'TBL'), (18, 23, 'COC'), (27, 32, 'LGC'), (33, 34, 'VLC')]}),
    ('kontrak tenor kurang dari 6 bulan', {'entities': [(0, 7, 'TBL'), (8, 13, 'COC'), (14, 20, 'LGC'), (26, 27, 'VLC')]}),
    ('kontrak yang tenor lebih dari 24 bulan', {'entities': [(0, 7, 'TBL'), (13, 18, 'COC'), (19, 24, 'LGC'), (30, 32, 'VLC')]}),
    ('kontrak yg tenor di atas 12 bulan', {'entities': [(0, 7, 'TBL'), (11, 16, 'COC'), (20, 24, 'LGC'), (25, 27, 'VLC')]}),
]


def train_spacy(data,iterations):
    TRAIN_DATA = data
    nlp = spacy.blank('en')  # create blank Language class
    # create the built-in pipeline components and add them to the pipeline
    # nlp.create_pipe works for built-ins that are registered with spaCy
    if 'ner' not in nlp.pipe_names:
        ner = nlp.create_pipe('ner')
        nlp.add_pipe('ner')
       

    # add labels
    for _, annotations in TRAIN_DATA:
         for ent in annotations.get('entities'):
            #print(ent)
            ner.add_label(ent[2])

    # get names of other pipes to disable them during training
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != 'ner']
    with nlp.disable_pipes(*other_pipes):  # only train NER
        optimizer = nlp.begin_training()
        for itn in range(iterations):
            print("Starting iteration " + str(itn))
            random.shuffle(TRAIN_DATA)
            losses = {}
            for text, annotations in TRAIN_DATA:
                doc = nlp.make_doc(text)
                example = Example.from_dict(doc, annotations)
                nlp.update([example], drop=0.2, losses=losses, sgd=optimizer)
                #print(text)
                #print(annotations)
            print(losses)
    return nlp


prdnlp = train_spacy(TRAIN_DATA, 50)


# for text, _ in TRAIN_DATA:
#     doc = prdnlp(text)
#     print("Entities", [(ent.text, ent.label_) for ent in doc.ents])
#     print("Tokens", [(t.text, t.ent_type_, t.ent_iob) for t in doc])

# Save our trained Model
modelfile = input("Enter your Model Name: ")
prdnlp.to_disk(modelfile)

#Test your text
test_text = input("Enter your testing text: ")
doc = prdnlp(test_text)
for ent in doc.ents:
    print(ent.text, ent.start_char, ent.end_char, ent.label_)
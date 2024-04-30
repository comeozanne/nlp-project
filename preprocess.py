import json
from transformers import AutoTokenizer
import yaml
import pandas as pd
import datasets

data = json.load(open("entities.json"))
with open("tokens.yml") as f:
    tags_file = yaml.load(f, Loader=yaml.FullLoader)


def get_labels(tokens):
    tags = {}
    for token in tokens:
        tags[tokens[token]["start"]] = token
    return tags

tag2literal = get_labels(tags_file)

def get_literal(tags):
    res=[]
    for tag in tags:
        res.append(tag2literal.get(tag))
    return res

literal2tag = get_literal(tag2literal)


def split_sentence(sentence, all_tags):
    words = []
    tags = []
    current_tag = None
    current_word = None
    for word in sentence.split(" "):
        if word.startswith(tuple(all_tags)):
            if current_word is not None:
                words.append(current_word)
                tags.append(current_tag)
            current_tag = word[0]
            current_word = word[1:]
        else:
            current_word += " " + word

    return words, tags


def replace_idem(text, labels, prev_text=None, prev_labels=None):
    if prev_text is None or prev_labels is None:
        prev_text = text
        prev_labels = labels

    updated_text = []
    updated_labels = []

    for i in range(len(text)):
        if text[i] == 'idem':
            updated_text.append(prev_text[i])
            updated_labels.append(prev_labels[i])
        else:
            updated_text.append(text[i])
            updated_labels.append(labels[i])

    return {'text': updated_text, 'labels': updated_labels}


def get_dataset():
    data = json.load(open("entities.json"))
    res = pd.DataFrame(columns=["text", "labels"])
    text = []
    labels = []
    for image in data.keys():
        sentences = data[image]
        for sentence in sentences.split("\n"):
            try:
                words, tags = split_sentence(sentence, tag2literal.keys())
                text.append(words)
                labels.append(get_literal(tags))
            except Exception as e:
                print('sentence not in right format : ', sentence)

    res["text"] = text
    res["labels"] = labels
    return res

def replace_idem_in_dataset(df):
    prev_text = None
    prev_labels = None
    res=pd.DataFrame(columns=["text", "labels"])

    for i, row in df.iterrows():
        text = row['text']
        labels = row['labels']
        if 'idem' in text:
            if prev_text==None or len(text)==len(prev_text):
                updates = replace_idem(text, labels, prev_text, prev_labels)
                res.loc[i, 'text'] = updates['text']
                res.loc[i, 'labels'] = updates['labels']

                prev_text = updates['text']
                prev_labels = updates['labels']
            else :
                print("Error: len(text) != len(prev_text)")
                print("prev_text: ", prev_text)
                print("text: ", text)
        else:
            res.at[i,'text']=text
            res.at[i,'labels']=labels
            prev_text=text
            prev_labels=labels

    return res

if __name__ == "__main__":
    df = get_dataset()
    df = replace_idem_in_dataset(df)
    df.to_csv("data.csv", index=False)

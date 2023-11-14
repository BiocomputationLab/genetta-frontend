import spacy
from fuzzywuzzy import fuzz, process
import re

iri_p = re.compile(r'(?i)\b((?:https?|ftp):\/\/[^\s/$.?#].[^\s]*)\b')
class LanguageAnalyser:
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')

    def break_text(self, text):
        doc = self.nlp(text)
        sentences = []
        for sent in doc.sents:
            sentences.append(sent.text)
        return sentences

    def get_subject(self, sentence):
        doc = self.nlp(sentence)
        subject = None
        for token in doc:
            if token.dep_ == "nsubj":
                subject = token.text
                break
        return subject

    def get_proper_nouns(self, text):
        doc = self.nlp(text)
        return [token.text for token in doc if token.pos_ == "PROPN"]

    def get_nouns(self, text):
        doc = self.nlp(text)
        return [token.text for token in doc if token.pos_ == "NOUN"]

    def get_all_nouns(self, text):
        doc = self.nlp(text)
        return [token.text for token in doc if token.pos_ == "NOUN" or
                token.pos_ == "PROPN"]
    
    def get_non_stop_words(self,text):
        doc = self.nlp(text)
        return [token.text for token in doc if 
                not token.is_stop and 
                not token.is_punct and 
                not token.is_space]

    def get_all_uris(self,text):
        return re.findall(iri_p, text)
    

    def similarity(self,word1,word2):
        token1 = self.nlp(word1)
        token2 = self.nlp(word2)
        return token1.similarity(token2)
        

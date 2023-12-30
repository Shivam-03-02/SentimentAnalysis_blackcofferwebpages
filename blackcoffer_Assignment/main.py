from bs4 import BeautifulSoup
import requests
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
import re
import string
filpa='./input.xlsx'
df=pd.read_excel(filpa)

nltk.download('punkt')


for i in range(0,int(df.size/2)):
    f=requests.get(df['URL'][i])
    if f.status_code==200:
        soup=BeautifulSoup(f.text,'html.parser')
        file=open(df['URL_ID'][i]+'.txt','w',encoding='utf-8')
        container=soup.find('div',class_='td-post-content tagdiv-type')
        if container==None:  
            container=soup.findAll('div',class_='tdb-block-inner td-fix-index')
            for i in container:
                if len(i.contents)>10:
                    container=i

        if container.find('pre')!=None:
            elem_toremove=container.find('pre')
            elem_toremove.extract()
        title=soup.find('h1')
        file.write(title.text+'\n')    
        file.write(container.text)


def findtotalstopwords():
    stopwords=set()
    stopfile=open('./StopWords/StopWords_Auditor.txt','r')
    stfil1=stopfile.read().split()
    for i in stfil1:
        stopwords.add(i) 
    stopfile2=open('./StopWords/StopWords_Currencies.txt','r')
    stfil2=stopfile2.read().split()
    for i in range(0,len(stfil2),2):
        stopwords.add(stfil2[i])
    stopfile3=open('./StopWords/StopWords_Currencies.txt','r')
    stfil3=stopfile3.read().split()
    for i in range(0,len(stfil3)):
        if stfil3[i]=='|':
            i+=2
            if i>=len(stfil3):
                break
        stopwords.add(stfil3[i])
    stopfile4=open('./StopWords/StopWords_Generic.txt','r')
    stfil4=stopfile4.read().split()
    for i in stfil4:
        stopwords.add(i)    
    stopfile5=open('./StopWords/StopWords_GenericLong.txt','r')
    stfil5=stopfile5.read().split()
    for i in stfil5:
        stopwords.add(i)        
    stopfile6=open('./StopWords/StopWords_Geographic.txt','r')
    stfil6=stopfile6.read().split()
    for i in range(0,len(stfil6)):
        if stfil6[i]=='|':
            i+=2
        stopwords.add(stfil6[i])        
    stopfile7=open('./StopWords/StopWords_Names.txt','r')
    stfil7=stopfile7.read().split()
    for i in range(0,len(stfil7)):
        if stfil7[i]=='|':
            i+=8
        stopwords.add(stfil7[i])
    return stopwords    


def create_sentiment_dictionary():
    positive_wordsfile=open('./MasterDictionary/negative-words.txt','r')
    negative_wordsfile=open('./MasterDictionary/positive-words.txt','r')
    positive_words = set()
    negative_words = set()
    stop_words=findtotalstopwords()
    for i in positive_wordsfile.read().split():
        if i not in stop_words:
            positive_words.add(i)
    for j in positive_wordsfile.read().split():
        if j not in stop_words:
            negative_words.add(j)     
    return positive_words, negative_words

def clean_totalwords(dictionary):
    all_punctuation=string.punctuation
    for word in all_punctuation:
        if word in dictionary:
            dictionary.remove(word)
            
    return dictionary

def totalcharactercount(words):
    sum=0
    for i in words:
        sum+=len(i)
    return sum    
def complexword_count(cleaned_words):
    vowels = ["a", "e", "i", "o", "u"]
    count_complexwords=0
    count_vowels=0
    total_syllable=0
    for i in cleaned_words:
        if i[-2:]=='es' or i[-2:]=='ed':
            continue  
        count_vowels=0
        for j in i:
            if j in vowels:
                count_vowels+=1
            if count_vowels >2: 
                count_complexwords+=1
        total_syllable+=count_vowels            
    return count_complexwords,total_syllable            


def count_personal_pronouns(text):
    pronouns = ["I", "we", "my", "ours", "us"]
    pattern = r'\b(?:' + '|'.join(re.escape(pronoun) for pronoun in pronouns) + r')\b(?!s*\bUS\b)'
    for i in text:
        matches = re.findall(pattern, i, flags=re.IGNORECASE)
    pronoun_counts = {pronoun: matches.count(pronoun) for pronoun in pronouns}
    return sum(pronoun_counts.values())
                   
def perform_custom_sentiment_analysis(text, positive_words, negative_words):
    words = text.lower().split()
    sentences=sent_tokenize(text)
    stop_words=findtotalstopwords()
    stop_words={word.lower() for word in stop_words}

    words_without_stopwords = [word.lower() for word in words if word.lower() not in stop_words]
    cleaned_words=clean_totalwords(words_without_stopwords)
    text_without_stopwords = ' '.join(words_without_stopwords)
    positive_count = sum(word in positive_words for word in words)
    negative_count = sum(word in negative_words for word in words)

    total_words = len(cleaned_words)
    total_complexwords,totalsyllable_count=complexword_count(cleaned_words)
    total_sentences= len(sentences)
    positive_score = positive_count / total_words
    negative_score = negative_count / total_words
    polarity_score = (positive_score - negative_score) / (positive_score + negative_score + 0.000001)
    subjectivity_score = (positive_score + negative_score)/(total_words + 0.000001)
    avg_sentence_length=total_words/total_sentences
    Percentage_of_complex_words=total_complexwords/total_words
    fog_index=0.4*(avg_sentence_length + Percentage_of_complex_words)
    syllableperword=totalsyllable_count/total_words
    total_pronouns=count_personal_pronouns(words_without_stopwords)
    avg_wordlength=totalcharactercount(cleaned_words)/total_words
    return {'positive score': positive_score, 'negative score': negative_score,'polarity score': polarity_score,'subjectivity score': subjectivity_score,'Avg sentence length': avg_sentence_length,'Percentage of complex words':Percentage_of_complex_words,'fog index':fog_index,'avg number of words per sentence':avg_sentence_length,'complex word count':total_complexwords,'word count':total_words,'syllable per word':syllableperword,'personal pronouns':total_pronouns,'Avg Word Length':avg_wordlength}

positive_words, negative_words = create_sentiment_dictionary()

df2=pd.read_excel('./Output Data Structure.xlsx')
for i in range(1,101):
    f=open('./blackassign000'+str(1)+'.txt','r')
    text_to_analyze = f.read()
    sentiment_scores = perform_custom_sentiment_analysis(text_to_analyze, positive_words, negative_words)
    for key in sentiment_scores.keys():
        df2[key.upper()][i-1]=sentiment_scores[key]
        
df2.to_excel('./Output Data Structure.xlsx', index=False, engine='openpyxl')

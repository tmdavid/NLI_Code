from __future__ import print_function
import pandas as pd
from os.path import splitext
import string
import re
import argparse
from collections import Counter, defaultdict
import numpy as np

__author__ = 'david_torrejon'

"""
TODO

implement the option to download data direct from snli webpage + uncompress...
http://nlp.stanford.edu/projects/snli/snli_1.0.zip
"""


"""
# all the functions here are prepared to deal with snli corpus provided, hence a list of strings, not a whole text.

Simple Implementation of the GloVe model:
Jeffrey Pennington, Richard Socher, and Christopher D. Manning. 2014. GloVe: Global Vectors for Word Representation.
http://nlp.stanford.edu/projects/glove/

X -> co-ocurrence matrix
Xij = number of times j appears in context of i
Xi = SUMk(Xik)
Pij = P(j|i)= Xij/Xi Probability of j appear in i

Context -> sentence
"""

'''
"sentence1_parse": "(ROOT (S (NP (CD Two) (NNS women)) (VP (VBP are) (VP (VBG embracing) (SBAR (IN while) (S (NP (VBG holding)) (VP (TO to) (VP (VB go) (NP (NNS packages)))))))) (. .)))", "sentence2": "The sisters are hugging goodbye while holding to go packages after just eating lunch.", "sentence2_binary_parse": "( ( The sisters ) ( ( are ( ( hugging goodbye ) ( while ( holding ( to ( ( go packages ) ( after ( just ( eating lunch ) ) ) ) ) ) ) ) ) . ) )", "sentence2_parse": "(ROOT (S (NP (DT The) (NNS sisters)) (VP (VBP are) (VP (VBG hugging) (NP (UH goodbye)) (PP (IN while) (S (VP (VBG holding) (S (VP (TO to) (VP (VB go) (NP (NNS packages)) (PP (IN after) (S (ADVP (RB just)) (VP (VBG eating) (NP (NN lunch))))))))))))) (. .)))"}
"sentence2_parse": "(ROOT (S (NP (CD Two) (NN woman)) (VP (VBP are) (VP (VBG holding) (NP (NNS packages)))) (. .)))"}
"sentence2_parse": "(ROOT (S (NP (DT The) (NNS men)) (VP (VBP are) (VP (VBG fighting) (PP (IN outside) (NP (DT a) (NNS deli))))) (. .)))"}
'''


parser = argparse.ArgumentParser(description='Get File to process with GloVe')
parser.add_argument('-f', metavar='file_name', type=str, nargs=1, help='name of the file')

#some parameters
default_folder = 'snli_1.0/'
ndimensions = 300
#not_useful tokens
non_useful_tokens = ['a', 'the']

#functions
def test_init():
    glove_init()

def token_count(corpus, ndim):
    tokens_dict = defaultdict(int) #empty dict faster access than checking if its in a list
    word2idx = {}
    idx = 1
    for sentence in corpus:
        regex = re.compile('[%s]' % re.escape(string.punctuation))
        sentence = regex.sub('', sentence).lower()
        #print (sentence)
        tokens_sentence = sentence.split(" ")
        for token in tokens_sentence:
            #print (token)
            if token not in non_useful_tokens:
                tokens_dict[token]+=1
            if token not in word2idx:
                word2idx[token] = idx
                #print (token, idx)
                idx +=1

    #tokens_list = sorted(tokens_dict.items(), key=itemgetter(1), reverse=True)
    c = Counter(tokens_dict)
    common_tokens = c.most_common()
    print (common_tokens[:10])
    #print (sum(c.values()))
    # return 300 most common tokens
    # can return all and after matrix pick 300 better?
    return common_tokens, word2idx, idx

def convert_sentence_index(sentence, word2id):
    sindex = []
    regex = re.compile('[%s]' % re.escape(string.punctuation))
    sentence = regex.sub('', sentence).lower()
    #print (sentence)
    tokens_sentence = sentence.split(" ")
    for token in tokens_sentence:
        sindex.append(word2id[token])
    return sindex

def get_coocu_matrix(corpus, word2idx, rows):
    # not proper for computations...would be better a np matrix but to represent... word -> index?
    cooc_m = np.zeros((rows+1, rows+1))
    print ('Matrix of size',cooc_m.size,'created...')
    print ('Generating coocurrence matrix...')
    """
      1  2  3  -> first row and first column have indexes of words
    1 x  y  z
    2 x1 y1 z1
    3 x2 y2 z2

    """
    for sentence in corpus:
        #print (sentence)
        idx_sent = convert_sentence_index(sentence, word2idx)
        #print (idx_sent)
        for idx_s in idx_sent:
            cooc_m[idx_s][0]=idx_s
            for idx_w in idx_sent:
                cooc_m[0][idx_w]=idx_w
                cooc_m[idx_s][idx_w]+=1
    print (cooc_m[0])
    print (cooc_m[:,0])
    print (cooc_m[1])




def glove_init():
    try:
        args = parser.parse_args()
        file_name = default_folder + args.f[0]
        print("Reading file", file_name, "...")
        file_path, file_ext = splitext(file_name)
        with open(file_name, 'rb') as f:
            data = f.readlines()
            data_json_str = "[" + ','.join(data) + "]"
            data_df = pd.read_json(data_json_str)
        print(file_ext,"loaded...")
        # sentence1_parse sentence2_parse, sentence1, sentence2
        keep_columns = ['sentence1','sentence2','sentence1_parse','sentence2_parse']
        data_df = data_df[keep_columns]
        sentences = data_df['sentence1'].tolist() + data_df['sentence2'].tolist()
        '''
        I dont know whether to delete 2 sentences from sentence 1, because there are
        3 sentences meaning the same for every pack of sentencnes
        s1-s2 E, s1-s2 N, s1-s2 C, where s1 is always same
        '''
        # build dictionary?
        print("Counting word appearances...")
        tokens, word2index, nidx = token_count(sentences, ndimensions)
        coocurrence_matrix = get_coocu_matrix(sentences, word2index, nidx)

    except BaseException as e:
        print (e)


test_init()

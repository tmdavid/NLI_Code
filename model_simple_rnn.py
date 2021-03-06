__author__ = 'david_torrejon'


"""
This module implements a simple RNN model for the snli paper:
http://nlp.stanford.edu/pubs/snli_paper.pdf
"""


from keras.layers import recurrent
from keras.models import Sequential, slice_X
from keras.layers.core import Activation, TimeDistributedDense, RepeatVector, Merge, Dense, Dropout, Flatten, Reshape
from keras.regularizers import l2, activity_l2
from keras.optimizers import SGD
from keras.layers.embeddings import Embedding
from keras.preprocessing.text import Tokenizer, one_hot, base_filter
from keras import backend as K

import numpy as np
import glove
from extract_sentences import return_sparse_vector


class paper_model():
    #parameters
    def __init__(self, number_stacked_layers=3, dimensions_emb=300, is_tbir=False):
        self.RNN = recurrent.LSTM
        self.stacked_layers = number_stacked_layers
        self.dimensions_emb = dimensions_emb #dimensions of embeddings
        self.weights_path = "./weights.hdf5" #weights_maxlen
        self.nli_model = ''

        if is_tbir:
            self.filename_output = 'predictions_tbir.txt'
            open(self.filename_output, 'w')
        else:
            self.filename_output = 'predictions.txt'
            open(self.filename_output, 'w')
    #NN paramters!
    """
    simply a stack of three 200d
    tanh layers, with the bottom layer taking the concatenated
    sentence representations as input and the
    top layer feeding a softmax classifier, all trained
    jointly with the sentence embedding model itself.
    """

    """
    models are randomly
    initialized using standard techniques and trained using AdaDelta (Zeiler, 2012) minibatch SGD until
    performance on the development set stops improving.
    We applied L2 regularization to all models, manually tuning the strength coefficient (lambda) for
    each, and additionally applied dropout (Srivastava et al., 2014) to the inputs
    and outputs of the sentence embedding models (though not to its internal
    connections) with a fixed dropout rate. All models were implemented in a common framework for this paper.
    """
    def file_len(self, fname):
        i=0
        try:
            with open(fname) as f:
                for i, l in enumerate(f):
                    pass
            return i + 1
        except:
            open(fname, "w")
            return 0

    def data_preparation_nn(self, sentences, diferences=3):
        premises_encoded = []
        hypothesis_encoded = []
        expected_output = []
        for data in sentences:
            #print data[0][0].shape, data[0][1].shape
            if data[2] <= diferences:
                premises_encoded.append(data[0][0])
                hypothesis_encoded.append(data[0][1])
                expected_output.append(data[1])
        return np.asarray(premises_encoded), np.asarray(hypothesis_encoded), np.asarray(expected_output)

    def data_tbir_preparation(self, sentences):
        premises_encoded = []
        hypothesis_encoded = []
        expected_output = []
        id_query=[]
        id_premises=[]
        for data in sentences:
            premises_encoded.append(data[0][0])
            hypothesis_encoded.append(data[0][1])
            expected_output.append(data[1])
            id_query.append(data[2])
            id_premises.append(data[3])
        return np.asarray(premises_encoded), np.asarray(hypothesis_encoded), expected_output, id_query, id_premises


    def build_model(self, emb_init,  n_symbols, LOAD_W=True, max_pre=45, max_hypo=45):
                   #DROPOUT TO INPUT AND OUTPUTS OF THE SENTENCE EMBEDDINGS!!

        print('Build embeddings model...')
        #check this maxlen
        maxlen = 45

        premise_model = Sequential()
        hypothesis_model = Sequential()
        # 2 embedding layers 1 per premise 1 per hypothesis
        #shared_emb_layer = Embedding(output_dim=300, input_dim=n_symbols + 1, mask_zero=True, weights=[emb_init])


        premise_model.add(Embedding(output_dim=300, input_dim=n_symbols + 1, mask_zero=True, weights=[emb_init]))
        premise_model.add(Dropout(0.1))
        premise_model.add(self.RNN(100, return_sequences=False)) #best perf is 300
        premise_model.add(Dropout(0.1))

        hypothesis_model.add(Embedding(output_dim=300, input_dim=n_symbols + 1, mask_zero=True, weights=[emb_init]))
        hypothesis_model.add(Dropout(0.1))
        hypothesis_model.add(self.RNN(100, return_sequences=False)) #best perf is 300
        hypothesis_model.add(Dropout(0.1))

        print('Concat premise + hypothesis...')
        self.nli_model = Sequential()
        self.nli_model.add(Merge([premise_model, hypothesis_model], mode='mul', concat_axis=1))#concat irrelevant if mult
        self.nli_model.add(Dense(input_dim=100, output_dim=200, init='normal', activation='tanh')) #input 600 output 200d
        for i in range(1, self.stacked_layers-1):
            print ('stacking %d layer')%i
            self.nli_model.add(Dense(input_dim=200, output_dim=200, init='normal', activation='tanh')) #200d

        print ('stacking last layer')
        self.nli_model.add(Dense(input_dim=200, output_dim=3, init='normal', activation='tanh')) #200d
        print ('Softmax layer...')
        # 3 way softmax (entail, neutral, contradiction)
        self.nli_model.add(Dense(3, init='uniform'))
        self.nli_model.add(Activation('softmax')) # care! 3way softmax!

        print('Compiling model...')
        #sgd = SGD(lr=0.1, decay=1e-6, momentum=0.9, nesterov=True)
        self.nli_model.compile(loss='categorical_crossentropy', optimizer='rmsprop')
        print('Model Compiled')
        #print self.nli_model.summary()
        #print('generating sparse vectors(1hot encoding) from sentences...')

        if LOAD_W:
            print('loading weights...')
            self.nli_model.load_weights(self.weights_path)

    def train_model(self, data_train, batch_range):

        #split data
        #data preparation
        #print data_train[0]
        premises_encoded, hypothesis_encoded, expected_output = self.data_preparation_nn(data_train, 3)

        """
        nb_samples, timesteps, input_dim) means:
        - nb_samples samples (examples)
        - for each sample, a number of time steps (the same for all samples in the batch)
        - for each time step of each sample, input_dim features.
        NEEEEED TO CONVER DATA TO SPARSE VECTORSSASDASD
        """

        '''
        TODO PREPARE DATA OUTSIDE HERE TO GENERATE BOTH TEST AND TRAIN
        '''

        print('premsises shape and sample....')
        print premises_encoded.shape
        print('hypothesis shape and sample....')
        print hypothesis_encoded.shape
        print('output shape and sample....')
        print expected_output.shape
        print expected_output[0]

        #(nb_samples, timesteps, input_dim). -> (expected_output[0], [1], len_vocab)

        X = [premises_encoded, hypothesis_encoded]
        #print X[0]
        #raise SystemExit(0)
        # I dont want the conversion here, make the conversion somewhere else, for esthetic purpouses
        print('training....')
        history = self.nli_model.fit(X, expected_output, batch_size=64, nb_epoch=1, verbose=1, sample_weight=None, show_accuracy=True)
        #print self.nli_model.layers[0].get_output(train=True)[0].eval({self.nli_model.layers[0].input[0]: X[0].astype(np.int32)})
        #print self.nli_model.layers[2].get_inputs(train=True)[0].eval({self.nli_model.layers[0].input[0]: X[0].astype(np.int32)})
        if batch_range == 540000:
            lines = self.file_len("lossfile.txt")
            loss_file = open("lossfile.txt", "a")
            for loss in history.history['loss']:
                lines+=1
                loss_file.write("("+str(lines)+","+str(loss)+")\n")


        print('saving weights')
        self.nli_model.save_weights(self.weights_path, overwrite=True)

    def test_model(self, data_test,  test_file, is_tbir=False):

        print ('testing....')
        if is_tbir is False:
            premises_encoded_t, hypothesis_encoded_t, expected_output_t = self.data_preparation_nn(data_test, 3)
        else:
            #print data_test[0]
            premises_encoded_t, hypothesis_encoded_t, expected_output_t, img_query_t, id_querys = self.data_tbir_preparation(data_test)

        print('premsises shape and sample....')
        print premises_encoded_t.shape
        print('hypothesis shape and sample....')
        print hypothesis_encoded_t.shape

        X_t = [premises_encoded_t, hypothesis_encoded_t]
        #print X_t[0]
        score = self.nli_model.evaluate(X_t, expected_output_t, batch_size=64, show_accuracy=True, verbose=1)
        predictions = self.nli_model.predict(X_t, batch_size=64, verbose=1)


        """
        store results?
        """
        correct = 0
        f = open(self.filename_output, 'w')
        g = open("wrong_pairs.txt", "w")
        if is_tbir:
            for pred, e_out, id_query, idq in zip(predictions, expected_output_t, img_query_t, id_querys):
                #print np.argmax(pred), np.argmax(e_out)
                if np.argmax(pred) == np.argmax(e_out): #np arrays!
                    correct +=1
                sup = str(pred) + " " + str(e_out) + " " + str(id_query) + " " + str(idq)
                f.write(sup)
                f.write('\n')

        else:
            list_premises = test_file['sentence1'].tolist()
            list_hypothesis = test_file['sentence2'].tolist()
            for pred, e_out, p, h in zip(predictions, expected_output_t, list_premises, list_hypothesis):
                #print np.argmax(pred), np.argmax(e_out)
                if np.argmax(pred) == np.argmax(e_out): #np arrays!
                    correct +=1
                else:
                    sup = str(pred) + " " + str(e_out)
                    f.write(sup)
                    f.write('\n')
                    wrong = str(p) + "#" + str(h) + "\n"
                    g.write(wrong)

            g.close()
            perc = float(correct)/float(len(predictions))
            print 'Predictions correct ', correct,'out of',len(predictions), 'acc(%): ', perc
            #print out
            #add graph of the test set learning.
        f.close()
        return perc

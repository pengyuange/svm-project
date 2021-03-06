
from xlrd import open_workbook
from xlwt import *
from sklearn import svm
from sklearn import *
from sklearn.cross_validation import *
from math import pow
from collections import defaultdict 
import hashlib
import itertools
import numpy as np
from scrape_uniprot import *
from global_alignment import *



#http://en.wikipedia.org/wiki/Amino_acid#Classification
"""
Aliphatic:	Glycine, Alanine, Valine, Leucine, Isoleucine
Hydroxyl or Sulfur/Selenium-containing:	Serine, Cysteine, Selenocysteine, Threonine, Methionine
Cyclic:	Proline
Aromatic:	Phenylalanine, Tyrosine, Tryptophan
Basic:	Histidine, Lysine, Arginine
Acidic and their Amide:	Aspartate, Glutamate, Asparagine, Glutamine
"""
#Map using above grouping of AA's
AA1 = {"G":1, "A":1, "V":1, "L":1, "I":1,
		"S":2, "C":2, "U":2, "T":2, "M":2,
		"P":3,
		"F":4, "Y":4, "W":4,
		"H":5, "K":5, "R":5,
		"D":6, "E":6, "N":6, "Q":6}

#http://en.wikipedia.org/wiki/Proteinogenic_amino_acid#Non-specific_abbreviations
AA2 = {'R':1, 'H':1, 'K':1,
		'D':2, 'E':2,
		'S':3, 'T':3, 'N':3, 'Q':3,
		'C':4, 'U':4, 'G':4, 'P':4,
		'A':5, 'I':5, 'L':5, 'M':5, 'F':5, 'W':5, 'Y':5, 'V':5}

#http://www.ann.com.au/MedSci/amino.htm (for AA3, AA4, AA5)
# nonpolar, polar, acidic(polar), basic(polar)
AA3 = {'G':1, 'A':1, 'V':1, 'L':1, 'I':1, 'P':1, 'M':1, 'F':1, 'W':1,
	'S':2, 'T':2, 'N':2, 'Q':2, 'C':2, 'Y':2,
	'D':3, 'E':3,
	'K':4, 'R':4, 'H':4}
#structure
AA4 = {'G':1, 'A':1, 
		'V':2, 'L':2, 'I':2, 
		'P':3, 'F':3, 
		'Y':4, 'W':4, 
		'M':5, 
		'S':6, 'T':6, 
		'C':7,
		'Q':8, 'N':8,
		'D':9, 'E':9,
		'K':10, 'R':10, 'H':10
		}
AA5 = {'G':1, 'A':1, 'V':1, 'L':1, 'I':1,
		'C':2, 'M':2,
		'F':3, 'Y':3, 'W':3,
		'S':4, 'T':4, 'N':4, 'Q':4,
		'E':5, 'D':5,
		'K':6, 'R':6, 'H':6,
		'P':7 
		}	

"""
G - Glycine (Gly)
P - Proline (Pro)
A - Alanine (Ala)
V - Valine (Val)
L - Leucine (Leu)
I - Isoleucine (Ile)
M - Methionine (Met)
C - Cysteine (Cys)
F - Phenylalanine (Phe)
Y - Tyrosine (Tyr)
W - Tryptophan (Trp)
H - Histidine (His)
K - Lysine (Lys)
R - Arginine (Arg)
Q - Glutamine (Gln)
N - Asparagine (Asn)
E - Glutamic Acid (Glu)
D - Aspartic Acid (Asp)
S - Serine (Ser)
T - Threonine (Thr)
"""
#One letter codes for AA's
AA = ['G', 'P', 'A', 'V', 'L', 'I', 'M', 'C',
		'F', 'Y', 'W', 'H', 'K', 'R', 'Q', 'N',
		'E', 'D', 'S', 'T']

		
#(seq, kwargs["id"], kwargs["function_dict"], kwargs["all_functions"])

def function_features(seq, seq_id,function_dict, all_functions):
	occurences = [0]*len(all_functions)
	print "ID: " + str(seq_id)
	function_list = function_dict[seq_id]
	print "list: " + str(function_list)
	for i in range(0, len(all_functions)):
		func = all_functions[i]
		if func in function_list:
			occurences[i] = 1
		
	print 'END FUNCTION FEAUTRES'
	return occurences

def alignment_features(seq, sequences):
	similarity = [0] * len(sequences)
	scores = [0]* len(sequences)
	for i in range(0, len(sequences)):
		score = getAlignment(seq, sequences[i], 1, -1, -1)
		scores[i] = score

	
	
	my_max = np.max(scores)
	old_scores = np.copy(scores)
	scores.remove(my_max)	#remove the highest score because that is the same
	my_max = np.max(scores)
	stdv = np.std(scores)
	thresh = my_max - stdv


	print 'stdv: ' + str(stdv)
	print 'max: ' + str(my_max)
	print 'thresh: ' + str(thresh)
	for i in range(0, len(sequences)):
		if old_scores[i]>thresh:
			similarity[i] = 1
	
	print similarity
	return similarity


#Returns list of all possible n_grams
def all_n_grams(n):
	#each elt. in list is a tuple of AA's
	grams = list(itertools.product(AA, repeat=n))
	
	#convert tuples to strings
	for index, AA_tuple in enumerate(grams):
		gram = ""
		for a in AA_tuple:
			gram += a
		grams[index] = gram
	return grams

#Returns list of all possible AAn n_grams
#e.g. a 3-gram may be '152': AA in 1st group, AA in 5th group, ...
def all_AAn_n_grams(AAn, n):
    num_groups = len(set(AAn.values()))
    groups = [i for i in range(1, num_groups+1)]
    grams = list(itertools.product(groups, repeat=n))

    for index, group_tuple in enumerate(grams):
		gram = ""
		for x in group_tuple:
			gram += str(x)
		grams[index] = gram
    return grams

#Returns vector counting how many of each possible n_gram occured
#Length of vector is length of all_n_grams
#occurences[i] = # times all_n_grams[i] occured in seq
def n_gram_counts(seq, n, all_n_grams):
	#n_grams = all_n_grams(n)
	occurences = [0]*len(all_n_grams)
	for i in range(0, len(seq) - n):
		gram = ''
		for j in range(i, i+n):
			gram += seq[j]
		index = all_n_grams.index(gram)
		occurences[index] += 1
	#For RELATIVE frequencies
	#Note: Choice of constant (50) makes a big difference
	#After a certain threshold, increasing constant doesn't seem to improve
	#for i, count in enumerate(occurences):
	#	occurences[i] = float(count) / float(len(seq)) * 50
	return occurences

def AAn_n_gram_counts(seq, AAn, n, all_AAn_n_grams):
	occurences = [0]*len(all_AAn_n_grams)
	for i in range(0, len(seq) - n):
		gram = ''
		for j in range(i, i+n):
			gram += str(AAn[seq[j]])
		index = all_AAn_n_grams.index(gram)
		occurences[index] += 1
	return occurences

#Count occurences of each Amino Acid
def AA_counts(seq):
	AA = {'G':0, 'P': 1, 'A': 2, 'V':3, 'L':4,
		'I':5, 'M':6, 'C':7, 'F':8, 'Y':9,
		'W':10, 'H':11, 'K':12, 'R':13, 'Q':14,
		'N':15,'E':16, 'D':17, 'S':18, 'T':19}
	counts = [0] * 20
	for a in seq:
		counts[AA[a]] += 1
	return counts

#Count occurences of each class of AA
def AAn_counts(seq, AAn):
	counts = [0] * len(set(AAn.values()))
	for a in seq:
		#Grouping values consecutive indexed by 1
		counts[AAn[a] - 1] += 1
	return counts 


max_seq_len = 465 
#Map sequence to groupings
#Len(feature vector) = len(seq)
#v[i] = which group seq[i] is in according to AAn
def map_seq(seq, AAn):
	mapped_features = []
	for a in seq: #map AA's using 1st AA grouping
		mapped_features.append(AAn[a])
	mapped_features += [0 for _ in range(max_seq_len-len(seq))] # pad with zero's (seqs have diff lengths)
	return mapped_features

#Count distance between next occurence of each AA
#[G1, G2, G3, P1, P2, P3, ...]
#G2 = num. of G's that were followed by a G 2 AA's later
def AA_distances(seq, n):
	AA = {'G':0, 'P': 1, 'A': 2, 'V':3, 'L':4,
		'I':5, 'M':6, 'C':7, 'F':8, 'Y':9,
		'W':10, 'H':11, 'K':12, 'R':13, 'Q':14,
		'N':15,'E':16, 'D':17, 'S':18, 'T':19}

	distances = [0]*len(AA)*n

	for i, A in enumerate(seq):
		for j in range(i, len(seq)):
			if seq[j] == A and j-i <= n:
				dist = j-i
				distances[AA[A]*n + (dist-1)] += 1
	return distances

#AA_distances but groupings instead of AA's themselves
def AAn_distances(seq, AAn, n):
	distances = [0]*len(set(AAn.values()))*n

	for i, A in enumerate(seq):
		for j in range(i, len(seq)):
			if AAn[seq[j]] == AAn[A] and j-i <= n:
				dist = j-i
				#AAn's indexed from 1
				distances[ (AAn[A]-1)*n + (dist-1)] += 1
	return distances



'''X, Y input vectors,
classifier the different classifier with varying kernels,
test_type: the type of testing that should be done ie kfold,
test_parameters: the parameters that were ordered with'''
def train_test_SVM(X, Y, classifier, test_type, **kwargs):
	#Train SVM
	if test_type == 'k_fold':
		num_folds = kwargs['k']
		print 'K: ' + str(num_folds)
		kf = KFold(len(Y), n_folds=num_folds, indices=True)
		score_sum = 0
		for train, test in kf:
			score = classifier.fit(X[train], Y[train]).score(X[test], Y[test])
			print "score: " + str(score)
			score_sum += score
		#we want the average of the predicted kernels
		avg = score_sum/num_folds
		return avg
	if test_type == 'strat_k_fold':
		num_folds = kwargs['k']
		print 'Strat_K: ' + str(num_folds)
		skf = StratifiedKFold(Y, num_folds)
		score_sum = 0
		for train, test in skf:
			score = classifier.fit(X[train], Y[train]).score(X[test], Y[test])
			print "score: " + str(score)
			score_sum += score
		#we want the average of the predicted kernels
		avg = score_sum/num_folds
		print "avg: " + str(avg)
		return avg

	

#Map for different substrates (classes)
subs_class_dict = {'dhpg':0,'horn':1, 'pip':2, 'bht':3, 'dab':4,'dhb':5,
		'Orn':6, 'dht':7, 'hpg':8, 'A':9, 'C':10, 'E':11, 'D':12, 'G':13,
		'F':14, 'I':15, 'K':16, 'L':17, 'N':18, 'Q':19, 'P':20, 'S':21,
		'R':22,'T':23, 'W':24, 'V':25, 'Y':26, 'orn':27,
		'beta-ala':28, 'ORN':29, 'hyv-d':30, 'aad':31}


#Open Workbook, return tuple (vector of sequences, vector of substrate classes)
def getData():
	seqs=[]
	subs=[]
	ids = []

	book = open_workbook('Adomain_Substrate.xls')
	worksheet = book.sheet_by_name('Adomain_Substrate')
	num_rows = worksheet.nrows
	id_cell = 0
	substrate_cell = 1
	seq_cell = 2
	for i in range (1, num_rows):
		seq = worksheet.cell_value(i, seq_cell)
		substrate = worksheet.cell_value(i, substrate_cell)
		seq_id = worksheet.cell_value(i, id_cell)
		seqs.append(seq)
		subs.append(subs_class_dict[substrate])
		ids.append(seq_id)
	return (seqs, subs, ids)

#Return feature vector for a sequence
#Takes variable keyword arguments
#feature ="ngram", "AAcounts", "AAncounts", or "mapseq"
#extra parameter n depending on given feature
def getFeaturesFromSeq(seq, **kwargs):
	features = []
	f = kwargs["feature"]
	AAn_dict = {1: AA1, 2: AA2, 3:AA3, 4:AA4, 5:AA5}
	if f == "ngram":
		n = kwargs["n"]
		grams = all_n_grams(n)
		features = n_gram_counts(seq, n, grams)
	elif f == "AAcounts":
		features = AA_counts(seq)
	elif f == "AAncounts":
		n = kwargs["n"]
		features = AAn_counts(seq, AAn_dict[n])
	elif f == "mapseq":
		n = kwargs["n"]
		features = map_seq(seq, AAn_dict[n])
	elif f == 'AAn_ngram':
		n = kwargs['n']
		AAn = AAn_dict[kwargs['AAn']]
		grams = all_AAn_n_grams(AAn, n)
		features = AAn_n_gram_counts(seq, AAn, n, grams)
	elif f == 'AA_distances':
		n = kwargs['n']
		features = AA_distances(seq, n)
	elif f == 'AAn_distances':
		n = kwargs['n']
		AAn = AAn_dict[kwargs['AAn']]
		features = AAn_distances(seq, AAn, n)
	elif f == 'functions':
		features = function_features(seq, kwargs["id"], kwargs["function_dict"], kwargs["all_functions"])
	elif f == 'alignment':
		features = alignment_features(seq, kwargs["sequences"])
	return features

#Adds features to pre-existing X using getFeaturesFromSeq(seq, **kwargs)
def addFeatures(seqs, X, **kwargs):
	print 'add features'
	#if kwargs["feature"] == 'functions'
	if kwargs["feature"] == 'functions':
		for i, seq in enumerate(seqs):
			X[i] += getFeaturesFromSeq(seq, feature=kwargs["feature"], id= kwargs["ids"][i], function_dict=kwargs["function_dict"], all_functions=kwargs["all_functions"])
		return X
	elif kwargs["feature"] == 'alignment':
		for i, seq in enumerate(seqs):
			X[i] += getFeaturesFromSeq(seq, feature=kwargs["feature"], sequences=seqs)
		return X
	else:
		for i, seq in enumerate(seqs):
			X[i] += getFeaturesFromSeq(seq, feature=kwargs["feature"], n=kwargs["n"])
		return X


#function_features()
#print getData()
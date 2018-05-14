###Edwin Gavis
###03/12/18

import collections
import sklearn.cluster as skcluster 
import sklearn.decomposition as skdecomp 
import sklearn.feature_extraction.text as sktext
import sklearn.naive_bayes as sknb 
import sqlite3 as sql
import urllib3

from sklearn.externals import joblib

N_CLUST = 10

def build_kmeans(name, get_corpus, misses = True, verbose = False):
	'''
	Builds a kmeans model (N_CLUST clusters) and then dumps the model, 
	fitted tf-idf vectorizer and a list of database entries that aren't 
	represented  in the corpus to .pkl files w/ the given name in:
	myform/form_app/models/. 

	Uses a given function (get_corpus) to retrieve the corpus and if run in 
	verbose mode prints out the top terms associated with each centroid.
	'''
	corpus, misses = get_corpus()
	vect = sktext.TfidfVectorizer(stop_words = 'english')
	dtm = vect.fit_transform(corpus) 
	model = skcluster.KMeans(n_clusters = N_CLUST)
	model.fit(dtm)
	print(collections.Counter(model.labels_))
	if verbose:
		centroids = model.cluster_centers_.argsort()[:,::-1]
		terms = vect.get_feature_names()
		for clust_num in range(N_CLUST):
			print('cluster ' + str(clust_num))
			for i in centroids[clust_num, :10]:
				print(terms[i])
	if misses:
		joblib.dump(misses, 'myform/form_app/models/km_' + name + '_misses.pkl')
	joblib.dump(vect, 'myform/form_app/models/km_' + name + '_vector.pkl')
	joblib.dump(model, 'myform/form_app/models/km_' + name + '_model.pkl') 
	
def get_name_corpus():
	'''
	Returns a corpus of organization names and a list of the indexes of
	any organizations that don't have names in the database. 
	'''
	connect = sql.connect("myform/with_coords")
	db = connect.cursor()
	q1 = '''SELECT final_name FROM mcp'''
	corpus = []
	misses = []
	org_names = db.execute(q1).fetchall()
	for i, name in enumerate(org_names):
		if name[0] and name[1]:
			corpus.append(name[0] + " " + name[1])
		elif name[0]:
			corpus.append(name[0])
		elif name[1]:
			corpus.append(name[1])
		else:
			misses.append(i)
	return corpus, misses

def get_txt_corpus():
	'''
	Returns a corpus of organization natural language descriptions and a list
	of the indexes of organizations that don't have natural language 
	descriptions in the database. 
	'''
	connect = sql.connect("myform/with_coords")
	db = connect.cursor()
	q1 = '''SELECT text_dump FROM mcp'''
	corpus = []
	misses = []
	for i, text_dump in enumerate(db.execute(q1).fetchall()):
		if text_dump[0]:
			corpus.append(text_dump[0])
		else:
			misses.append(i)
	return corpus, misses

def get_irs_corpus():
	'''
	Returns a corpus of organizations with self-chosen IRS classifications and
	a list of the indexes of organizations that don't have IRS classifications 
	in the database. 
	'''
	connect = sql.connect("myform/with_coords")
	db = connect.cursor()
	q1 = '''SELECT pp_text FROM mcp'''
	corpus = []
	misses = []
	for i, pp_text in enumerate(db.execute(q1).fetchall()):
		if pp_text[0]:
			corpus.append(pp_text[0])
		else:
			misses.append(i)
	return corpus, misses

def get_combined_corpus():
	'''
	Creates a corpus of all text from all organizations in the database.
	'''
	connect = sql.connect("myform/with_coords")
	db = connect.cursor()
	q1 = '''SELECT name, "name:1", text_dump, pp_text FROM mcp'''
	corpus = []
	for i, all_text in enumerate(db.execute(q1).fetchall()):
		writing = ""
		for text in all_text:
			if text:
				writing += text + " "
		corpus.append(writing)
	return corpus, []

###UNCOMMENT TO (RE)BUILD MODELS###
#build_kmeans("name", get_name_corpus)
#build_kmeans("txt", get_txt_corpus)
#build_kmeans("irs", get_irs_corpus)
#build_kmeans("combined", get_combined_corpus, misses = False)

######################

def get_stops():
	'''
	Returns the list of English stop words from:
	"RCV1: A New Benchmark Collection for Text Categorization Research", 2004,
	    David D. Lewis, Yiming Yang, Tony G. Rose and Fan Li
	        Via the MIT Journal of Machine Learning Research Volume 5
	'''
	print('Getting Stops')
	http = urllib3.PoolManager()
	url = 'http://www.ai.mit.edu/projects/jmlr/papers/volume5/lewis04a/'
	url += 'a11-smart-stop-list/english.stop'
	r = http.request('GET', )
	cleaned_stops = str(r.data).replace('\\n', ' ').split(' ')
	return cleaned_stops

STOP_WORDS = get_stops

def latent_dirichlet():
	'''
	Fits a latent dirichlet allocation model to the corpus of organization
	descriptions and/or self-reported IRS designations. Then prints the top
	10 words in each component. Does NOT return the model for further use.  
	'''
	n_top_words = 10
	connect = sql.connect("myform/with_coords")
	db = connect.cursor()
	query = '''SELECT text_dump, pp_text FROM mcp'''
	corpus = []
	for all_text in db.execute(query).fetchall():
		writing = ""
		for alpha in all_text:
			if alpha:
				writing += alpha + " "
		corpus.append(writing)
	new_stops = ["chicago", "illinois", "founded", "year"]
	vect = sktext.CountVectorizer(stop_words = STOP_WORDS + new_stops)
	dtm = vect.fit_transform(corpus)
	model = skdecomp.LatentDirichletAllocation(
		n_components=N_CLUST, 
		max_iter=5,
        learning_method='online',
        learning_offset=50)
	model.fit(dtm)
	tf_feature_names = vect.get_feature_names()
	print_top_words(model, tf_feature_names, n_top_words)

def print_top_words(model, feature_names, n_top_words):
	'''
	Prints the N (n_top_words) words from each component of a latent dirichlet
	model (model) using the vocabulary of the term frequency matrix (tf_feature_names). 
	'''
	#From scikit dcumentation example: goo.gl/H8YE19
    for topic_idx, topic in enumerate(model.components_):
        output = "Topic #%d: " % topic_idx
        output += " ".join([feature_names[i]
                            for i in topic.argsort()[:-n_top_words - 1:-1]])
        print(output)

latent_dirichlet()

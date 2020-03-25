import argparse, cgi, requests, string
from urllib.error import URLError
import urllib.parse

from SPARQLWrapper import SPARQLExceptions, SPARQLWrapper, JSON
from rdflib import Namespace, RDF, RDFS, URIRef
import unidecode

from settings import DATASET, GRAPH

DBpedia = Namespace('http://dbpedia.org/ontology/')
DHTK = Namespace('http://dhtk.unil.ch/data/')
NIE = Namespace('http://www.semanticdesktop.org/ontologies/2007/01/19/nie#')
PG = Namespace('http://www.gutenberg.org/2009/pgterms/')
UWA = Namespace('http://www.w3.org/2007/uwa/context/common.owl#')

PREFIXES = f"""
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX fabio: <http://purl.org/spar/fabio/>
PREFIX nie: <{NIE}>
PREFIX pgterms: <{PG}>
PREFIX rdf: <RDF>
PREFIX rdfs: <{RDFS}>
PREFIX uwa: <{UWA}>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

sparql = SPARQLWrapper('/'.join([DATASET, 'query']), updateEndpoint='/'.join([DATASET, 'update']))


def bookshelves():
	query = f"""
{PREFIXES}
SELECT DISTINCT ?p ?v
WHERE {{
  ?x pgterms:bookshelf [ ?p ?v ]
}}
"""
	sparql.method = 'GET'
	sparql.setQuery(query)
	sparql.setReturnFormat(JSON)
	try:
		results = sparql.query().convert()
	except URLError:
		print("FATAL: Couldn't query SPARQL endpoint")
		exit()
	for bind in results['results']['bindings']:
		if RDF.value == URIRef(bind['p']['value']):
			shelfname = bind['v']['value']
			table = str.maketrans('', '', string.punctuation)
			slug = [w.translate(table) for w in shelfname]
			slug = ''.join(slug)
			slug = unidecode.unidecode(slug).lower().replace(' ', '_')
			shelf = DHTK['/'.join(['collection', 'gutenberg', slug])]
			# WARN translate Bookshelf for non-English ones (e.g. PT Prateleira)
			fix = f"""
{PREFIXES}
WITH <{GRAPH}>
DELETE {{
	?x pgterms:bookshelf ?b . 
	?b rdf:value "{shelfname}"
	 ; <http://purl.org/dc/dcam/memberOf> ?t
}}
INSERT {{
	?x pgterms:bookshelf <{shelf}> . 
	<{shelf}> dct:title "{shelfname}"
	 ; rdfs:seeAlso ?wiki
	 ; a ?t
}}
WHERE {{
	?x pgterms:bookshelf ?b . 
	?b rdf:value "{shelfname}"
	 ; <http://purl.org/dc/dcam/memberOf> ?t
	BIND(STRDT(CONCAT("https://www.gutenberg.org/wiki/",REPLACE("{shelfname}", "\\s", "_"),"_(Bookshelf)"), xsd:anyURI) as ?wiki)
}}
"""
			sparql.method = 'POST'
			sparql.setQuery(fix)
			sparql.query()
    # return graph


def formats():
	query = f"""
{PREFIXES}
SELECT DISTINCT ?p ?v
WHERE {{
  ?x dct:format [ ?p ?v ]
}}
"""
	sparql.method = 'GET'
	sparql.setQuery(query)
	sparql.setReturnFormat(JSON)
	try:
		results = sparql.query().convert()
	except URLError:
		print("FATAL: Couldn't query SPARQL endpoint")
		exit()
	for bind in results['results']['bindings']:
		if RDF.value == URIRef(bind['p']['value']):
			content_type = bind['v']['value']
			mimetype, options = cgi.parse_header(content_type)
			print('Doing ' + mimetype + ' ' + str(options))
			# print(options)
			mime = URIRef('http://www.iana.org/assignments/media-types/' + mimetype)
			if 'charset' in options and options['charset']:
				chst = options['charset']
				charset = UWA['CharacterSet_' + chst.upper()]
				format = DHTK['/'.join(['format', urllib.parse.quote(mimetype, safe=''), 'charset', chst])]
				insert = f"""
	?x dct:format <{format}> .
	<{format}> a uwa:ContentType
	   ; uwa:contentTypeName "{content_type}"^^xsd:string
	   ; nie:mimeType <{mime}>
	   ; nie:characterSet <{charset}> .
	<{mime}> a uwa:ContentType
	   ; uwa:contentTypeName "{mimetype}"^^xsd:string
	   ; ?p1 ?y1 .
	<{charset}> a uwa:CharacterSet
	   ; uwa:charsetName "{chst}"^^xsd:string
	.
"""
			else: 
				format = mime
				insert = f"""
	?x dct:format <{format}> .
	<{format}> a uwa:ContentType
	   ; uwa:contentTypeName "{mimetype}"^^xsd:string
	   ; ?p1 ?y1
	.
"""
			# print(format)
			fix = f"""
{PREFIXES}
DELETE {{ GRAPH ?g {{
	?x dct:format ?f . 
	?f rdf:value "{content_type}"^^dct:IMT
	 ; ?p1 ?y1
}}}}
INSERT {{ GRAPH ?g {{
{insert}
}}}}
WHERE {{ GRAPH ?g {{
	?x dct:format ?f . 
	?f rdf:value "{content_type}"^^dct:IMT
	 ; ?p1 ?y1 FILTER ( ?p1 != rdf:value )
}}}}
"""
			# print(fix)
			sparql.method = 'POST'
			sparql.setQuery(fix)
			sparql.query()
    # return graph


def toc():
	query = f"""
{PREFIXES}
SELECT DISTINCT ?x ?toc
FROM <{GRAPH}>
WHERE {{
  ?x dct:tableOfContents ?toc
}}
"""
	sparql.method = 'GET'
	sparql.setQuery(query)
	sparql.setReturnFormat(JSON)
	try:
		results = sparql.query().convert()
	except URLError:
		print("FATAL: Couldn't query SPARQL endpoint")
		exit()
	for bind in results['results']['bindings']:
		book = bind['x']['value']
		headings = bind['toc']['value'].split(' -- ')
		toc = URIRef('#'.join([book, '_toc']))
		insert = f"""
<{book}> dct:tableOfContents <{toc}> .
<{toc}> a fabio:TableOfContents
"""
		for i, h in enumerate(headings) :
			# print(str(i) + ' : ' + h)
			cno = i + 1
			head = h.strip().replace('"', '\\"')
			chap = URIRef('#'.join([book, '_chapter-' + str(cno)]))
			insert += f""". <{toc}> rdf:_{cno} <{chap}> ; rdf:member <{chap}> . <{chap}> dct:title \"\"\"{head}\"\"\""""
		
		fix = f"""
{PREFIXES}
WITH <{GRAPH}>
DELETE {{
	<{book}> dct:tableOfContents ?toc
}}
INSERT {{
{insert}
}}
WHERE {{ 
	<{book}> dct:tableOfContents ?toc
}}
"""
		sparql.method = 'POST'
		sparql.setQuery(fix)
		sparql.query()


parser = argparse.ArgumentParser(description='Run one or more refactoring processes.')
parser.add_argument('processes', metavar='P', nargs='+',
                   help='One or more of "bookshelves", "formats" or "toc"')

print('SPARQL service is ' + DATASET)
print('RDF graph is ' + GRAPH)
args = parser.parse_args()
if args.processes:
	print('Looking for the following to run: ' + str(args.processes))
	for fun in vars(args)['processes']:
		locals()[fun]()

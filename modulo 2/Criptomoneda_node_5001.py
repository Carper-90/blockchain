# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 22:36:31 2022

@author:  Carlos Augusto Persico (Carper-90)
"""

# Módulo 2 - Crear una Criptomoneda

# Para Instalar:
# Flask==1.1.2: pip install Flask==1.1.2
# Cliente HTTP Postman: https://www.getpostman.com/
# requests==2.27.1: pip install requests==2.27.1

# Importar las librerías
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Parte 1 - Crear la Cadena de Bloques
class Blockchain:
    
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
        
    def create_block(self, proof, previous_hash):#Crear un nuevo bloque de la cadena
        block = {'index' : len(self.chain)+1, #Crear un nuevo bloque de la cadena
                 'timestamp' : str(datetime.datetime.now()), #Crear un nuevo bloque de la cadena
                 'proof' : proof, #Crear un nuevo bloque de la cadena
                 'previous_hash': previous_hash, #Crear un nuevo bloque de la cadena
                 'transactions': self.transactions} 
        self.transactions = []
        self.chain.append(block) #Crear un nuevo bloque de la cadena 
        return block #Crear un nuevo bloque de la cadena

    def get_previous_block(self): #Obtener el último bloque de la cadena
        return self.chain[-1] #Obtener el último bloque de la cadena
    
    def proof_of_work(self, previous_proof): 
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else: 
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
    def add_transactio(self, sender, receiver, amount):
        self.transactions.append({ 'sender': sender,
                                  'receiver': receiver,
                                  'amount':amount})
        previous_block = self.get_previous_block()
        return previous_block ['index'] + 1
    def add_node (self, address):
        parsed_url= urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length=response.json()['length']
                chain=response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain :
            self.chain = longest_chain
            return True
        return False
# Parte 2 - Minado de un Bloque de la Cadena

# Crear una aplicación web
app = Flask(__name__)
# Si se obtiene un error 500, actualizar flask, reiniciar spyder y ejecutar la siguiente línea
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

#direccion del nodo en el puerto 5000
node_address = str(uuid4()).replace('-', '')

# Crear una Blockchain
blockchain = Blockchain()

# Minar un nuevo bloque
@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transactio(sender=node_address, receiver='Carlos', amount=5)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message' : '¡Felicidades, has minado un nuevo bloque!', 
                'index': block['index'],
                'timestamp' : block['timestamp'],
                'proof' : block['proof'],
                'previous_hash' : block['previous_hash'],
                'transactions':  block['transactions'] }
    return jsonify(response), 200

# Obtener la cadena de bloques al completo
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain' : blockchain.chain, 
                'length' : len(blockchain.chain)}
    return jsonify(response), 200

# Comprobar si la cadena de bloques es válida
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message' : 'Parece todo va bien. La cadena de bloques es super válida.'}
    else:
        response = {'message' : 'Creo que estamos jodidos. La cadena de bloques no es válida.'}
    return jsonify(response), 200  
#añadir una nueva transaccion a la cadena
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json=request.get_json()
    transaction_keys = ['sender','receiver','amount']
    if not all (key in json for key in transaction_keys):
        return 'faltan datos',400
    index=blockchain.add_transactio(json['sender'], json['receiver'], json['amount'])
    response = {'message':f'la transacción sera añadida al bloque{index}'}
    return jsonify(response), 201
 # Parte 3 - Descentralizar la cadena de bloques que hayamos creado
 #conectar nuevos nodos
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json=request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'no hay nodos para añadir', 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message':'Todos los nodos han sido conectados. la cadena de criptomonedas contiene ahora los siguientes nodos:',
                'total_nodes':list(blockchain.nodes)}
    return jsonify(response), 201
    #remplazar la cadena por la mas larga si es necesario
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replace = blockchain.replace_chain()
    if is_chain_replace:
        response = {'message' : 'los nodos tenian diferentes cadenas y han sido todas remplazadas por la mas larga.',
                    'new_chain':blockchain.chain}
    else:
        response = {'message' : 'todo correcto. la cadena en toos los nodos ya es la mas larga',
                    'actual_chain':blockchain.chain}
    return jsonify(response), 200  
    
    
    
    
    transaction_keys = ['sender','receiver','amount']
    if not all (key in json for key in transaction_keys):
        return 'faltan datos',400
    index=blockchain.add_transactio(json['sender'], json['receiver'], json['amount'])
    response = {'message':f'la transacción sera añadida al bloque{index}'}
    return jsonify(response), 201
# Ejecutar la app
app.run(host = '0.0.0.0', port = 5001)

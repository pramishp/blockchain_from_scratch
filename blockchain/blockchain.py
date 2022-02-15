import json  # syntax for storing and exchanging data(javascript object notation)
import random  # अनियमित सन्ख्या दिन्छ।

from datetime import datetime  # समयको लागि ।
from hashlib import sha256  # hash value निकाल्ने मोड्युल ् ।

from urllib.parse import urlparse  # helper for url parsing to add nodes

import requests


class Blockchain(object):  # ब्लकचेनको ब्लु पृन्ट ।
    def __init__(self):
        self.chain = []  #
        self.pending_transactions = []

        # Create the genesis block
        print("Creating genesis block")
        self.chain.append(self.new_block(None))

    def new_block(self, transaction):
        block = {
            'index': len(self.chain),
            'timestamp': datetime.utcnow().isoformat(),
            'transactions': transaction,
            'previous_hash': self.last_block["hash"] if self.last_block else None,
            'nonce': format(random.getrandbits(64), "x"),
        }

        # Get the hash of this new block, and add it to the block
        block_hash = self.hash(block)
        block["hash"] = block_hash


        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """
        self.pending_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        # We ensure the dictionary is sorted or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return sha256(block_string).hexdigest()

    @property
    def last_block(self):
        # Returns the last block in the chain (if there are blocks)
        return self.chain[-1] if self.chain else None

    @staticmethod
    def valid_block(block):
        # Checks if a block's hash starts with 0000
        return block["hash"].startswith("0000")

    def proof_of_work(self):
        while True:
            new_block = self.new_block(self.pending_transactions)
            if self.valid_block(new_block):
                break

        # Reset the list of pending transactions
        self.pending_transactions = []
        self.chain.append(new_block)
        print("Found a new block: ", new_block)


class BlockchainWrapper(Blockchain):
    def __init__(self):
        super().__init__()
        self.nodes = set()

    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if not self.valid_block(block):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

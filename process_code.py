# %%
import json
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import CodeSplitter
from pprint import pprint
import tree_sitter_language_pack

code_documents = SimpleDirectoryReader(input_dir="./documents/code", recursive=True).load_data()
paths = [doc.metadata['file_path'] for doc in code_documents]
pprint(tree_sitter_language_pack.get_parser("csharp"))
pprint(paths)

from llama_index import GPTIndex
from llama_index import Document

# PDFやテキストデータのインデックス化
documents = [Document.from_file("data/purpose_of_questions_japanese.pdf")]
index = GPTIndex.from_documents(documents)

# インデックスを保存して再利用
index.save_to_disk("index.json")